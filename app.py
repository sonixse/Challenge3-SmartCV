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
from src.schemas.candidate import CandidateProfile

EXAMPLES_DIR = Path("data/synth/raw")
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

# ─── Ranking placeholder ──────────────────────────────────────────────
st.divider()
st.header("Rànquing d'ofertes")
st.info("🚧 **Properament:** matching semàntic amb ofertes (Alan Turing + Marie Curie + Hedy Lamarr)")
