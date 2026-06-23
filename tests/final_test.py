"""End-to-end test: loads a pre-interpreted profile (skips PDF extraction)
and runs the full qualifier → linguist → detective → podium → visionary → publisher chain.
"""
import time

from src.agents.interpreter import load_profile
from src.data.load_vacancies import load as load_vacancies
from src.orchestrator.graph import (
    qualifier_node, linguist_node, detective_node,
    podium_node, visionary_node, publisher_node,
)
from src.config import MODEL

PROFILE_JSON = "data/processed/01_candidate.json"

start = time.time()
candidate = load_profile(PROFILE_JSON)
_, vacancies = load_vacancies()

print(f"Candidate: {candidate.name}")
print(f"Experience: {candidate.years_experience} yrs | Education: {candidate.education_level}")
print(f"Languages: {[(l.language, l.level) for l in candidate.languages]}")
print(f"Skills: {[s.name for s in candidate.skills[:5]]} ...")
print()

state = {
    "pdf_path":  PROFILE_JSON,
    "model":     MODEL,
    "candidate": candidate,
    "vacancies": vacancies,
}

# Qualifier
state.update(qualifier_node(state))
print(f"Qualifier pass: {state['qualifier_result']['pass']}")
kept = sum(1 for r in state["qualifier_result"]["by_offer"].values() if r["decision"] == "keep")
print(f"Kept {kept} / {len(vacancies)} vacancies")
print()

# Linguist
state.update(linguist_node(state))
grey_zone = state["linguist_result"].get("grey_zone", [])
print(f"Grey zone skills ({len(grey_zone)}): {grey_zone[:5]}")
print()

# Detective (only if grey zone)
if grey_zone:
    state.update(detective_node(state))
    det = state["detective_result"]
    print(f"Detective resolved: {det['summary']}")
    print()

# Podium
state.update(podium_node(state))
ranking = state["podium_result"]["ranking"]
print(f"Podium — top {len(ranking)} offers:")
for i, e in enumerate(ranking[:5], 1):
    print(f"  #{i} {e['role']} ({e['sector']}) — {e['score_match']}%")
print()

# Visionary
state.update(visionary_node(state))
vr = state["visionary_result"]
print(f"Best fit: {vr['best_fit_role']} ({vr['best_fit_score']}%)")
print(f"Top gaps: {[g['skill'] for g in vr['top_gaps'][:3]]}")
print(f"Strengths: {vr['strengths'][:3]}")
print(f"Coaching: {vr['coaching'][:300]}")
print()

# Publisher
state.update(publisher_node(state))
pub = state["publisher_result"]
print(f"Saved: run_id={pub['run_id']} | {pub['offers_ranked']} offers | db={pub['db_path']}")

print("Time taken: %.1f seconds" % (time.time() - start))
