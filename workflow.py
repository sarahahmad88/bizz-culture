"""The learning loop, expressed as small testable state transitions."""
import copy
from datetime import datetime, timezone
from uuid import uuid4

from config import LEVELS, MAX_RESPONSE_CHARS
from knowledge import retrieve_context
from schemas import Setup
from scoring import score_evaluation


def new_attempt(setup: Setup, mode, scenario, knowledge=None, parent_id=None):
    return {"id": str(uuid4()), "parent_id": parent_id,
            "created": datetime.now(timezone.utc).isoformat(),
            "setup": setup.model_dump(), "mode": mode, "scenario": scenario.model_dump(),
            "knowledge": copy.deepcopy(knowledge or retrieve_context(setup)),
            "rounds": LEVELS[setup.level], "turns": [], "status": "ready", "result": None,
            "calls": 0, "request_log": []}


def prepare_response(attempt, text):
    if attempt["status"] not in ("ready", "conversing"):
        raise ValueError("This attempt is not accepting responses.")
    text = text.strip()
    if not text or len(text) > MAX_RESPONSE_CHARS:
        raise ValueError(f"Write 1–{MAX_RESPONSE_CHARS} characters.")
    if len(attempt["turns"]) >= attempt["rounds"]:
        raise ValueError("The conversation is already complete.")
    return text


def commit_response(attempt, text, reply):
    text = prepare_response(attempt, text)
    if len(attempt["turns"]) + 1 < attempt["rounds"] and not reply:
        raise ValueError("A conversation reply is required before committing this turn.")
    attempt["turns"].append({"turn": len(attempt["turns"]) + 1, "user": text, "ai": reply})
    attempt["status"] = "awaiting_evaluation" if len(attempt["turns"]) == attempt["rounds"] else "conversing"


def complete_attempt(attempt, evaluation):
    if attempt["status"] != "awaiting_evaluation":
        raise ValueError("Finish the configured rounds before requesting an evaluation.")
    result = score_evaluation(attempt, evaluation)
    attempt["result"] = result
    attempt["status"] = "completed"


def retry_attempt(attempt):
    from schemas import Scenario
    return new_attempt(Setup(**attempt["setup"]), attempt["mode"],
                       Scenario(**attempt["scenario"]), attempt["knowledge"], attempt["id"])
