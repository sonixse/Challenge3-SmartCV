import base64
import re
from pathlib import Path

import streamlit as st

from src.agents.interpreter import (
    DEFAULT_OUTPUT_DIR,
    interpret,
    load_profile,
    save_profile,
)
from src.agents.podium import PodiumEntry, build_entry
from src.agents.qualifier import qualify
from src.data.load_vacancies import load as load_vacancies
from src.schemas.candidate import CandidateProfile
from src.schemas.vacancy import Vacancy

# Mapping del schema canònic (anglès) al vocabulari del Qualifier
_EDU_MAP = {
    "No degree": None,
    "Bachelor's": "Grau",
    "Master's": "Master",
    "PhD": "Doctorat",
}


def _candidate_to_qualifier(profile: CandidateProfile) -> dict:
    idiomes = {
        l.language.lower(): ("C2" if l.level == "Native" else l.level)
        for l in profile.languages
    }
    return {
        "experiencia_anys": float(profile.years_experience),
        "idiomes": idiomes,
        "formacio_nivell": _EDU_MAP.get(profile.education_level),
    }


def _vacancy_to_qualifier(vac: Vacancy, exp_max: int) -> dict:
    idioma_req = {
        r.language.lower(): ("C2" if r.level == "Native" else r.level)
        for r in vac.required_language_list
    }
    return {
        "experiencia_min": int(vac.years_experience),
        "experiencia_max": int(exp_max),
        "idioma_requerit": idioma_req,
        "formacio_min": _EDU_MAP.get(vac.highest_degree),
    }


@st.cache_data(show_spinner=False)
def _cached_vacancies() -> list[Vacancy]:
    _, vacs = load_vacancies()
    return vacs


@st.cache_resource(show_spinner=False)
def _try_linguist():
    """Carrega el Linguist (BGE + Chroma) una sola vegada. None si no està disponible."""
    try:
        from src.agents.linguist import analyse
        return analyse
    except Exception:
        return None


def _fallback_linguist(candidate: CandidateProfile, vacancy: Vacancy) -> dict:
    """Substitut determinista quan BGE/Chroma no estan disponibles.

    Compara noms en minúscules: igual → MATCH, prefix/contingut comú → GREY ZONE,
    altrament NO MATCH. Pitjor que el semàntic real però manté el rànquing operatiu.
    """
    cand_names = [s.name.lower() for s in candidate.skills]
    items = list(vacancy.skills) + list(vacancy.tools)
    out_skills = []
    for req in items:
        rn = req.name.lower()
        cls = "NO MATCH"
        best = None
        for cn in cand_names:
            if cn == rn:
                cls, best = "MATCH", cn
                break
            if cn in rn or rn in cn:
                cls, best = "GREY ZONE", cn
        out_skills.append({"vacancy_skill": req.name, "best_match": best, "similarity": 0.0, "classification": cls})
    return {"skills": out_skills}


def _linguist_for(candidate: CandidateProfile, vacancy: Vacancy) -> dict:
    fn = _try_linguist()
    if fn is None:
        return _fallback_linguist(candidate, vacancy)
    try:
        return fn(candidate, vacancy)
    except Exception:
        return _fallback_linguist(candidate, vacancy)


def compute_ranking(profile: CandidateProfile, top_n: int = 10) -> list[PodiumEntry]:
    """Avalua el candidat contra totes les ofertes via Qualifier + Linguist + Podium."""
    prof_input = _candidate_to_qualifier(profile)
    entries: list[PodiumEntry] = []
    for vac in _cached_vacancies():
        off_input = _vacancy_to_qualifier(vac, vac.years_experience + 7)
        qres = qualify(prof_input, off_input)
        if qres.decision == "eliminate":
            continue
        ling = _linguist_for(profile, vac)
        entry = build_entry(vac, ling, qres, prof_input, off_input)
        if entry is not None:
            entries.append(entry)

    entries.sort(key=lambda e: e.score_match, reverse=True)
    return entries[:top_n]


