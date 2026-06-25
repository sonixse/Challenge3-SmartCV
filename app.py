import base64
import re
from pathlib import Path

import streamlit as st

# Must be the very first Streamlit call
st.set_page_config(
    page_title="SmartCV · AI Job Matching",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed",
)

from src.ui.skill_icons import skill_icon_html
from src.agents.interpreter import DEFAULT_OUTPUT_DIR, interpret, load_profile, save_profile
from src.agents.podium import PodiumEntry, build_entry
from src.agents.qualifier import qualify
from src.data.load_vacancies import load as load_vacancies
from src.schemas.candidate import CandidateProfile
from src.schemas.vacancy import Vacancy

# ─── Constants ────────────────────────────────────────────────────────

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
UPLOADS_DIR   = Path("data/uploads")

# ─── Backend helpers (unchanged logic) ───────────────────────────────

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
    try:
        from src.agents.linguist import analyse
        return analyse
    except Exception:
        return None


def _fallback_linguist(candidate: CandidateProfile, vacancy: Vacancy) -> dict:
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
        out_skills.append({
            "vacancy_skill": req.name,
            "best_match": best,
            "similarity": 0.0,
            "classification": cls,
        })
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
    grey_zone: list[str] = linguist_result.get("grey_zone") or [
        s["vacancy_skill"]
        for s in linguist_result.get("skills", [])
        if s.get("classification") == "GREY ZONE"
    ]
    if not grey_zone:
        return linguist_result
    try:
        from src.agents.detective import resolve as detective_resolve
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
        knowledge = st.session_state.get("detective_knowledge", {})
        for skill, verdict in det.verdicts.items():
            if skill not in knowledge:
                knowledge[skill] = {
                    "classification": verdict.classification,
                    "reasoning": verdict.reasoning,
                }
        st.session_state.detective_knowledge = knowledge
    except Exception:
        pass
    return linguist_result


def compute_ranking(profile: CandidateProfile, top_n: int = 10) -> list[PodiumEntry]:
    st.session_state.detective_knowledge = {}
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


def _vacancy_by_id(vid: int) -> Vacancy | None:
    return next((v for v in _cached_vacancies() if v.id == vid), None)

# ─── File / cache helpers ─────────────────────────────────────────────

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
        import fitz
        doc = fitz.open(pdf_path_str)
        page = doc.load_page(0)
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
        with st.spinner(f"Processing {pdf_path.name} with AI — may take 30–60 s…"):
            profile = interpret(str(pdf_path))
        save_profile(profile, str(cache_path))
        return profile
    except Exception as e:
        msg = str(e).lower()
        if any(tok in msg for tok in ("connect", "refus", "ollama", "11434", "connection")):
            st.error(
                "Cannot connect to Ollama. Make sure `ollama serve` is running "
                "and `llama3` is installed (`ollama pull llama3`)."
            )
        else:
            st.error(f"Error processing CV: {e}")
        return None


def render_pdf(pdf_path: Path, height: int = 520) -> None:
    try:
        data = pdf_path.read_bytes()
    except Exception as e:
        st.warning(f"Could not read PDF: {e}")
        return
    b64 = base64.b64encode(data).decode("utf-8")
    st.markdown(
        f'<iframe src="data:application/pdf;base64,{b64}" '
        f'width="100%" height="{height}" '
        f'style="border:none;border-radius:12px;"></iframe>',
        unsafe_allow_html=True,
    )

# ─── UI render helpers ────────────────────────────────────────────────

