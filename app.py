import base64
import re
from pathlib import Path

import streamlit as st

from src.ui.skill_icons import skill_icon_html

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

_LEVEL_COLOR = {
    "native": "#15803d", "c2": "#15803d",
    "c1": "#1d4ed8", "b2": "#7c3aed",
    "b1": "#b45309", "a2": "#dc2626", "a1": "#dc2626",
}

EXAMPLES_DIR = Path("data/raw")
PROCESSED_DIR = Path(DEFAULT_OUTPUT_DIR)
UPLOADS_DIR = Path("data/uploads")

#########################################################################

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


def _run_detective(linguist_result: dict, raw_text: str) -> dict:
    """Resolve grey-zone skills via Detective and merge verdicts into linguist_result.

    Supports both the real Linguist output (has a 'grey_zone' key) and the
    fallback (no key — grey-zone skills are inferred from the skills list).
    Falls back silently if Detective fails or Ollama is unavailable; Podium
    then applies the 0.5 credit fallback for any remaining GREY ZONE entries.
    """
    grey_zone: list[str] = linguist_result.get("grey_zone") or [
        s["vacancy_skill"]
        for s in linguist_result.get("skills", [])
        if s.get("classification") == "GREY ZONE"
    ]
    if not grey_zone:
        return linguist_result

    try:
        from src.agents.detective import resolve as detective_resolve
        # best_match: the candidate skill the Linguist found closest to each grey-zone skill.
        # Passed as aliases so _relevant_context can locate the right CV section even when
        # the vacancy skill name does not appear verbatim in the text.
        aliases = {
            s["vacancy_skill"]: s["best_match"]
            for s in linguist_result.get("skills", [])
            if s.get("classification") == "GREY ZONE" and s.get("best_match")
        }
        det = detective_resolve(grey_zone, raw_text, aliases=aliases)
        for skill_entry in linguist_result.get("skills", []):
            name = skill_entry["vacancy_skill"]
            if name in det.verdicts:
                skill_entry["classification"] = det.verdicts[name].classification

        # Accumulate verdicts for the advisor (first encounter per skill wins)
        knowledge = st.session_state.get("detective_knowledge", {})
        for skill, verdict in det.verdicts.items():
            if skill not in knowledge:
                knowledge[skill] = {
                    "classification": verdict.classification,
                    "reasoning":      verdict.reasoning,
                }
        st.session_state.detective_knowledge = knowledge
    except Exception:
        pass  # Ollama unavailable — keep GREY ZONE, Podium gives 0.5 credit

    return linguist_result


def compute_ranking(profile: CandidateProfile, top_n: int = 10) -> list[PodiumEntry]:
    """Avalua el candidat contra totes les ofertes via Qualifier + Linguist + Detective + Podium."""
    st.session_state.detective_knowledge = {}  # reset for each new ranking run
    prof_input = _candidate_to_qualifier(profile)
    entries: list[PodiumEntry] = []
    for vac in _cached_vacancies():
        off_input = _vacancy_to_qualifier(vac, vac.years_experience + 7)
        qres = qualify(prof_input, off_input)
        if qres.decision == "eliminate":
            continue
        ling = _linguist_for(profile, vac)
        ling = _run_detective(ling, profile.raw_text)
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


def render_advisor_chat(profile: CandidateProfile, ranking: list[PodiumEntry]) -> None:
    from chat.advisor import build_context, advisor_respond

    st.markdown("### Assessor de CVs 🧑‍💼")
    st.caption("Pregunta'm per què el teu CV no fa match o com pots millorar-lo.")

    detective_knowledge = st.session_state.get("detective_knowledge", {})
    system_prompt = build_context(profile, ranking, detective_knowledge)

    if "advisor_history" not in st.session_state:
        st.session_state.advisor_history = []

    for msg in st.session_state.advisor_history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    if user_input := st.chat_input("Escriu la teva pregunta..."):
        st.session_state.advisor_history.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.write(user_input)
        with st.chat_message("assistant"):
            with st.spinner("..."):
                reply = advisor_respond(
                    user_input,
                    st.session_state.advisor_history[:-1],
                    system_prompt,
                )
            st.write(reply)
        st.session_state.advisor_history.append({"role": "assistant", "content": reply})


