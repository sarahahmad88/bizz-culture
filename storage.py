"""Session history plus portable export. No shared database or pretend login."""
import json


def save_completed(history, attempt):
    if attempt["status"] != "completed":
        raise ValueError("Only completed attempts belong in scored history.")
    # Deep-copy to avoid edits to the active attempt mutating history.
    record = json.loads(json.dumps(attempt))
    return [record] + [x for x in history if x["id"] != record["id"]]


def export_data(history, include_transcript=True):
    records = json.loads(json.dumps(history))
    if not include_transcript:
        for record in records:
            record["turns"] = []
            if record.get("result"):
                record["result"]["responses"] = []
            record.pop("raw_evaluation", None)
    return json.dumps({"format": "culture-coach-1", "attempts": records}, ensure_ascii=False, indent=2)
