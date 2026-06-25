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
from src.agents.podium import PodiumEntry
from src.config import MODEL
from src.data.load_vacancies import load as load_vacancies
from src.schemas.candidate import CandidateProfile
from src.schemas.vacancy import Vacancy
from src.i18n import init_lang, t, render_lang_switcher

# ─── Constants ────────────────────────────────────────────────────────

_LEVEL_COLOR = {
    "native": "#15803d", "c2": "#15803d",
    "c1": "#1d4ed8", "b2": "#7c3aed",
    "b1": "#b45309", "a2": "#dc2626", "a1": "#dc2626",
}

EXAMPLES_DIR = Path("data/raw")
PROCESSED_DIR = Path(DEFAULT_OUTPUT_DIR)
UPLOADS_DIR   = Path("data/uploads")

# ─── Backend: LangGraph orchestration ─────────────────────────────────

@st.cache_resource(show_spinner=False)
def _cached_vacancies() -> list[Vacancy]:
    _, vacs = load_vacancies()
    return vacs


@st.cache_data(show_spinner=False)
def _run_graph_cached(pdf_path: str, mtime: float, model: str, candidate_json: str | None = None) -> dict:
    """Run the full LangGraph pipeline once per CV (cache key: path + mtime).
    If candidate_json is provided, the interpreter node is skipped (~8-10s saved).
    Returns only what the UI needs, not the full Pydantic state."""
    from src.orchestrator.graph import compiled
    invoke_input: dict = {"pdf_path": pdf_path, "model": model}
    if candidate_json is not None:
        invoke_input["candidate"] = CandidateProfile.model_validate_json(candidate_json)
    final_state = compiled.invoke(invoke_input)
    return {
        "candidate": final_state["candidate"].model_dump(),
        "ranking": final_state.get("podium_result", {}).get("ranking", []),
        "detective_knowledge": {
            skill: {"classification": v["classification"], "reasoning": v["reasoning"]}
            for skill, v in final_state.get("detective_result", {}).get("verdicts", {}).items()
        },
    }


def compute_ranking(
    pdf_path: str,
    model: str = MODEL,
    top_n: int = 10,
    candidate: CandidateProfile | None = None,
) -> tuple[list[PodiumEntry], CandidateProfile]:
    """Evaluate the candidate by running the full graph (single source of truth).
    Passes pre-loaded candidate to skip the interpreter node if already available."""
    mtime = Path(pdf_path).stat().st_mtime
    candidate_json = candidate.model_dump_json() if candidate else None
    result = _run_graph_cached(pdf_path, mtime, model, candidate_json)
    st.session_state.detective_knowledge = result["detective_knowledge"]
    entries = [PodiumEntry.model_validate(d) for d in result["ranking"]]
    profile = CandidateProfile.model_validate(result["candidate"])
    return entries[:top_n], profile


def _vacancy_by_id(vid: int) -> Vacancy | None:
    return next((v for v in _cached_vacancies() if v.id == vid), None)


