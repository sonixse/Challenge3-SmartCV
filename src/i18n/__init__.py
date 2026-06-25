"""i18n module for SmartCV — language detection, translation lookup, switcher."""

from __future__ import annotations
import streamlit as st
from .translations import TRANSLATIONS

SUPPORTED = ["en", "es", "ca", "ru", "it", "fr", "de"]
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


_LANG_LABELS = {
    "en": "EN · English",
    "es": "ES · Español",
    "ca": "CA · Català",
    "ru": "RU · Русский",
    "it": "IT · Italiano",
    "fr": "FR · Français",
    "de": "DE · Deutsch",
}


def render_lang_switcher() -> None:
    """Language dropdown selector."""
    current = get_lang()
    options = SUPPORTED
    labels  = [_LANG_LABELS.get(c, c.upper()) for c in options]
    idx     = options.index(current) if current in options else 0

    chosen = st.selectbox(
        "🌐",
        options=labels,
        index=idx,
        label_visibility="collapsed",
        key="_lang_select",
    )
    chosen_code = options[labels.index(chosen)]
    if chosen_code != current:
        set_lang(chosen_code)
        st.rerun()
