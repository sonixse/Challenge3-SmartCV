"""i18n module for SmartCV — language detection, translation lookup, switcher."""

from __future__ import annotations
import streamlit as st
from .translations import TRANSLATIONS

SUPPORTED = ["en", "es", "ca"]
DEFAULT   = "en"


def init_lang() -> None:
    """Initialise language for this session.
    Priority: session_state → URL ?lang=xx → English default.
    """
    if "lang" in st.session_state:
        return
    qp = st.query_params.get("lang", "")
    if qp in SUPPORTED:
        st.session_state["lang"] = qp
        return
    st.session_state["lang"] = DEFAULT


def get_lang() -> str:
    return st.session_state.get("lang", DEFAULT)


def set_lang(code: str) -> None:
    if code in SUPPORTED:
        st.session_state["lang"] = code
        st.query_params["lang"] = code


def t(key: str, **kwargs) -> str:
    """Return the translated string for the current language.
    Falls back to English when a key is missing.
    Supports named format args: t("ranking.caption", n=5, total=100)
    """
    lang = get_lang()
    text = (
        TRANSLATIONS.get(lang, {}).get(key)
        or TRANSLATIONS["en"].get(key)
        or key
    )
    if kwargs:
        try:
            text = text.format(**kwargs)
        except (KeyError, ValueError):
            pass
    return text


def render_lang_switcher() -> None:
    """Compact three-button language switcher: EN / ES / CA."""
    current = get_lang()
    c1, c2, c3 = st.columns(3)
    for col, code in zip([c1, c2, c3], SUPPORTED):
        label = code.upper()
        with col:
            if current == code:
                st.markdown(
                    f"<div style='text-align:center;padding:5px 0;"
                    f"background:#A100FF;border-radius:8px;font-size:0.82rem;"
                    f"font-weight:800;color:white;letter-spacing:1px;'>{label}</div>",
                    unsafe_allow_html=True,
                )
            else:
                if st.button(label, key=f"_lang_{code}", use_container_width=True):
                    set_lang(code)
                    st.rerun()
