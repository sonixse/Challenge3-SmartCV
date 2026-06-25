import re
import time
from pathlib import Path
from typing import TypedDict
from langgraph.graph import StateGraph, END
from src.schemas.candidate import CandidateProfile
from src.config import LINGUIST_TOP_K, PODIUM_TOP_N


def _log(msg: str) -> None:
    print(f"[graph] {msg}", flush=True)

# Education level mapping: canonical English to Qualifier's Catalan/Spanish labels
_EDU_MAP = {
    "No degree":  None,
    "Bachelor's": "Grau",
    "Master's":   "Master",
    "PhD":        "Doctorat",
}

# Language name normalization: non-English names → canonical English key
# (vacancies always use English names; CVs may use native-language names)
_LANG_NORM: dict[str, str] = {
    # Spanish
    "español": "spanish", "castellano": "spanish", "espanol": "spanish",
    # English
    "inglés": "english", "ingles": "english", "anglès": "english", "angles": "english",
    # French
    "français": "french", "frances": "french", "francés": "french", "frances": "french",
    # German
    "deutsch": "german", "alemán": "german", "aleman": "german", "alemany": "german",
    # Catalan
    "català": "catalan", "catala": "catalan",
    # Italian
    "italiano": "italian",
    # Portuguese
    "português": "portuguese", "portugues": "portuguese",
    # Chinese
    "中文": "chinese", "mandarin": "chinese", "mandarín": "chinese",
    # Arabic
    "عربي": "arabic", "árabe": "arabic", "arabe": "arabic",
    # Dutch
    "nederlands": "dutch", "holandés": "dutch",
}


def _norm_lang(name: str) -> str:
    """Normalize a language name to its canonical lowercase English form."""
    return _LANG_NORM.get(name.lower(), name.lower())


class State(TypedDict):
    # --- initial inputs (required when invoking the compiled graph) ---
    pdf_path:  str   # absolute path to the candidate's CV PDF
    model:     str   # Ollama model name, e.g. "llama3"

    # --- filled in by nodes ---
    candidate:        CandidateProfile
    vacancies:        list   # list[Vacancy], loaded once by interpreter_node
    qualifier_result: dict   # {"pass": bool, "by_offer": {offer_id_str: QualifierResult dict}}
    linguist_result:  dict   # {"by_offer": {offer_id_str: analyse_dict}, "grey_zone": [str]}
    detective_result: dict   # DetectiveResult.model_dump()
    podium_result:    dict   # {"ranking": [PodiumEntry dicts sorted by score_match desc]}
    visionary_result: dict   # VisionaryResult.model_dump()
    publisher_result: dict   # {"run_id": int, "candidate": str, "best_fit_role": str, ...}


def _prof_input(candidate: CandidateProfile) -> dict:
    """Convert CandidateProfile → Qualifier input dict."""
    return {
        "experiencia_anys": float(candidate.years_experience),
        "idiomes": {
            _norm_lang(lang.language): ("C2" if lang.level == "Native" else lang.level)
            for lang in candidate.languages
        },
        "formacio_nivell": _EDU_MAP.get(candidate.education_level),
    }


def _off_input(vac):
    return {
        "experiencia_min": int(vac.years_experience),
        "experiencia_max": int(vac.years_experience) + 7,
        "idioma_requerit": {
            r.language.lower(): ("C2" if r.level == "Native" else r.level)
            for r in vac.required_language_list
        },
        "formacio_min": _EDU_MAP.get(vac.highest_degree),
    }

# nodes

def _cache_path_for(pdf_path: Path, processed_dir: Path) -> Path:
    """Replicate the UI's naming convention so both layers share the disk cache.

    - data/uploads/<stem>.pdf  → data/processed/upload_<stem>_candidate.json
    - data/raw/<NN>_*.pdf      → data/processed/<NN>_candidate.json
    - anything else            → data/processed/<stem>_candidate.json
    """
    stem = pdf_path.stem
    if pdf_path.parent.name == "uploads":
        return processed_dir / f"upload_{stem}_candidate.json"
    m = re.match(r"(\d+)", pdf_path.name)
    if m:
        return processed_dir / f"{m.group(1).zfill(2)}_candidate.json"
    return processed_dir / f"{stem}_candidate.json"