def _render_axis_signal(label: str, reason: str | None) -> None:
    """Mostra un eix com a senyal: ✓ verd si net, ⚠ àmbar amb el motiu si penalitzat."""
    if reason is None:
        st.markdown(f"<span style='color:#1f8a3c'>✓ {label}: encaixa</span>", unsafe_allow_html=True)
    else:
        st.markdown(f"<span style='color:#b76e00'>⚠ {reason}</span>", unsafe_allow_html=True)


def _vacancy_by_id(vid: int) -> Vacancy | None:
    return next((v for v in _cached_vacancies() if v.id == vid), None)


def render_ranking(profile: CandidateProfile) -> None:
    st.markdown("### 🏆 Top 10 ofertes per a aquest candidat")
    st.caption("Ordenat per compatibilitat (més alt = millor encaix).")

    top = compute_ranking(profile, top_n=10)
    total_offers = len(_cached_vacancies())
    if not top:
        st.warning(
            f"Cap de les {total_offers} ofertes manté aquest candidat — "
            f"sempre acaba en `eliminate` per idioma o experiència."
        )
        return

    st.caption(f"Mostrant {len(top)} de {total_offers} ofertes vàlides.")

    for rank, entry in enumerate(top, start=1):
        vac = _vacancy_by_id(entry.offer_id)
        with st.container(border=True):
            top_l, top_r = st.columns([4, 1])
            with top_l:
                st.markdown(f"**#{rank} — {entry.role}** · _{entry.sector}_")
                if vac is not None:
                    st.caption(
                        f"Oferta #{vac.id} · exp ≥ {vac.years_experience} anys · "
                        f"formació: {vac.highest_degree} · "
                        f"{'amb pràctiques' if vac.has_internship else 'sense pràctiques'}"
                    )
                    if vac.required_language_list:
                        st.caption(
                            "Idiomes: "
                            + " · ".join(
                                f"{r.language} {r.level}" for r in vac.required_language_list
                            )
                        )
            with top_r:
                st.markdown(
                    f"<div style='text-align:right;font-size:2.6rem;font-weight:700;line-height:1'>"
                    f"{entry.score_match}<span style='font-size:1.2rem'>%</span></div>"
                    f"<div style='text-align:right;color:#888;font-size:0.85rem'>match</div>",
                    unsafe_allow_html=True,
                )

            _render_axis_signal("Idioma", entry.reasons.language)
            _render_axis_signal("Experiència", entry.reasons.experience)
            _render_axis_signal("Formació", entry.reasons.education)

            calc_bits = [f"Match base {entry.score_semantic}"]
            if entry.penalties.language:
                calc_bits.append(f"−{entry.penalties.language} idioma")
            if entry.penalties.experience:
                calc_bits.append(f"−{entry.penalties.experience} exp")
            if entry.penalties.education:
                calc_bits.append(f"−{entry.penalties.education} formació")
            calc_bits.append(f"→ **{entry.score_match}**")
            st.caption(" · ".join(calc_bits))

            if entry.flags:
                st.caption("⚑ " + " · ".join(f"`{f}`" for f in entry.flags))

            if vac is not None:
                with st.expander("Veure detalls de l'oferta"):
                    must_have = [s for s in vac.skills if s.type == "must_have"]
                    nice_to_have = [s for s in vac.skills if s.type == "nice_to_have"]
                    other = [s for s in vac.skills if s.type not in {"must_have", "nice_to_have"}]

                    if must_have:
                        st.markdown("**Skills imprescindibles (must-have)**")
                        for s in must_have:
                            st.write(f"• {s.name} — _{s.purpose}_")
                    if nice_to_have:
                        st.markdown("**Skills valorades (nice-to-have)**")
                        for s in nice_to_have:
                            st.write(f"• {s.name} — _{s.purpose}_")
                    if other:
                        st.markdown("**Altres skills**")
                        for s in other:
                            st.write(f"• {s.name} — _{s.purpose}_")
                    if vac.tools:
                        st.markdown("**Eines**")
                        for t in vac.tools:
                            st.write(f"• {t.name} — _{t.purpose}_")
                    if vac.required_languages:
                        st.caption(
                            f"L'oferta demana parlar com a mínim {vac.required_languages} idiomes."
                        )