def _epic_loader_html() -> str:
    return (
        "<style>"
        "@keyframes titleGlow{"
        "0%,100%{text-shadow:0 0 30px rgba(161,0,255,.6);}"
        "50%{text-shadow:0 0 60px rgba(161,0,255,1),0 0 120px rgba(161,0,255,.3);}}"
        "@keyframes fadeIn{from{opacity:0;transform:translateY(10px);}to{opacity:1;transform:translateY(0);}}"
        "@keyframes spinRing{from{transform:rotate(0deg);}to{transform:rotate(360deg);}}"
        "@keyframes centerPulse{"
        "0%,100%{box-shadow:0 0 0 0 rgba(161,0,255,.6);transform:translate(-50%,-50%) scale(1);}"
        "50%{box-shadow:0 0 0 12px rgba(161,0,255,0);transform:translate(-50%,-50%) scale(1.2);}}"
        "@keyframes orbit1{from{transform:rotate(0deg) translateX(38px) rotate(0deg);}to{transform:rotate(360deg) translateX(38px) rotate(-360deg);}}"
        "@keyframes orbit2{from{transform:rotate(120deg) translateX(28px) rotate(-120deg);}to{transform:rotate(480deg) translateX(28px) rotate(-480deg);}}"
        "@keyframes orbit3{from{transform:rotate(240deg) translateX(20px) rotate(-240deg);}to{transform:rotate(-120deg) translateX(20px) rotate(120deg);}}"
        "@keyframes msgCycle{"
        "0%{opacity:0;transform:translateY(5px);}"
        "3%{opacity:1;transform:translateY(0);}"
        "22%{opacity:1;transform:translateY(0);}"
        "25%{opacity:0;transform:translateY(-4px);}"
        "100%{opacity:0;}}"
        "</style>"
        "<div style='position:fixed;top:0;left:0;width:100vw;height:100vh;"
        "background:#0D0D0D;z-index:99999;"
        "display:flex;flex-direction:column;align-items:center;justify-content:center;'>"
        "<div style='animation:fadeIn .6s ease both;text-align:center;'>"
        "<div style='display:inline-flex;align-items:center;gap:28px;margin-bottom:20px;'>"
        "<div style='font-size:1.1rem;font-weight:700;letter-spacing:5px;"
        "text-transform:uppercase;color:#A100FF;'>SmartCV</div>"
        "<span style='color:rgba(255,255,255,0.15);font-size:1.4rem;'>|</span>"
        "<h1 style='font-size:2.4rem;font-weight:900;margin:0;line-height:1;"
        "background:linear-gradient(90deg,#fff 0%,#A100FF 100%);"
        "-webkit-background-clip:text;-webkit-text-fill-color:transparent;"
        f"background-clip:text;animation:titleGlow 2.5s ease-in-out infinite;'>{t('loader.agents')}</h1>"
        "</div>"
        f"<p style='color:#4B5563;font-size:1.25rem;margin:0 0 52px 0;'>"
        f"{t('loader.subtitle')}</p>"
        # ── Orbiting geometry ─────────────────────────────────────────
        "<div style='position:relative;width:160px;height:160px;margin:0 auto 52px auto;'>"
        "<div style='position:absolute;inset:0;border-radius:50%;border:2px dashed rgba(161,0,255,0.4);animation:spinRing 4s linear infinite;'></div>"
        "<div style='position:absolute;inset:20px;border-radius:50%;border:2px dashed rgba(161,0,255,0.2);animation:spinRing 3s linear infinite reverse;'></div>"
        "<div style='position:absolute;top:50%;left:50%;width:22px;height:22px;margin:-11px;border-radius:50%;background:#A100FF;animation:centerPulse 1.5s ease-in-out infinite;'></div>"
        "<div style='position:absolute;top:50%;left:50%;width:14px;height:14px;margin:-7px;border-radius:50%;background:#A100FF;animation:orbit1 2.2s linear infinite;'></div>"
        "<div style='position:absolute;top:50%;left:50%;width:11px;height:11px;margin:-5.5px;border-radius:50%;background:#7C3AED;animation:orbit2 3.1s linear infinite;'></div>"
        "<div style='position:absolute;top:50%;left:50%;width:8px;height:8px;margin:-4px;border-radius:50%;background:#C084FC;animation:orbit3 1.8s linear infinite reverse;'></div>"
        "</div>"
        # ── Cycling messages ──────────────────────────────────────────
        "<div style='position:relative;height:24px;width:480px;margin:0 auto;'>"
        f"<div style='position:absolute;width:100%;text-align:center;font-size:1rem;font-weight:700;letter-spacing:2px;color:#6B7280;animation:msgCycle 24s linear infinite 0s;'>{t('ticker.msg1')}</div>"
        f"<div style='position:absolute;width:100%;text-align:center;font-size:1rem;font-weight:700;letter-spacing:2px;color:#6B7280;animation:msgCycle 24s linear infinite -18s;'>{t('ticker.msg2')}</div>"
        f"<div style='position:absolute;width:100%;text-align:center;font-size:1rem;font-weight:700;letter-spacing:2px;color:#6B7280;animation:msgCycle 24s linear infinite -12s;'>{t('ticker.msg3')}</div>"
        f"<div style='position:absolute;width:100%;text-align:center;font-size:1rem;font-weight:700;letter-spacing:2px;color:#6B7280;animation:msgCycle 24s linear infinite -6s;'>{t('ticker.msg4')}</div>"
        "</div>"
        "</div>"
        "</div>"
    )

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
    # ── Experience + Education + Skills + Languages — compact ─────────
    lang_parts = []
    for lang in profile.languages:
        color = _LEVEL_COLOR.get(lang.level.lower().replace(" ", ""), "#555")
        lang_parts.append(
            f"<span style='display:inline-flex;align-items:center;gap:10px;"
            f"background:#1A1A1A;border-radius:12px;padding:8px 16px;"
            f"margin:4px 8px 4px 0;border:1px solid rgba(255,255,255,0.08)'>"
            f"<span style='font-weight:700;font-size:1.05rem;color:white'>{lang.language}</span>"
            f"<span style='background:{color};color:white;border-radius:7px;"
            f"padding:3px 10px;font-size:0.82rem;font-weight:700'>{lang.level}</span>"
            f"</span>"
        )

    tags = "".join(
        f"<span style='display:inline-block;background:rgba(161,0,255,0.12);color:#D8B4FE;"
        f"border:1px solid rgba(161,0,255,0.28);border-radius:18px;padding:7px 18px;"
        f"margin:4px 6px 4px 0;font-size:1.05rem;font-weight:600'>"
        f"{s.name}{(' · ' + str(s.years) + 'y') if s.years is not None else ''}</span>"
        for s in profile.skills
    ) if profile.skills else f"<span style='color:#6B7280'>{t('profile.no_skills')}</span>"

    st.markdown(
        f"<div style='margin-top:20px;display:grid;grid-template-columns:1fr 1fr;gap:14px;'>"

        # Experience
        f"<div style='background:#1A1A1A;border-radius:14px;padding:18px 20px;"
        f"border:1px solid rgba(255,255,255,0.08)'>"
        f"<div style='font-size:0.78rem;font-weight:700;letter-spacing:1.5px;"
        f"text-transform:uppercase;color:#A100FF;margin-bottom:8px'>{t('profile.experience')}</div>"
        f"<div style='font-size:2.2rem;font-weight:900;color:white;line-height:1'>{profile.years_experience}"
        f"<span style='font-size:1rem;color:#9CA3AF;margin-left:8px'>{t('profile.years')}</span></div>"
        f"</div>"

        # Education
        f"<div style='background:#1A1A1A;border-radius:14px;padding:18px 20px;"
        f"border:1px solid rgba(255,255,255,0.08)'>"
        f"<div style='font-size:0.78rem;font-weight:700;letter-spacing:1.5px;"
        f"text-transform:uppercase;color:#A100FF;margin-bottom:8px'>{t('profile.education')}</div>"
        f"<div style='font-size:1.1rem;font-weight:800;color:white;line-height:1.35'>{profile.education_level}"
        f"<br><span style='font-size:0.95rem;color:#9CA3AF;font-weight:500'>{profile.education_field}</span></div>"
        f"</div>"

        "</div>"

        # Skills
        f"<div style='margin-top:18px'>"
        f"<div style='font-size:0.78rem;font-weight:700;letter-spacing:1.5px;"
        f"text-transform:uppercase;color:#A100FF;margin-bottom:10px'>{t('profile.skills')}</div>"
        f"<div style='line-height:2.6'>{tags}</div>"
        f"</div>"

        # Languages
        f"<div style='margin-top:18px'>"
        f"<div style='font-size:0.78rem;font-weight:700;letter-spacing:1.5px;"
        f"text-transform:uppercase;color:#A100FF;margin-bottom:10px'>{t('profile.languages')}</div>"
        f"<div>{''.join(lang_parts) if lang_parts else '<span style=color:#6B7280>' + t('profile.no_langs') + '</span>'}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )


def render_ranking(top: list[PodiumEntry]) -> list[PodiumEntry]:
    total_offers = len(_cached_vacancies())

    st.markdown(
        "<div style='margin-bottom:20px;'>"
        "<div style='font-size:2.2rem;font-weight:900;color:white;line-height:1;margin-bottom:6px;"
        "background:linear-gradient(90deg,#ffffff,#A100FF);"
        "-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;'>"
        f"{t('ranking.title')}</div>"
        f"<div style='font-size:0.9rem;color:#6B7280;font-weight:500;letter-spacing:.5px'>"
        f"{t('ranking.caption', n=len(top), total=total_offers)}</div>"
        "</div>",
        unsafe_allow_html=True,
    )

    if not top:
        st.warning(t("ranking.no_matches", total=total_offers))
        st.markdown(
            "<div style='background:rgba(161,0,255,0.08);border:1px solid rgba(161,0,255,0.25);"
            "border-left:3px solid #A100FF;border-radius:12px;padding:14px 18px;margin-top:12px;'>"
            "<p style='color:#A100FF;font-size:0.85rem;font-weight:700;letter-spacing:1px;"
            "text-transform:uppercase;margin:0 0 5px 0;'>SmartCV Assessor</p>"
            "<p style='color:rgba(255,255,255,0.75);font-size:0.95rem;margin:0;line-height:1.5;'>"
            "Ask the assessor below why you got 0 matches and what to improve."
            "</p></div>",
            unsafe_allow_html=True,
        )
        return []

    medal = {1: "🥇", 2: "🥈", 3: "🥉"}

    def _signal(reason: str | None, label: str) -> str:
        if reason is None:
            return (
                f"<span style='display:inline-flex;align-items:center;gap:5px;"
                f"background:rgba(22,163,74,0.13);color:#4ade80;border-radius:8px;"
                f"padding:4px 10px;font-size:0.78rem;font-weight:700'>"
                f"✓ {label}</span>"
            )
        short = reason.split("·")[0].strip() if "·" in reason else reason
        return (
            f"<span style='display:inline-flex;align-items:center;gap:5px;"
            f"background:rgba(217,119,6,0.13);color:#fbbf24;border-radius:8px;"
            f"padding:4px 10px;font-size:0.78rem;font-weight:700'>"
            f"⚠ {short}</span>"
        )

    cards_html = "<style>@keyframes cardIn{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:translateY(0)}}</style>"

    for rank, entry in enumerate(top, start=1):
        vac = _vacancy_by_id(entry.offer_id)
        score = entry.score_match

        if score >= 70:
            score_bg  = "linear-gradient(135deg,#A100FF,#7C3AED)"
            bar_color = "#A100FF"
        elif score >= 40:
            score_bg  = "linear-gradient(135deg,#D97706,#F59E0B)"
            bar_color = "#F59E0B"
        else:
            score_bg  = "linear-gradient(135deg,#DC2626,#EF4444)"
            bar_color = "#EF4444"

        rank_label = medal.get(rank, f"#{rank}")

        exp_req = f"≥{vac.years_experience}y" if vac else ""
        deg_req = vac.highest_degree if vac else ""
        meta = f"{exp_req} · {deg_req}" if exp_req else ""

        signals = " ".join([
            _signal(entry.reasons.language,   t("ranking.sig_lang")),
            _signal(entry.reasons.experience, t("ranking.sig_exp")),
            _signal(entry.reasons.education,  t("ranking.sig_edu")),
        ])

        flags_html = ""
        if entry.flags:
            flags_html = "<div style='margin-top:8px;display:flex;gap:6px;flex-wrap:wrap'>" + "".join(
                f"<span style='font-size:0.7rem;background:rgba(161,0,255,0.15);color:#C084FC;"
                f"border-radius:6px;padding:2px 8px;font-weight:600'>{f}</span>"
                for f in entry.flags
            ) + "</div>"

        # ── Expandable details: full vacancy info (i18n) ──────────
        details_html = ""
        if vac:
            def _chip(text: str, bg: str, fg: str, border: str | None = None) -> str:
                bd = f"border:1px solid {border};" if border else ""
                return (
                    f"<span style='display:inline-block;background:{bg};color:{fg};{bd}"
                    f"border-radius:10px;padding:6px 14px;margin:4px 6px 4px 0;"
                    f"font-size:0.95rem;font-weight:600'>{text}</span>"
                )

            must_skills  = [s for s in vac.skills if s.type == "must_have"   and s.name.lower() != "languages"]
            nice_skills  = [s for s in vac.skills if s.type == "nice_to_have"]
            other_skills = [s for s in vac.skills if s.type is None          and s.name.lower() != "languages"]

            sections: list[str] = []

            meta_chips = [
                _chip(t("offer.years_exp", n=vac.years_experience),
                      "rgba(255,255,255,0.05)", "#E5E7EB", "rgba(255,255,255,0.1)"),
                _chip(vac.highest_degree,
                      "rgba(255,255,255,0.05)", "#E5E7EB", "rgba(255,255,255,0.1)"),
                _chip(t("offer.internship_yes") if vac.has_internship else t("offer.internship_no"),
                      "rgba(255,255,255,0.05)", "#E5E7EB", "rgba(255,255,255,0.1)"),
                _chip(t("offer.id", id=vac.id),
                      "rgba(255,255,255,0.05)", "#9CA3AF", "rgba(255,255,255,0.1)"),
            ]
            sections.append(f"<div style='margin-top:6px'>{''.join(meta_chips)}</div>")

            def _block(label_key: str, color: str, chips_html: str) -> str:
                return (
                    f"<div style='margin-top:14px'>"
                    f"<div style='font-size:0.82rem;font-weight:800;letter-spacing:1.5px;"
                    f"text-transform:uppercase;color:{color};margin-bottom:6px'>{t(label_key)}</div>"
                    f"<div>{chips_html}</div></div>"
                )

            if must_skills:
                chips = "".join(_chip(s.name, "rgba(161,0,255,0.18)", "#D8B4FE", "rgba(161,0,255,0.4)") for s in must_skills)
                sections.append(_block("offer.must", "#A100FF", chips))
            if nice_skills:
                chips = "".join(_chip(s.name, "rgba(99,102,241,0.12)", "#A5B4FC", "rgba(99,102,241,0.3)") for s in nice_skills)
                sections.append(_block("offer.nice", "#818CF8", chips))
            if other_skills:
                chips = "".join(_chip(s.name, "rgba(255,255,255,0.06)", "#D1D5DB", "rgba(255,255,255,0.12)") for s in other_skills)
                sections.append(_block("offer.other", "#9CA3AF", chips))
            if vac.tools:
                chips = "".join(_chip(tl.name, "rgba(34,197,94,0.12)", "#86EFAC", "rgba(34,197,94,0.3)") for tl in vac.tools)
                sections.append(_block("offer.tools", "#4ADE80", chips))
            if vac.required_language_list:
                chips = "".join(
                    _chip(f"{l.language} · {l.level}", "rgba(59,130,246,0.14)", "#93C5FD", "rgba(59,130,246,0.35)")
                    for l in vac.required_language_list
                )
                sections.append(_block("offer.req_langs", "#60A5FA", chips))

            details_html = (
                "<details style='margin-top:14px;border-top:1px dashed rgba(255,255,255,0.1);padding-top:10px'>"
                "<summary style='cursor:pointer;list-style:none;display:flex;align-items:center;gap:6px;"
                "font-size:0.95rem;font-weight:700;letter-spacing:1px;text-transform:uppercase;"
                "color:#A100FF;outline:none'>"
                f"<span style='font-size:1rem'>▸</span> {t('offer.details')}"
                "</summary>"
                f"<div style='margin-top:8px'>{''.join(sections)}</div>"
                "</details>"
            )

        delay = (rank - 1) * 0.07

        _medal_border = {
            1: "border:2px solid #FFD700;box-shadow:0 0 22px rgba(255,215,0,0.25);",
            2: "border:2px solid #C0C0C0;box-shadow:0 0 18px rgba(192,192,192,0.2);",
            3: "border:2px solid #CD7F32;box-shadow:0 0 18px rgba(205,127,50,0.2);",
        }.get(rank, "border:1px solid rgba(255,255,255,0.09);")

        cards_html += (
            f"<div style='{_medal_border}border-radius:22px;"
            f"padding:22px 26px;margin-bottom:14px;background:#141414;"
            f"animation:cardIn .4s ease {delay:.2f}s both;'>"

            # top row
            f"<div style='display:flex;align-items:center;gap:22px;'>"

            # score bubble
            f"<div style='text-align:center;background:{score_bg};color:white;"
            f"border-radius:16px;padding:16px 20px;min-width:90px;flex-shrink:0;"
            f"box-shadow:0 6px 24px rgba(0,0,0,0.4);'>"
            f"<div style='font-size:2.6rem;font-weight:900;line-height:1'>{score}</div>"
            f"<div style='font-size:0.72rem;opacity:0.9;font-weight:800;letter-spacing:2px;margin-top:3px'>% MATCH</div>"
            f"</div>"

            # title block
            f"<div style='flex:1;min-width:0;'>"
            f"<div style='font-size:0.85rem;color:#6B7280;font-weight:600;letter-spacing:.5px;margin-bottom:4px'>"
            f"{rank_label}"
            f"</div>"
            f"<div style='font-size:1.45rem;font-weight:900;color:white;line-height:1.2;"
            f"white-space:nowrap;overflow:hidden;text-overflow:ellipsis;'>"
            f"{entry.role}"
            f"</div>"
            f"<div style='font-size:1rem;color:#A100FF;font-weight:700;margin-top:5px'>"
            f"{entry.sector}"
            f"</div>"
            f"</div>"
            # meta pill on the right
            + (f"<div style='flex-shrink:0;display:flex;flex-direction:column;align-items:flex-end;gap:6px;'>"
            f"<div style='background:#1F1F1F;border:1px solid rgba(255,255,255,0.1);"
            f"border-radius:12px;padding:10px 18px;text-align:center;'>"
            f"<div style='font-size:1rem;font-weight:700;color:white;white-space:nowrap;'>{meta}</div>"
            f"</div>"
            f"</div>" if meta else "<div></div>")
            + f"</div>"

            # score bar
            f"<div style='margin:16px 0 12px 0;background:rgba(255,255,255,0.05);"
            f"border-radius:4px;height:4px;overflow:hidden;'>"
            f"<div style='width:{score}%;height:100%;background:{bar_color};"
            f"border-radius:4px;'></div>"
            f"</div>"

            # signals row
            f"<div style='display:flex;gap:8px;flex-wrap:wrap'>{signals}</div>"
            f"{flags_html}"
            f"{details_html}"
            f"</div>"
        )

    st.markdown(
        f"<div style='max-height:65vh;overflow-y:auto;padding-right:6px'>{cards_html}</div>",
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
    font-size: 0.95rem !important;
    letter-spacing: 0.2px !important;
    transition: opacity 0.2s !important;
    padding: 0.45rem 1rem !important;
}
.stButton > button:hover { opacity: 0.82 !important; color: white !important; }
.stButton > button p,
.stButton > button span,
.stButton > button div {
    font-size: 0.95rem !important;
    color: white !important;
}

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
    font-weight: 700 !important;
    font-size: 1rem !important;
    color: #9CA3AF !important;
    padding: 9px 20px !important;
}
[data-testid="stTabs"] [data-baseweb="tab"] p,
[data-testid="stTabs"] [data-baseweb="tab"] span,
[data-testid="stTabs"] [data-baseweb="tab"] div {
    font-size: 1rem !important;
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

for _k, _v in [("selected", None), ("dropdown_v", 0), ("detective_knowledge", {}), ("ranking_requested", False), ("advisor_history", []), ("chat_fullscreen", False)]:
    if _k not in st.session_state:
        st.session_state[_k] = _v

init_lang()
examples = list_example_pdfs()

# ─── Main content ─────────────────────────────────────────────────────

selection = st.session_state.selected

if selection is None:
    # ── Language switcher (top-right) ────────────────────────────────
    _, _lc = st.columns([6, 1])
    with _lc:
        render_lang_switcher()

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
        f"{t('hero.tagline')}</p>"
        "</div>"
        "<br>"
        f"<h2 style='font-size:3.2rem;font-weight:900;"
        f"letter-spacing:-1px;line-height:1.15;margin:0;color:white;'>"
        f"{t('hero.headline')}"
        "</h2>"
        "</div>",
        unsafe_allow_html=True,
    )

    # ── Linear ticker with separator ─────────────────────────────────
    _TICKER_DATA = [
        ("📄", "#FF8C42", "Ada Lovelace",       t("ticker.ada")),
        ("⚖️", "#60A5FA", "Marie Curie",         t("ticker.marie")),
        ("🧠", "#34D399", "Alan Turing",         t("ticker.alan")),
        ("🔍", "#FBBF24", "Hedy Lamarr",         t("ticker.hedy")),
        ("🥇", "#F87171", "Serena Williams",     t("ticker.serena")),
        ("💡", "#C084FC", "Steve Jobs",          t("ticker.steve")),
        ("🏆", "#FCD34D", "Johannes Gutenberg",  t("ticker.johannes")),
    ]

    _separator = (
        "<div style='display:inline-flex;align-items:center;gap:14px;"
        "padding:0 40px;flex-shrink:0;'>"
        f"<span style='font-size:1.3rem;font-weight:800;letter-spacing:3px;"
        f"text-transform:uppercase;color:white;white-space:nowrap;'>{t('ticker.label')}</span>"
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
            f"{t('landing.decoded')}"
            "</h2>"
            f"<p style='color:rgba(255,255,255,0.65);font-size:1.25rem;font-weight:400;"
            f"line-height:1.6;margin:0 0 20px 0;'>{t('landing.desc')}</p>"
            f"<p style='font-size:1.3rem;font-weight:700;letter-spacing:1.5px;"
            f"text-transform:uppercase;color:#A100FF;margin:0 0 10px 0;'>{t('landing.extract_label')}</p>"
            f"<div style='color:#9CA3AF;font-size:1.5rem;line-height:2.1;font-weight:500;margin:0 0 22px 0;'>"
            f"✦ &nbsp;{t('landing.extract.skills')}<br>"
            f"✦ &nbsp;{t('landing.extract.edu')}<br>"
            f"✦ &nbsp;{t('landing.extract.langs')}"
            "</div>"
            "<div style='background:rgba(161,0,255,0.08);border:1px solid rgba(161,0,255,0.25);"
            "border-left:3px solid #A100FF;border-radius:12px;padding:14px 18px;'>"
            f"<p style='font-size:1.3rem;font-weight:800;letter-spacing:1px;"
            f"text-transform:uppercase;margin:0 0 8px 0;color:#A100FF;'>{t('assessor.title')}</p>"
            f"<p style='color:rgba(255,255,255,0.8);font-size:1.2rem;line-height:1.6;margin:0;'>"
            f"{t('landing.assessor_desc')}"
            "</p>"
            "</div>",
            unsafe_allow_html=True,
        )

    with cards_col:
        with st.container(border=True):
            st.markdown(
                f"<h3 style='font-size:2.4rem;font-weight:900;color:white;margin:8px 0 12px 0;'>"
                f"{t('upload.title')}</h3>"
                f"<p style='color:#9CA3AF;font-size:1.25rem;margin:0 0 18px 0;line-height:1.6;'>"
                f"{t('upload.desc')}</p>",
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
                st.success(f"✅ {uploaded.name} — {t('upload.ready')}")
                if st.button(t("upload.btn"), use_container_width=True, key="btn_process_upload"):
                    st.session_state.selected = ("upload", stem)
                    st.session_state.ranking_requested = True
                    st.rerun()

        st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

        with st.container(border=True):
            st.markdown(
                f"<h3 style='font-size:2.4rem;font-weight:900;color:white;margin:8px 0 12px 0;'>"
                f"{t('sample.title')}</h3>"
                f"<p style='color:#9CA3AF;font-size:1.25rem;margin:0 0 18px 0;line-height:1.6;'>"
                f"{t('sample.desc')}</p>"
                f"<p style='font-size:1rem;font-weight:700;letter-spacing:1px;"
                f"text-transform:uppercase;color:#A100FF;margin:0 0 10px 0;'>"
                f"{t('sample.profiles')}</p>",
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
                    if st.button(t("upload.btn"), use_container_width=True, key="btn_show_example"):
                        st.session_state.selected = ("example", label_to_nn[chosen_label])
                        st.session_state.ranking_requested = True
                        st.rerun()
            else:
                st.info(t("upload.no_cvs"))

    # ── Stats grid (below uploads) ────────────────────────────────────
    _STATS = [
        ("1,000", t("stat.vacancies"), ""),
        ("7",     t("stat.agents"),    "Ada &middot; Marie &middot; Alan &middot; Hedy<br>Serena &middot; Steve &middot; Johannes"),
        ("0",     t("stat.keywords"),  t("stat.keywords_sub")),
        ("100%",  t("stat.local"),     ""),
        ("4",    t("stat.axes"),  t("stat.axes_sub")),
        ("<30s", t("stat.speed"), ""),
    ]
    _stat_cells = "".join(
        f"<div style='background:#0D0D0D;padding:36px 20px;text-align:center;'>"
        f"<div style='font-size:3.8rem;font-weight:900;line-height:1;margin-bottom:12px;"
        f"background:linear-gradient(90deg,#ffffff 0%,#A100FF 100%);"
        f"-webkit-background-clip:text;-webkit-text-fill-color:transparent;"
        f"background-clip:text;'>{number}</div>"
        f"<div style='font-size:1rem;font-weight:700;letter-spacing:1.5px;"
        f"text-transform:uppercase;color:#6B7280;margin-bottom:{'10px' if sub else '0'};'>{label}</div>"
        + (f"<div style='font-size:1.05rem;color:#6B7280;line-height:1.8;margin-top:10px;font-weight:500;'>{sub}</div>" if sub else "")
        + f"</div>"
        for number, label, sub in _STATS
    )
    st.markdown(
        "<div style='display:grid;grid-template-columns:repeat(6,1fr);"
        "gap:1px;background:rgba(255,255,255,0.07);border-radius:20px;"
        "overflow:hidden;margin-top:40px;'>"
        + _stat_cells + "</div>",
        unsafe_allow_html=True,
    )

else:
    # ── DETAIL VIEW ───────────────────────────────────────────────────

    # Same hero header as landing
    st.markdown(
        "<div style='text-align:center;padding:0 0 20px 0;'>"
        "<div style='display:inline-flex;align-items:center;gap:24px;margin-bottom:14px;'>"
        "<h1 style='font-size:5rem;font-weight:900;letter-spacing:-3px;line-height:1;margin:0;"
        "background:linear-gradient(90deg,#ffffff 0%,#A100FF 100%);"
        "-webkit-background-clip:text;-webkit-text-fill-color:transparent;"
        "background-clip:text;'>SmartCV</h1>"
        f"<p style='color:rgba(255,255,255,0.55);font-size:1.8rem;font-weight:600;"
        f"letter-spacing:10px;text-transform:uppercase;margin:0;line-height:1;'>"
        f"{t('hero.tagline')}</p>"
        "</div>"
        "<br>"
        f"<h2 style='font-size:3.2rem;font-weight:900;"
        f"letter-spacing:-1px;line-height:1.15;margin:0;color:white;'>"
        f"{t('hero.headline')}"
        "</h2>"
        "</div>",
        unsafe_allow_html=True,
    )

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
        entries: list[PodiumEntry] = []

        if st.session_state.ranking_requested:
            _loader = st.empty()
            _loader.markdown(_epic_loader_html(), unsafe_allow_html=True)
            try:
                entries, profile_from_graph = compute_ranking(
                    str(pdf_path), candidate=profile
                )
                if profile is None:
                    profile = profile_from_graph
                    save_profile(profile, str(cache))
            except Exception as e:
                msg = str(e).lower()
                if any(tok in msg for tok in ("connect", "refus", "ollama", "11434")):
                    st.error(t("err.ollama"))
                else:
                    st.error(t("err.cv", err=e))
            finally:
                _loader.empty()

        # Top bar: name + lang switcher + back button
        _, _lc2 = st.columns([6, 1])
        with _lc2:
            render_lang_switcher()
        top_l, top_r = st.columns([5, 1])
        with top_l:
            if profile:
                st.markdown(
                    f"<h2 style='margin:0;font-size:1.55rem;font-weight:800;"
                    f"color:white;line-height:1.1'>{profile.name}</h2>",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f"<h2 style='margin:0;font-size:1.4rem;font-weight:800;color:white'>"
                    f"{pdf_path.name}</h2>",
                    unsafe_allow_html=True,
                )
        with top_r:
            if st.button(t("detail.change_cv"), use_container_width=True):
                st.session_state.selected = None
                st.session_state.ranking_requested = False
                st.session_state.advisor_history = []
                st.session_state.chat_fullscreen = False
                st.session_state.dropdown_v += 1
                st.rerun()

        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

        # ── Prepare assessor context once ────────────────────────────────
        _assessor_available = bool(profile)  # show even with 0 matches
        if _assessor_available:
            from chat.advisor import build_context, advisor_respond
            detective_knowledge = st.session_state.get("detective_knowledge", {})
            _system_prompt = build_context(profile, entries, detective_knowledge)

        # ── FULL-SCREEN CHAT MODE ─────────────────────────────────────────
        if st.session_state.get("chat_fullscreen") and _assessor_available:
            back_col, title_col = st.columns([1, 5])
            with back_col:
                if st.button(t("assessor.back"), use_container_width=True):
                    st.session_state.chat_fullscreen = False
                    st.rerun()
            with title_col:
                st.markdown(
                    f"<p style='font-size:1.5rem;font-weight:800;letter-spacing:1px;"
                    f"text-transform:uppercase;color:#A100FF;margin:6px 0 0 0;'>"
                    f"{t('assessor.fullscreen')}</p>",
                    unsafe_allow_html=True,
                )

            for msg in st.session_state.advisor_history:
                with st.chat_message(msg["role"]):
                    st.write(msg["content"])

            if user_input := st.chat_input(t("assessor.fs_placeholder"), key="advisor_fs_input"):
                st.session_state.advisor_history.append({"role": "user", "content": user_input})
                with st.chat_message("user"):
                    st.write(user_input)
                with st.chat_message("assistant"):
                    with st.spinner("Thinking…"):
                        try:
                            reply = advisor_respond(user_input, st.session_state.advisor_history[:-1], _system_prompt)
                        except Exception as e:
                            reply = t("assessor.error", err=e)
                    st.write(reply)
                st.session_state.advisor_history.append({"role": "assistant", "content": reply})

        else:
            # ── NORMAL TWO-COLUMN LAYOUT ──────────────────────────────────
            left_col, right_col = st.columns([1, 1], gap="large")

            with left_col:
                tab_pdf, tab_data = st.tabs([t("detail.tab_pdf"), t("detail.tab_profile")])
                with tab_pdf:
                    render_pdf(pdf_path, height=520)
                with tab_data:
                    if profile:
                        render_profile(profile)
                    else:
                        st.info(t("detail.no_profile"))

                # ── SmartCV Assessor (compact, below PDF) ─────────────────
                if _assessor_available:
                    hdr_l, hdr_r = st.columns([3, 1])
                    with hdr_l:
                        st.markdown(
                            f"<div style='margin-top:28px;margin-bottom:10px;'>"
                            f"<p style='font-size:1.6rem;font-weight:800;letter-spacing:1px;"
                            f"text-transform:uppercase;margin:0 0 6px 0;color:#A100FF;'>"
                            f"{t('assessor.title')}</p>"
                            f"<p style='color:#9CA3AF;font-size:1rem;margin:0 0 12px 0;line-height:1.5;'>"
                            f"{t('assessor.desc')}</p>"
                            "</div>",
                            unsafe_allow_html=True,
                        )
                    with hdr_r:
                        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
                        if st.button(t("assessor.expand"), use_container_width=True, key="btn_fullscreen"):
                            st.session_state.chat_fullscreen = True
                            st.rerun()

                    for msg in st.session_state.advisor_history:
                        with st.chat_message(msg["role"]):
                            st.write(msg["content"])

                    if user_input := st.chat_input(t("assessor.placeholder"), key="advisor_input"):
                        st.session_state.advisor_history.append({"role": "user", "content": user_input})
                        with st.chat_message("user"):
                            st.write(user_input)
                        with st.chat_message("assistant"):
                            with st.spinner("Thinking…"):
                                try:
                                    reply = advisor_respond(user_input, st.session_state.advisor_history[:-1], _system_prompt)
                                except Exception as e:
                                    reply = t("assessor.error", err=e)
                            st.write(reply)
                        st.session_state.advisor_history.append({"role": "assistant", "content": reply})

            with right_col:
                render_ranking(entries)
