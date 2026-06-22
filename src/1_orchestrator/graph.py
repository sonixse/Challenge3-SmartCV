from typing import TypedDict
from langgraph.graph import StateGraph, END
from src.schemas.candidate import CandidateProfile


class State(TypedDict):
    candidate:        CandidateProfile
    qualifier_result: dict   # pass/score/fail
    linguist_result:  dict   # match/grey zone/no match per vacancy
    detective_result: dict   # resolve grey zone skills
    podium_result:    dict   # candidates ranking
    visionary_result: dict   # coaching, gap analysis


# replace each with a real (State) once the corresponding agent is ready to plug in

def interpreter_node(_state: State) -> dict:  # src/agents/interpreter.py
    raise NotImplementedError

def qualifier_node(_state: State) -> dict:    # src/agents/3_qualifier.py
    raise NotImplementedError

def linguist_node(_state: State) -> dict:     # src/agents/4_linguist.py
    raise NotImplementedError

def detective_node(_state: State) -> dict:
    raise NotImplementedError

def podium_node(_state: State) -> dict:
    raise NotImplementedError

def visionary_node(_state: State) -> dict:
    raise NotImplementedError

def publisher_node(_state: State) -> dict:
    raise NotImplementedError


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

# compiled = graph.compile()  # uncomment once all node stubs are implemented
