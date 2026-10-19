"""Deterministic retrieval tools: zero LLM calls, zero network requests."""
import copy
import json
from pathlib import Path

_DATA = json.loads((Path(__file__).parent / "data" / "knowledge.json").read_text())


def retrieve_context(setup):
    template = copy.deepcopy(_DATA["templates"][setup.template])
    return {"template": template, "dimensions": copy.deepcopy(_DATA["dimensions"]),
            "anchors": copy.deepcopy(_DATA["anchors"]), "version": _DATA["version"],
            "review_status": _DATA["review_status"], "source": _DATA["source"],
            "country_scores": None,
            "note": "No country scores are supplied. Evaluate this fictional context, never nationality."}


def get_rubric(attempt):
    """Read the snapshot frozen at setup, not potentially changed external rules."""
    return copy.deepcopy(attempt["knowledge"])


def get_attempt_context(attempt):
    return {"setup": copy.deepcopy(attempt["setup"]),
            "scenario": copy.deepcopy(attempt["scenario"]),
            "turns": copy.deepcopy(attempt["turns"])}


def all_knowledge():
    return copy.deepcopy(_DATA)