def interpreter_node(state: State) -> dict:
    from src.agents.interpreter import interpret, load_profile, save_profile, DEFAULT_OUTPUT_DIR
    from src.data.load_vacancies import load as load_vacancies

    _, vacancies = load_vacancies()

    if state.get("candidate") is not None:
        _log(f"interpreter: SKIP — profile pre-loaded ({state['candidate'].name})")
        return {"vacancies": vacancies}

    t0 = time.time()
    pdf_path = Path(state["pdf_path"])
    _log(f"interpreter: START — pdf={state['pdf_path']}")

    cache_path = _cache_path_for(pdf_path, Path(DEFAULT_OUTPUT_DIR))
    profile = None
    if cache_path.exists():
        try:
            profile = load_profile(str(cache_path))
            _log(f"interpreter: loaded cached profile from {cache_path.name}")
        except Exception as e:
            _log(f"interpreter: cache load failed ({e}), will reparse")
            profile = None

    if profile is None:
        profile = interpret(state["pdf_path"], model=state["model"])
        try:
            save_profile(profile, str(cache_path))
        except Exception as e:
            _log(f"interpreter: warning — could not save cache: {e}")

    _log(f"interpreter: profile parsed ({len(profile.skills)} skills, {len(profile.languages)} langs)")
    _log(f"interpreter: DONE in {time.time()-t0:.1f}s — {len(vacancies)} vacancies loaded")
    return {"candidate": profile, "vacancies": vacancies}


def qualifier_node(state: State) -> dict:
    from src.agents.qualifier import qualify

    t0 = time.time()
    _log(f"qualifier: START — {len(state['vacancies'])} vacancies")
    prof = _prof_input(state["candidate"])
    by_offer = {}
    for vac in state["vacancies"]:
        result = qualify(prof, _off_input(vac))
        by_offer[str(vac.id)] = result.model_dump()

    n_keep = sum(1 for r in by_offer.values() if r["decision"] == "keep")
    has_any_keep = n_keep > 0
    _log(f"qualifier: DONE in {time.time()-t0:.2f}s — keep={n_keep}, eliminate={len(by_offer)-n_keep}")
    return {
        "qualifier_result": {
            "pass":     has_any_keep,
            "by_offer": by_offer,
        }
    }


def linguist_node(state: State) -> dict:
    from src.agents.linguist import analyse, retrieve_top_k

    t0 = time.time()
    candidate          = state["candidate"]
    qualifier_by_offer = state["qualifier_result"]["by_offer"]
    _log(f"linguist: START — top_k={LINGUIST_TOP_K}")

    # Step 1: ChromaDB coarse retrieval — restrict to top-K semantically relevant vacancies
    t_chroma = time.time()
    top_ids = set(retrieve_top_k(candidate, k=LINGUIST_TOP_K))
    _log(f"linguist: Chroma top-K retrieved in {time.time()-t_chroma:.2f}s — {len(top_ids)} ids")

    keep_ids = {vid for vid, r in qualifier_by_offer.items() if r.get("decision") == "keep"}
    filtered_ids = top_ids & keep_ids

    # If the semantic filter leaves too few candidates (ChromaDB top-K misses the kept offers),
    # fall back to analysing all kept vacancies without the ChromaDB filter.
    use_chroma_filter = len(filtered_ids) >= 5
    _log(f"linguist: chroma∩keep={len(filtered_ids)} — {'using filter' if use_chroma_filter else 'FALLBACK: analysing all keeps'}")

    by_offer: dict[str, dict] = {}
    grey_zone_seen: set[str] = set()
    all_grey_zone: list[str] = []

    n_analysed = 0
    t_analyse = time.time()
    for vac in state["vacancies"]:
        vid = str(vac.id)
        if qualifier_by_offer.get(vid, {}).get("decision") != "keep":
            continue
        if use_chroma_filter and vid not in top_ids:
            continue  # skip vacancies outside the semantic top-K only when filter is reliable
        ta = time.time()
        result = analyse(candidate, vac)
        n_analysed += 1
        if n_analysed % 5 == 0 or n_analysed <= 3:
            _log(f"linguist:   analysed {n_analysed} vacancies (last vid={vid} in {time.time()-ta:.2f}s)")
        by_offer[vid] = result
        for skill in result.get("grey_zone", []):
            if skill not in grey_zone_seen:
                grey_zone_seen.add(skill)
                all_grey_zone.append(skill)

    _log(
        f"linguist: DONE in {time.time()-t0:.2f}s — analysed={n_analysed}, "
        f"unique grey zones={len(all_grey_zone)}"
    )
    return {
        "linguist_result": {
            "by_offer":  by_offer,
            "grey_zone": all_grey_zone,
        }
    }