def render_ranking(profile: CandidateProfile) -> list[PodiumEntry]:
    st.markdown("### Rànquing d'ofertes")
    with st.spinner("Calculant matching..."):
        top = compute_ranking(profile)
    _render_ranking_cards(top)
    return top


def _render_ranking_cards(top: list[PodiumEntry]) -> None:
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
                    must_have   = [s for s in vac.skills if s.type == "must_have"]
                    nice_to_have = [s for s in vac.skills if s.type == "nice_to_have"]
                    other       = [s for s in vac.skills if s.type not in {"must_have", "nice_to_have"}]
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

def render_profile(profile: CandidateProfile) -> None:
    meta_parts = []
    if profile.location:
        meta_parts.append(f"📍 {profile.location}")
    if profile.contact:
        meta_parts.append(f"✉️ {profile.contact}")
    meta_html = (
        f"<p style='color:#888;font-size:0.85rem;margin:4px 0 0 0'>"
        + " &nbsp;·&nbsp; ".join(meta_parts) + "</p>"
    ) if meta_parts else ""

    st.markdown(
        f"<div style='padding:8px 0 16px 0'>"
        f"<h2 style='margin:0;font-size:1.9rem;font-weight:800'>{profile.name}</h2>"
        f"{meta_html}</div>",
        unsafe_allow_html=True,
    )

    CARD_H = "130px"
    exp_col, edu_col = st.columns([1, 2])
    with exp_col:
        st.markdown(
            f"<div style='background:linear-gradient(135deg,#0e4f82,#1976d2);color:white;"
            f"border-radius:14px;padding:20px 16px;text-align:center;"
            f"min-height:{CARD_H};display:flex;flex-direction:column;justify-content:center'>"
            f"<div style='font-size:0.85rem;font-weight:700;letter-spacing:1px;"
            f"text-transform:uppercase;margin-bottom:6px'>💼 Experiència</div>"
            f"<div style='font-size:3rem;font-weight:900;line-height:1'>{profile.years_experience}</div>"
            f"<div style='font-size:0.85rem;opacity:.85;margin-top:4px'>anys</div>"
            f"</div>",
            unsafe_allow_html=True,
        )
    with edu_col:
        st.markdown(
            f"<div style='background:linear-gradient(135deg,#1a5c3a,#2e7d52);color:white;"
            f"border-radius:14px;padding:20px 18px;"
            f"min-height:{CARD_H};display:flex;flex-direction:column;justify-content:center'>"
            f"<div style='font-size:0.85rem;font-weight:700;letter-spacing:1px;"
            f"text-transform:uppercase;margin-bottom:8px'>🎓 Formació</div>"
            f"<div style='font-size:1.4rem;font-weight:800;line-height:1.2'>{profile.education_level}</div>"
            f"<div style='font-size:0.88rem;opacity:.85;margin-top:6px'>{profile.education_field}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

    st.markdown(
        "<p style='font-size:1rem;font-weight:700;letter-spacing:1px;text-transform:uppercase;"
        "color:white;margin-bottom:8px'>🛠 Skills</p>",
        unsafe_allow_html=True,
    )
    if profile.skills:
        icons_html = ""
        for s in profile.skills:
            icon = skill_icon_html(s.name, size=22)
            if icon:
                icons_html += (
                    f"<span title='{s.name}' style='display:inline-flex;align-items:center;"
                    f"justify-content:center;width:36px;height:36px;margin:3px 2px;"
                    f"background:#f3f0ff;border-radius:8px'>"
                    f"{icon}</span>"
                )
        st.markdown(f"<div style='margin-bottom:10px'>{icons_html}</div>", unsafe_allow_html=True)

        tags = "".join(
            f"<span style='display:inline-block;"
            f"border:1.5px solid #7c3aed;color:#6d28d9;"
            f"border-radius:24px;padding:9px 20px;margin:5px 6px 5px 0;"
            f"font-size:1.05rem;font-weight:600;background:#ede9fe'>"
            f"{s.name}{(f' · {s.years}a') if s.years is not None else ''}</span>"
            for s in profile.skills
        )
        st.markdown(f"<div style='line-height:2.8'>{tags}</div>", unsafe_allow_html=True)
    else:
        st.caption("_Sense skills detectades_")

    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

    st.markdown(
        "<p style='font-size:1rem;font-weight:700;letter-spacing:1px;text-transform:uppercase;"
        "color:white;margin-bottom:8px'>🌐 Idiomes</p>",
        unsafe_allow_html=True,
    )
    if profile.languages:
        lang_html = "".join(
            f"<div style='display:inline-flex;align-items:center;gap:8px;"
            f"background:rgba(0,0,0,.04);border-radius:10px;padding:8px 16px;"
            f"margin:4px 6px 4px 0;border:1px solid rgba(0,0,0,.08)'>"
            f"<span style='font-weight:700;font-size:0.95rem'>{lang.language}</span>"
            f"<span style='background:{_LEVEL_COLOR.get(lang.level.lower().replace(' ',''), '#555')};"
            f"color:white;border-radius:6px;padding:2px 9px;"
            f"font-size:0.75rem;font-weight:700'>{lang.level}</span>"
            f"</div>"
            for lang in profile.languages
        )
        st.markdown(f"<div style='line-height:3'>{lang_html}</div>", unsafe_allow_html=True)
    else:
        st.caption("_Sense idiomes detectats_")


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

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

if "selected" not in st.session_state:
    st.session_state.selected = None
if "dropdown_v" not in st.session_state:
    st.session_state.dropdown_v = 0
if "detail_view" not in st.session_state:
    st.session_state.detail_view = "pdf"

examples = list_example_pdfs()

st.markdown(
    "<style>div[data-baseweb='select'] { cursor: pointer; }"
    "div[data-baseweb='select'] * { cursor: pointer; }</style>",
    unsafe_allow_html=True,
)

# ─── Capçalera: títol + dropdown | upload ─────────────────────────────
hdr_left, hdr_right = st.columns([3, 2], gap="large")

with hdr_left:
    st.title("🎯 SmartCV")
    st.caption("Sistema multi-agent de matching semàntic CV ↔ oferta")

    if examples:
        nn_list = list(examples.keys())
        labels = []
        for nn in nn_list:
            p = load_cached(cache_path_for_nn(nn))
            labels.append(p.name if p else f"CV #{nn}")
        label_to_nn = dict(zip(labels, nn_list))

        chosen_label = st.selectbox(
            "Currículums d'exemple",
            options=labels,
            index=None,
            placeholder="Selecciona un currículum d'exemple...",
            label_visibility="collapsed",
            key=f"cv_dropdown_{st.session_state.dropdown_v}",
        )
        if chosen_label:
            st.session_state.selected = ("example", label_to_nn[chosen_label])

with hdr_right:
    st.subheader("Afegir currículum")
    uploaded = st.file_uploader("Puja un PDF", type=["pdf"], key="uploader")
    if uploaded is not None:
        stem = Path(uploaded.name).stem
        target_pdf = UPLOADS_DIR / uploaded.name
        if not target_pdf.exists():
            target_pdf.write_bytes(uploaded.getbuffer())
        if st.button("Processar currículum pujat", key="btn_process_upload"):
            st.session_state.selected = ("upload", stem)
            st.rerun()

# ─── Detall del CV seleccionat ────────────────────────────────────────
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
        header_l, header_r = st.columns([4, 1])
        with header_l:
            st.subheader(f"Anàlisi — {pdf_path.name}")
        with header_r:
            if st.button("Esborrar currículum actual", use_container_width=True):
                st.session_state.selected = None
                st.session_state.dropdown_v += 1
                st.session_state.detail_view = "pdf"
                st.rerun()

        profile = load_cached(cache)
        if profile is None:
            profile = run_interpret_with_ui(pdf_path, cache)

        left_col, right_col = st.columns([1, 1], gap="large")

        with left_col:
            tab_pdf, tab_data = st.tabs(["📄 PDF original", "📋 Dades extretes"])
            with tab_pdf:
                render_pdf(pdf_path)
            with tab_data:
                if profile:
                    render_profile(profile)
                else:
                    st.info("Encara no hi ha dades extretes per a aquest currículum.")

        with right_col:
            if profile:
                top = render_ranking(profile)
                st.divider()
                render_advisor_chat(profile, top)
            else:
                st.info("Processa el currículum per veure el rànquing i el chat assessor.")
