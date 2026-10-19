"""Validate evidence and calculate scores. No AI arithmetic or keyword scoring."""
from statistics import mean
from schemas import Evaluation


def normalized_score(values):
    valid = [value for value in values if value is not None]
    if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not 0 <= v <= 5 for v in valid):
        raise ValueError("Ratings must be 0–5 or null.")
    return round(100 * sum(valid) / (5 * len(valid))) if valid else None


def score_evaluation(attempt, evaluation: Evaluation):
    turns = attempt["turns"]
    ids = [r.turn for r in evaluation.responses]
    if sorted(ids) != list(range(1, len(turns) + 1)):
        raise ValueError("Evaluation must include every learner response exactly once.")
    relevant = attempt["knowledge"]["template"]["relevant"]
    results = []
    for review in sorted(evaluation.responses, key=lambda r: r.turn):
        rating_ids = [r.dimension for r in review.ratings]
        if sorted(rating_ids) != sorted(relevant):
            raise ValueError("Each response must include exactly the scenario-relevant dimensions.")
        text = turns[review.turn - 1]["user"]
        for rating in review.ratings:
            if rating.score is not None and (not rating.evidence.strip() or rating.evidence not in text):
                raise ValueError("Scored ratings must quote exact evidence from the learner response.")
        results.append({**review.model_dump(),
                        "score": normalized_score([r.score for r in review.ratings]),
                        "coverage": sum(r.score is not None for r in review.ratings) / len(relevant)})
    # Equal dimension weighting. Nulls are excluded; zero is retained.
    dimensions = {}
    for dim in relevant:
        values = [r["score"] for row in results for r in row["ratings"]
                  if r["dimension"] == dim and r["score"] is not None]
        dimensions[dim] = mean(values) if values else None
    return {"responses": results, "dimensions": dimensions,
            "overall": normalized_score(list(dimensions.values())),
            "summary": evaluation.summary, "next_step": evaluation.next_step,
            "coverage": mean([r["coverage"] for r in results]) if results else 0}