def detective_node(state: State) -> dict:
    from src.agents.detective import resolve

    t0 = time.time()
    linguist_result = state["linguist_result"]
    grey_zone_skills = linguist_result.get("grey_zone", [])
    _log(f"detective: START — {len(grey_zone_skills)} grey-zone skills to resolve")

    # aliases: vacancy skill for closest candidate skill (for context extraction)
    aliases: dict[str, str] = {}
    for ling in linguist_result["by_offer"].values():
        for entry in ling.get("skills", []):
            if entry.get("classification") == "GREY ZONE" and entry.get("best_match"):
                aliases.setdefault(entry["vacancy_skill"], entry["best_match"])

    det = resolve(grey_zone_skills, state["candidate"].raw_text,
                  model=state["model"], aliases=aliases)
    _log(
        f"detective: resolved in {time.time()-t0:.2f}s — "
        f"match={det.summary.get('resolved_to_match', 0)}, "
        f"no_match={det.summary.get('resolved_to_no_match', 0)}"
    )

    # Merge verdicts back into per-offer skill lists and rebuild match/no_match lists
    updated_by_offer: dict[str, dict] = {}
    for offer_id, ling in linguist_result["by_offer"].items():
        updated_skills = [
            {**e, "classification": det.verdicts[e["vacancy_skill"]].classification}
            if e["vacancy_skill"] in det.verdicts else e
            for e in ling.get("skills", [])
        ]
        updated_by_offer[offer_id] = {
            **ling,
            "skills":    updated_skills,
            "match":     [s["vacancy_skill"] for s in updated_skills if s["classification"] == "MATCH"],
            "grey_zone": [s["vacancy_skill"] for s in updated_skills if s["classification"] == "GREY ZONE"],
            "no_match":  [s["vacancy_skill"] for s in updated_skills if s["classification"] == "NO MATCH"],
        }

    return {
        "detective_result": det.model_dump(),
        "linguist_result": {
            **linguist_result,
            "by_offer":  updated_by_offer,
            "grey_zone": [],  # all resolved, podium never sees GREY ZONE
        },
    }


def podium_node(state: State) -> dict:
    from src.agents.podium import build_entry
    from src.agents.qualifier import QualifierResult

    t0 = time.time()
    _log("podium: START")
    qualifier_by_offer = state["qualifier_result"]["by_offer"]
    linguist_by_offer  = state["linguist_result"]["by_offer"]
    prof = _prof_input(state["candidate"])

    entries = []
    skipped_unanalysed = 0
    for vac in state["vacancies"]:
        vid = str(vac.id)
        q_dict = qualifier_by_offer.get(vid, {})
        if q_dict.get("decision") != "keep":
            continue
<<<<<<< HEAD
        ling = linguist_by_offer.get(vid)
        if not ling:
            continue  # not in Chroma top-K, no semantic analysis available
=======
        # Skip vacancies the Linguist never analysed (outside Chroma top-K):
        # building entries with score_semantic=0 added noise without affecting
        # the visible top-N.
        if vid not in linguist_by_offer:
            skipped_unanalysed += 1
            continue
        ling = linguist_by_offer[vid]
>>>>>>> refs/remotes/origin/main
        qres = QualifierResult.model_validate(q_dict)
        entry = build_entry(vac, ling, qres, prof, _off_input(vac))
        if entry is not None:
            entries.append(entry)

    entries.sort(key=lambda e: e.score_match, reverse=True)
    _log(
        f"podium: DONE in {time.time()-t0:.2f}s — {len(entries)} entries built, "
        f"skipped {skipped_unanalysed} unanalysed (kept by Qualifier but outside Linguist top-K), "
        f"top-{PODIUM_TOP_N} returned"
    )
    return {
        "podium_result": {
            "ranking": [e.model_dump() for e in entries[:PODIUM_TOP_N]]
        }
    }


def visionary_node(state: State) -> dict:
    from src.agents.visionary import analyse
    t0 = time.time()
    _log("visionary: START — 1 Ollama call (no timeout)")
    result = analyse(
        candidate_name=state["candidate"].name,
        podium_result=state["podium_result"],
        linguist_result=state["linguist_result"],
        model=state["model"],
    )
    _log(f"visionary: DONE in {time.time()-t0:.2f}s")
    return {"visionary_result": result.model_dump()}


def publisher_node(state: State) -> dict:
    from src.agents.publisher import publish
    t0 = time.time()
    _log("publisher: START")
    candidate = state["candidate"]
    result = publish(
        candidate_name=candidate.name,
        candidate_contact=candidate.contact,
        pdf_path=state["pdf_path"],
        model=state["model"],
        podium_result=state["podium_result"],
        visionary_result=state["visionary_result"],
    )
    _log(f"publisher: DONE in {time.time()-t0:.2f}s — run_id={result.get('run_id')}")
    return {"publisher_result": result}


# graph 

graph = StateGraph(State)

graph.add_node("interpreter", interpreter_node)
graph.add_node("qualifier",   qualifier_node)
graph.add_node("linguist",    linguist_node)
graph.add_node("detective",   detective_node)
graph.add_node("podium",      podium_node)
graph.add_node("visionary",   visionary_node)
graph.add_node("publisher",   publisher_node)

graph.set_entry_point("interpreter")
graph.add_edge("interpreter", "qualifier")
graph.add_conditional_edges(
    "qualifier",
    lambda s: "linguist" if s["qualifier_result"]["pass"] else END,
)
graph.add_conditional_edges(
    "linguist",
    lambda s: "detective" if s["linguist_result"].get("grey_zone") else "podium",
)
graph.add_edge("detective", "podium")
graph.add_edge("podium",    "visionary")
graph.add_edge("visionary", "publisher")
graph.add_edge("publisher", END)

compiled = graph.compile()