def render_profile(profile: CandidateProfile) -> None:
    exp_col, edu_col = st.columns([1, 2])
    with exp_col:
        st.markdown(
            "<div style='background:linear-gradient(135deg,#4F46E5,#7C3AED);color:white;"
            "border-radius:14px;padding:16px;text-align:center;"
            "min-height:110px;display:flex;flex-direction:column;justify-content:center'>"
            "<div style='font-size:0.76rem;font-weight:700;letter-spacing:1px;"
            "text-transform:uppercase;margin-bottom:4px'>💼 Experience</div>"
            f"<div style='font-size:2.8rem;font-weight:900;line-height:1'>{profile.years_experience}</div>"
            "<div style='font-size:0.78rem;opacity:.85;margin-top:2px'>years</div>"
            "</div>",
            unsafe_allow_html=True,
        )
    with edu_col:
        st.markdown(
            "<div style='background:linear-gradient(135deg,#065F46,#059669);color:white;"
            "border-radius:14px;padding:16px 18px;"
            "min-height:110px;display:flex;flex-direction:column;justify-content:center'>"
            "<div style='font-size:0.76rem;font-weight:700;letter-spacing:1px;"
            "text-transform:uppercase;margin-bottom:6px'>🎓 Education</div>"
            f"<div style='font-size:1.25rem;font-weight:800;line-height:1.2'>{profile.education_level}</div>"
            f"<div style='font-size:0.82rem;opacity:.85;margin-top:4px'>{profile.education_field}</div>"
            "</div>",
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    st.markdown(
        "<p style='font-size:0.78rem;font-weight:700;letter-spacing:1px;"
        "text-transform:uppercase;color:#A100FF;margin:0 0 6px 0'>🛠 Skills</p>",
        unsafe_allow_html=True,
    )
    if profile.skills:
        icons_html = "".join(
            f"<span title='{s.name}' style='display:inline-flex;align-items:center;"
            f"justify-content:center;width:30px;height:30px;margin:2px;"
            f"background:#1F1A2E;border-radius:7px'>"
            f"{skill_icon_html(s.name, size=18)}</span>"
            for s in profile.skills
            if skill_icon_html(s.name, size=18)
        )
        if icons_html:
            st.markdown(f"<div style='margin-bottom:6px'>{icons_html}</div>", unsafe_allow_html=True)

        tags = "".join(
            f"<span style='display:inline-block;background:rgba(161,0,255,0.12);color:#C084FC;"
            f"border:1px solid rgba(161,0,255,0.3);border-radius:20px;padding:4px 12px;"
            f"margin:3px 4px 3px 0;font-size:0.82rem;font-weight:600'>"
            f"{s.name}{(' · ' + str(s.years) + 'y') if s.years is not None else ''}</span>"
            for s in profile.skills
        )
        st.markdown(f"<div style='line-height:2.4'>{tags}</div>", unsafe_allow_html=True)
    else:
        st.caption("No skills detected")

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    st.markdown(
        "<p style='font-size:0.78rem;font-weight:700;letter-spacing:1px;"
        "text-transform:uppercase;color:#A100FF;margin:0 0 6px 0'>🌐 Languages</p>",
        unsafe_allow_html=True,
    )
    if profile.languages:
        lang_parts = []
        for lang in profile.languages:
            color = _LEVEL_COLOR.get(lang.level.lower().replace(" ", ""), "#555")
            lang_parts.append(
                f"<div style='display:inline-flex;align-items:center;gap:6px;"
                f"background:#1A1A1A;border-radius:10px;padding:5px 12px;"
                f"margin:3px 5px 3px 0;border:1px solid rgba(255,255,255,0.1)'>"
                f"<span style='font-weight:700;font-size:0.88rem;color:white'>{lang.language}</span>"
                f"<span style='background:{color};color:white;border-radius:5px;"
                f"padding:2px 7px;font-size:0.7rem;font-weight:700'>{lang.level}</span>"
                f"</div>"
            )
        st.markdown(f"<div>{''.join(lang_parts)}</div>", unsafe_allow_html=True)
    else:
        st.caption("No languages detected")


def render_ranking(profile: CandidateProfile) -> list[PodiumEntry]:
    st.markdown(
        "<p style='font-size:0.78rem;font-weight:700;letter-spacing:1px;"
        "text-transform:uppercase;color:#A100FF;margin:0 0 6px 0'>🏆 Best Job Matches</p>",
        unsafe_allow_html=True,
    )

    with st.spinner("Computing matches…"):
        top = compute_ranking(profile)

    total_offers = len(_cached_vacancies())

    if not top:
        st.warning(
            f"No matches found among {total_offers} offers — "
            "candidate is eliminated by language or experience requirements."
        )
        return []

    st.caption(f"Showing {len(top)} of {total_offers} offers · sorted by AI match score")

    def _signal(reason: str | None, label: str) -> str:
        if reason is None:
            return f"<span style='color:#16a34a;font-size:0.76rem;font-weight:600'>✓ {label}</span>"
        short = reason.split("·")[0].strip() if "·" in reason else reason
        return f"<span style='color:#b45309;font-size:0.76rem'>⚠ {short}</span>"

    cards_html = ""
    for rank, entry in enumerate(top, start=1):
        vac = _vacancy_by_id(entry.offer_id)

        signals = (
            _signal(entry.reasons.language, "Language")
            + "&nbsp;&nbsp;"
            + _signal(entry.reasons.experience, "Experience")
            + "&nbsp;&nbsp;"
            + _signal(entry.reasons.education, "Education")
        )

        vac_meta = ""
        if vac is not None:
            vac_meta = (
                f"<div style='font-size:0.74rem;color:#9CA3AF;margin-top:1px'>"
                f"#{vac.id} · ≥{vac.years_experience}y exp · {vac.highest_degree}</div>"
            )

        score = entry.score_match
        if score >= 70:
            score_bg = "linear-gradient(135deg,#A100FF,#7C3AED)"
        elif score >= 50:
            score_bg = "linear-gradient(135deg,#D97706,#F59E0B)"
        else:
            score_bg = "linear-gradient(135deg,#DC2626,#EF4444)"

        flags_html = ""
        if entry.flags:
            flags_html = (
                "<div style='margin-top:4px'>"
                + "".join(
                    f"<span style='font-size:0.68rem;background:rgba(161,0,255,0.15);color:#C084FC;"
                    f"border-radius:5px;padding:1px 6px;margin-right:4px'>{f}</span>"
                    for f in entry.flags
                )
                + "</div>"
            )

        cards_html += (
            f"<div style='border:1px solid rgba(255,255,255,0.07);border-radius:14px;padding:12px 15px;"
            f"margin-bottom:9px;background:#1A1A1A;display:flex;gap:12px;align-items:center;'>"
            f"<div style='text-align:center;background:{score_bg};color:white;"
            f"border-radius:11px;padding:9px 12px;min-width:60px;flex-shrink:0;'>"
            f"<div style='font-size:1.65rem;font-weight:900;line-height:1'>{score}</div>"
            f"<div style='font-size:0.6rem;opacity:0.85;font-weight:600'>% match</div>"
            f"</div>"
            f"<div style='flex:1;min-width:0;'>"
            f"<div style='font-weight:700;color:#F9FAFB;font-size:0.94rem;"
            f"white-space:nowrap;overflow:hidden;text-overflow:ellipsis;'>"
            f"#{rank} — {entry.role} "
            f"<span style='color:#A100FF;font-size:0.78rem;font-weight:500'>{entry.sector}</span>"
            f"</div>"
            f"{vac_meta}"
            f"<div style='margin-top:5px'>{signals}</div>"
            f"{flags_html}"
            f"</div>"
            f"</div>"
        )

    st.markdown(
        f"<div style='max-height:60vh;overflow-y:auto;padding-right:4px'>{cards_html}</div>",
        unsafe_allow_html=True,
    )
    return top

# ─── Global CSS ───────────────────────────────────────────────────────

st.markdown("""
<style>
/* ── Demo chrome removal ── */
#MainMenu { visibility: hidden !important; }
footer    { visibility: hidden !important; }
[data-testid="stDecoration"] { display: none !important; }
[data-testid="stHeader"] {
    height: 0 !important;
    min-height: 0 !important;
    background: transparent !important;
}

/* ── Dark background ── */
.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
section[data-testid="stMain"],
.main {
    background: #0D0D0D !important;
}
.main .block-container,
[data-testid="block-container"] {
    padding-top: 0.2rem !important;
    padding-bottom: 2rem !important;
    max-width: 1380px !important;
    background: #0D0D0D !important;
}

/* ── Buttons — Accenture purple ── */
.stButton > button {
    background: #A100FF !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    letter-spacing: 0.2px !important;
    transition: opacity 0.2s !important;
    padding: 0.5rem 1.2rem !important;
}
.stButton > button:hover { opacity: 0.82 !important; color: white !important; }

/* ── File uploader — dark ── */
[data-testid="stFileUploadDropzone"] {
    border: 2px dashed rgba(161,0,255,0.45) !important;
    border-radius: 12px !important;
    background: rgba(161,0,255,0.05) !important;
}
[data-testid="stFileUploadDropzone"] p,
[data-testid="stFileUploadDropzone"] span,
[data-testid="stFileUploadDropzone"] small { color: #9CA3AF !important; }

/* ── Tabs — dark ── */
[data-testid="stTabs"] [data-baseweb="tab-list"] {
    gap: 4px;
    background: #1A1A1A;
    border-radius: 12px;
    padding: 4px;
    border: none;
}
[data-testid="stTabs"] [data-baseweb="tab"] {
    border-radius: 9px !important;
    font-weight: 600 !important;
    color: #9CA3AF !important;
    padding: 6px 18px !important;
}
[data-testid="stTabs"] [aria-selected="true"] {
    background: #2A2A2A !important;
    color: white !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.4) !important;
}

/* ── Selectbox — dark ── */
[data-baseweb="select"] > div:first-child {
    background: #1A1A1A !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    border-radius: 10px !important;
    color: white !important;
}

/* ── Bordered containers — dark ── */
[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 16px !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    background: #1A1A1A !important;
    padding: 24px 32px !important;
    box-shadow: none !important;
    box-sizing: border-box !important;
    min-height: 380px !important;
    height: 380px !important;
    overflow: auto !important;
}

/* ── Alerts ── */
[data-testid="stAlert"] { background: rgba(161,0,255,0.08) !important; border-color: rgba(161,0,255,0.3) !important; }
[data-testid="stAlert"] p { color: #E5E7EB !important; }

/* ── Spinner ── */
.stSpinner > div { color: #A100FF !important; }

/* ── Caption ── */
[data-testid="stCaptionContainer"] p { color: #6B7280 !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: #0D0D0D; border-radius: 10px; }
::-webkit-scrollbar-thumb { background: rgba(161,0,255,0.45); border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

# ─── Init ─────────────────────────────────────────────────────────────

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

for _k, _v in [("selected", None), ("dropdown_v", 0), ("detective_knowledge", {})]:
    if _k not in st.session_state:
        st.session_state[_k] = _v

examples = list_example_pdfs()

# ─── Main content ─────────────────────────────────────────────────────

selection = st.session_state.selected

if selection is None:
    # ── Full-width hero: centered ─────────────────────────────────────
    st.markdown(
        "<div style='text-align:center;padding:0 0 28px 0;'>"
        "<div style='display:inline-flex;align-items:center;gap:24px;margin-bottom:18px;'>"
        "<h1 style='font-size:5rem;font-weight:900;letter-spacing:-3px;line-height:1;margin:0;"
        "background:linear-gradient(90deg,#ffffff 0%,#A100FF 100%);"
        "-webkit-background-clip:text;-webkit-text-fill-color:transparent;"
        "background-clip:text;'>SmartCV</h1>"
        "<p style='color:rgba(255,255,255,0.55);font-size:1.8rem;font-weight:600;"
        "letter-spacing:10px;text-transform:uppercase;margin:0;line-height:1;'>"
        "AI &nbsp;&nbsp;&nbsp; Job &nbsp;&nbsp;&nbsp; Matching</p>"
        "</div>"
        "<br>"
        "<h2 style='font-size:3.2rem;font-weight:900;"
        "letter-spacing:-1px;line-height:1.15;margin:0;color:white;'>"
        "Find the jobs where you truly fit."
        "</h2>"
        "</div>",
        unsafe_allow_html=True,
    )

    # ── Linear ticker with separator ─────────────────────────────────
    _TICKER_DATA = [
        ("📄", "#FF8C42", "Ada Lovelace",       "Reads your CV"),
        ("⚖️", "#60A5FA", "Marie Curie",         "Filters hard rules"),
        ("🧠", "#34D399", "Alan Turing",         "Matches your skills"),
        ("🔍", "#FBBF24", "Hedy Lamarr",         "Resolves grey zones"),
        ("🥇", "#F87171", "Serena Williams",     "Scores & ranks"),
        ("💡", "#C084FC", "Steve Jobs",          "Coaches you"),
        ("🏆", "#FCD34D", "Johannes Gutenberg",  "Publishes results"),
    ]

    _separator = (
        "<div style='display:inline-flex;align-items:center;gap:14px;"
        "padding:0 40px;flex-shrink:0;'>"
        "<span style='font-size:1.3rem;font-weight:800;letter-spacing:3px;"
        "text-transform:uppercase;color:white;white-space:nowrap;'>7 AI agents</span>"
        "<span style='color:#A100FF;font-size:1.6rem;'>&middot;</span>"
        "<span style='font-size:1.3rem;font-weight:800;letter-spacing:3px;"
        "text-transform:uppercase;color:white;white-space:nowrap;'>one pipeline</span>"
        "</div>"
        "<span style='color:rgba(161,0,255,0.35);font-size:2rem;padding:0 10px;flex-shrink:0;'>|</span>"
    )

    def _tk(emoji, color, name, role):
        return (
            f"<div style='display:inline-flex;align-items:center;gap:16px;"
            f"background:#1A1A1A;border:1px solid rgba(255,255,255,0.09);"
            f"border-radius:20px;padding:24px 36px;margin-right:20px;flex-shrink:0;'>"
            f"<span style='font-size:3rem;line-height:1;'>{emoji}</span>"
            f"<div>"
            f"<div style='font-size:1.5rem;font-weight:800;letter-spacing:0.3px;"
            f"background:linear-gradient(90deg,#ffffff,{color});"
            f"-webkit-background-clip:text;-webkit-text-fill-color:transparent;"
            f"background-clip:text;white-space:nowrap;'>{role}</div>"
            f"<div style='font-size:1.1rem;color:#9CA3AF;font-weight:600;"
            f"white-space:nowrap;margin-top:4px;'>{name}</div>"
            f"</div>"
            f"</div>"
        )

    _items = "".join(_tk(*a) for a in _TICKER_DATA) + _separator
    _track  = _items + _items   # duplicate for seamless loop

    st.markdown(
        "<style>"
        "@keyframes sc-ticker {"
        "  0%   { transform:translateX(0); }"
        "  100% { transform:translateX(-50%); }"
        "}"
        ".sc-ticker-track {"
        "  display:inline-flex;align-items:center;"
        "  animation:sc-ticker 30s linear infinite;"
        "  width:max-content;"
        "}"
        ".sc-ticker-track:hover { animation-play-state:paused; }"
        "</style>"
        "<div style='border-top:1px solid rgba(255,255,255,0.08);"
        "border-bottom:1px solid rgba(255,255,255,0.08);"
        "overflow:hidden;padding:22px 0;margin-bottom:36px;"
        "mask-image:linear-gradient(90deg,transparent 0%,black 5%,black 95%,transparent 100%);'>"
        f"<div class='sc-ticker-track'>{_track}</div>"
        "</div>",
        unsafe_allow_html=True,
    )

    # ── Left: text + extracted info │ Right: upload + try ─────────────
    txt_col, cards_col = st.columns([1, 1], gap="large")

    with txt_col:
        st.markdown(
            # ── Headline
            "<h2 style='color:white;font-size:3rem;font-weight:900;"
            "letter-spacing:-1px;line-height:1.1;margin:0 0 10px 0;'>"
            "Your CV, decoded in seconds."
            "</h2>"
            # ── Subtext
            "<p style='color:rgba(255,255,255,0.65);font-size:1.25rem;font-weight:400;"
            "line-height:1.6;margin:0 0 20px 0;'>"
            "We read your CV, match your skills semantically against real job offers, "
            "and return a <span style='color:white;font-weight:600;'>ranked list</span> "
            "with the <span style='color:white;font-weight:600;'>exact reasons</span> "
            "behind every score. No black boxes."
            "</p>"
            # ── Extracted info label
            "<p style='font-size:1.3rem;font-weight:700;letter-spacing:1.5px;"
            "text-transform:uppercase;color:#A100FF;margin:0 0 10px 0;'>What we extract</p>"
            # ── Bullet list
            "<div style='color:#9CA3AF;font-size:1.5rem;line-height:2.1;font-weight:500;"
            "margin:0 0 22px 0;'>"
            "✦ &nbsp;Skills &amp; years of experience<br>"
            "✦ &nbsp;Education level &amp; field<br>"
            "✦ &nbsp;Languages &amp; proficiency"
            "</div>"
            # ── Assessor callout
            "<div style='background:rgba(161,0,255,0.08);border:1px solid rgba(161,0,255,0.25);"
            "border-left:3px solid #A100FF;border-radius:12px;padding:14px 18px;'>"
            "<p style='font-size:1.3rem;font-weight:800;letter-spacing:1px;"
            "text-transform:uppercase;margin:0 0 8px 0;color:#A100FF;'>SmartCV Assessor</p>"
            "<p style='color:rgba(255,255,255,0.8);font-size:1.2rem;line-height:1.6;margin:0;'>"
            "Not sure why a match failed or how to improve? "
            "<strong style='color:white;'>Ask our AI assessor</strong>: "
            "it explains every decision and gives you concrete advice."
            "</p>"
            "</div>",
            unsafe_allow_html=True,
        )

    with cards_col:
        with st.container(border=True):
            st.markdown(
                "<h3 style='font-size:2.4rem;font-weight:900;color:white;margin:8px 0 12px 0;'>"
                "Upload your CV</h3>"
                "<p style='color:#9CA3AF;font-size:1.25rem;margin:0 0 18px 0;line-height:1.6;'>"
                "Use a PDF. Once loaded, press Analyse — your profile and ranking will open."
                "</p>",
                unsafe_allow_html=True,
            )
            uploaded = st.file_uploader(
                "Upload PDF",
                type=["pdf"],
                label_visibility="collapsed",
                key="uploader",
            )
            if uploaded is not None:
                stem = Path(uploaded.name).stem
                target_pdf = UPLOADS_DIR / uploaded.name
                if not target_pdf.exists():
                    target_pdf.write_bytes(uploaded.getbuffer())
                st.success(f"✅ {uploaded.name} — ready!")
                if st.button("🚀  Analyse my CV", use_container_width=True, key="btn_process_upload"):
                    st.session_state.selected = ("upload", stem)
                    st.rerun()

        st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

        with st.container(border=True):
            st.markdown(
                "<h3 style='font-size:2.4rem;font-weight:900;color:white;margin:8px 0 12px 0;'>"
                "Try a sample profile</h3>"
                "<p style='color:#9CA3AF;font-size:1.25rem;margin:0 0 18px 0;line-height:1.6;'>"
                "No CV handy? Pick one of our pre-loaded profiles and see the full analysis live — no upload needed."
                "</p>"
                "<p style='font-size:1rem;font-weight:700;letter-spacing:1px;"
                "text-transform:uppercase;color:#A100FF;margin:0 0 10px 0;'>"
                "Available profiles</p>",
                unsafe_allow_html=True,
            )
            if examples:
                nn_list = list(examples.keys())
                labels = []
                for nn in nn_list:
                    p = load_cached(cache_path_for_nn(nn))
                    labels.append(p.name if p else f"CV #{nn}")
                label_to_nn = dict(zip(labels, nn_list))
                chosen_label = st.selectbox(
                    "Sample CV",
                    options=labels,
                    index=None,
                    placeholder="Select a sample profile…",
                    label_visibility="collapsed",
                    key=f"cv_dropdown_{st.session_state.dropdown_v}",
                )
                if chosen_label:
                    st.session_state.selected = ("example", label_to_nn[chosen_label])
                    st.rerun()
            else:
                st.info("No sample CVs found in data/raw/")

else:
    # ── DETAIL VIEW ───────────────────────────────────────────────────

    kind, key = selection
    if kind == "example":
        pdf_path = examples.get(key)
        cache = cache_path_for_nn(key)
    else:
        matches = list(UPLOADS_DIR.glob(f"{key}.*"))
        pdf_path = matches[0] if matches else None
        cache = cache_path_for_upload(key)

    if pdf_path is None or not pdf_path.exists():
        st.warning("PDF not found.")
        if st.button("← Back"):
            st.session_state.selected = None
            st.rerun()
    else:
        profile = load_cached(cache)
        if profile is None:
            profile = run_interpret_with_ui(pdf_path, cache)

        # Top bar: name + back button
        top_l, top_r = st.columns([5, 1])
        with top_l:
            if profile:
                meta_parts = []
                if profile.location:
                    meta_parts.append(f"📍 {profile.location}")
                if profile.contact:
                    meta_parts.append(f"✉️ {profile.contact}")
                meta_str = " &nbsp;·&nbsp; ".join(meta_parts)
                st.markdown(
                    f"<h2 style='margin:0 0 2px 0;font-size:1.55rem;font-weight:800;"
                    f"color:white;line-height:1.1'>{profile.name}</h2>"
                    f"<p style='margin:0;color:#6B7280;font-size:0.82rem'>{meta_str}</p>",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f"<h2 style='margin:0;font-size:1.4rem;font-weight:800;color:white'>"
                    f"{pdf_path.name}</h2>",
                    unsafe_allow_html=True,
                )
        with top_r:
            if st.button("← Change CV", use_container_width=True):
                st.session_state.selected = None
                st.session_state.dropdown_v += 1
                st.rerun()

        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

        # Two-column layout
        left_col, right_col = st.columns([1, 1], gap="large")

        with left_col:
            tab_pdf, tab_data = st.tabs(["📄 Original PDF", "📋 Extracted Profile"])
            with tab_pdf:
                render_pdf(pdf_path, height=520)
            with tab_data:
                if profile:
                    render_profile(profile)
                else:
                    st.info("No profile data yet — process the CV first.")

        with right_col:
            if profile:
                render_ranking(profile)
            else:
                st.info("Process the CV to see job matches.")