EXAMPLES_DIR = Path("data/raw")
PROCESSED_DIR = Path(DEFAULT_OUTPUT_DIR)
UPLOADS_DIR = Path("data/uploads")

st.set_page_config(page_title="SmartCV", page_icon="🎯", layout="wide")


def extract_nn(filename: str) -> str | None:
    m = re.match(r"(\d+)", filename)
    return m.group(1).zfill(2) if m else None


def list_example_pdfs() -> dict[str, Path]:
    out: dict[str, Path] = {}
    if not EXAMPLES_DIR.exists():
        return out
    for pdf in sorted(EXAMPLES_DIR.glob("*.pdf")):
        nn = extract_nn(pdf.name)
        if nn and nn not in out:
            out[nn] = pdf
    return out


@st.cache_data(show_spinner=False)
def pdf_first_page_png(pdf_path_str: str, mtime: float, zoom: float = 1.5) -> bytes | None:
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(pdf_path_str)
        page = doc.load_page(0)
        # If page is landscape, rotate 90º so all thumbnails share portrait orientation
        rect = page.rect
        rotate = 90 if rect.width > rect.height else 0
        mat = fitz.Matrix(zoom, zoom).prerotate(rotate)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        png = pix.tobytes("png")
        doc.close()
        return png
    except Exception:
        return None


def cache_path_for_nn(nn: str) -> Path:
    return PROCESSED_DIR / f"{nn}_candidate.json"


def cache_path_for_upload(stem: str) -> Path:
    return PROCESSED_DIR / f"upload_{stem}_candidate.json"


def load_cached(path: Path) -> CandidateProfile | None:
    if not path.exists():
        return None
    try:
        return load_profile(str(path))
    except Exception:
        return None


def run_interpret_with_ui(pdf_path: Path, cache_path: Path) -> CandidateProfile | None:
    try:
        with st.spinner(f"Processant {pdf_path.name} amb Llama3 (Ollama)... pot trigar 30-60s"):
            profile = interpret(str(pdf_path))
        save_profile(profile, str(cache_path))
        return profile
    except Exception as e:
        msg = str(e).lower()
        if any(tok in msg for tok in ("connect", "refus", "ollama", "11434", "connection")):
            st.error(
                "No es pot connectar amb Ollama. Assegura't que `ollama serve` "
                "està corrent i que tens el model `llama3` instal·lat "
                "(`ollama pull llama3`)."
            )
        else:
            st.error(f"Error processant el CV: {e}")
        return None


def render_pdf(pdf_path: Path, height: int = 720) -> None:
    try:
        data = pdf_path.read_bytes()
    except Exception as e:
        st.warning(f"No s'ha pogut llegir el PDF: {e}")
        return
    b64 = base64.b64encode(data).decode("utf-8")
    st.markdown(
        f'<iframe src="data:application/pdf;base64,{b64}" '
        f'width="100%" height="{height}" '
        f'style="border:1px solid #2a2a2a;border-radius:6px;"></iframe>',
        unsafe_allow_html=True,
    )
    st.download_button(
        "Descarregar PDF",
        data,
        file_name=pdf_path.name,
        mime="application/pdf",
        key=f"dl_{pdf_path.name}",
    )


def render_profile(profile: CandidateProfile) -> None:
    st.markdown(f"### {profile.name}")
    meta = []
    if profile.location:
        meta.append(f"📍 {profile.location}")
    if profile.contact:
        meta.append(f"✉️ {profile.contact}")
    if meta:
        st.caption(" · ".join(meta))

    st.markdown("**Experiència**")
    st.write(f"{profile.years_experience} anys d'experiència professional")

    st.markdown("**Formació**")
    st.write(f"{profile.education_level} · {profile.education_field}")

    st.markdown("**Skills**")
    if profile.skills:
        for s in profile.skills:
            years = f" — {s.years} anys" if s.years is not None else ""
            st.write(f"• {s.name}{years}")
    else:
        st.write("_Sense skills detectades_")

    st.markdown("**Idiomes**")
    if profile.languages:
        for lang in profile.languages:
            st.write(f"• {lang.language} ({lang.level})")
    else:
        st.write("_Sense idiomes detectats_")


def card_summary(nn: str, pdf: Path) -> tuple[str, str]:
    profile = load_cached(cache_path_for_nn(nn))
    if profile:
        skills_preview = ", ".join(s.name for s in profile.skills[:3])
        sub = f"{profile.years_experience} anys · {profile.education_level}"
        if skills_preview:
            sub += f"\n\n🛠 {skills_preview}"
        return profile.name, sub
    return f"CV #{nn}", f"{pdf.name}\n\n_sense processar — clica per extreure_"


# ──────────────────────────────────────────────────────────────────────
# UI
# ──────────────────────────────────────────────────────────────────────

st.title("🎯 SmartCV")
st.caption("Sistema multi-agent de matching semàntic CV ↔ oferta")

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

if "selected" not in st.session_state:
    st.session_state.selected = None

# ─── Examples ─────────────────────────────────────────────────────────
st.header("Currículums d'exemple")

examples = list_example_pdfs()

if not examples:
    st.info(f"No s'han trobat PDFs a `{EXAMPLES_DIR}/`.")
else:
    cols_per_row = 5
    items = list(examples.items())
    for row_start in range(0, len(items), cols_per_row):
        cols = st.columns(cols_per_row)
        for col, (nn, pdf) in zip(cols, items[row_start:row_start + cols_per_row]):
            title, sub = card_summary(nn, pdf)
            cached = cache_path_for_nn(nn).exists()
            with col:
                with st.container(border=True):
                    thumb = pdf_first_page_png(str(pdf), pdf.stat().st_mtime)
                    if thumb:
                        st.image(thumb, use_container_width=True)
                    st.markdown(f"**{title}**")
                    st.caption(sub)
                    label = "Veure" if cached else "Processar i veure"
                    if st.button(label, key=f"btn_ex_{nn}", use_container_width=True):
                        st.session_state.selected = ("example", nn)
                        st.rerun()

# ─── Upload ───────────────────────────────────────────────────────────
st.header("Afegir currículum")

uploaded = st.file_uploader("Puja un PDF", type=["pdf"], key="uploader")
if uploaded is not None:
    stem = Path(uploaded.name).stem
    target_pdf = UPLOADS_DIR / uploaded.name
    if not target_pdf.exists():
        target_pdf.write_bytes(uploaded.getbuffer())
    if st.button("Processar currículum pujat", key="btn_process_upload"):
        st.session_state.selected = ("upload", stem)
        st.rerun()

# ─── Detail view ──────────────────────────────────────────────────────
selection = st.session_state.selected
if selection is not None:
    kind, key = selection
    if kind == "example":
        pdf_path = examples.get(key)
        cache = cache_path_for_nn(key)
    else:
        matches = list(UPLOADS_DIR.glob(f"{key}.*"))
        pdf_path = matches[0] if matches else None
        cache = cache_path_for_upload(key)

    st.divider()
    if pdf_path is None or not pdf_path.exists():
        st.warning("No s'ha trobat el PDF seleccionat.")
    else:
        top_left, top_right = st.columns([4, 1])
        with top_left:
            st.subheader(f"Detall — {pdf_path.name}")
        with top_right:
            if st.button("⬅ Tornar", use_container_width=True):
                st.session_state.selected = None
                st.rerun()

        profile = load_cached(cache)
        if profile is None:
            profile = run_interpret_with_ui(pdf_path, cache)

        left, right = st.columns([1, 1])
        with left:
            st.markdown("#### PDF original")
            render_pdf(pdf_path)
        with right:
            st.markdown("#### Dades extretes")
            if profile:
                render_profile(profile)
            else:
                st.info("Encara no hi ha dades extretes per a aquest currículum.")

        if profile:
            st.divider()
            render_ranking(profile)
