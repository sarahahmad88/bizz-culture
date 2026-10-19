from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class Setup(StrictModel):
    my_culture: str = Field(min_length=1, max_length=60)
    other_culture: str = Field(min_length=1, max_length=60)
    template: Literal["deadline", "group_project"]
    level: Literal["Beginner", "Intermediate", "Advanced"]


class Scenario(StrictModel):
    brief: str = Field(min_length=15, max_length=1600)
    character: str = Field(min_length=3, max_length=180)
    opening: str = Field(min_length=5, max_length=900)


class Reply(StrictModel):
    message: str = Field(min_length=3, max_length=900)


class Rating(StrictModel):
    dimension: str
    score: int | None = Field(ge=0, le=5)
    evidence: str = Field(max_length=700)
    reason: str = Field(min_length=5, max_length=800)


class ResponseReview(StrictModel):
    turn: int = Field(ge=1, le=15)
    ratings: list[Rating]
    strength: str = Field(min_length=5, max_length=700)
    improvement: str = Field(min_length=5, max_length=700)
    alternative: str = Field(min_length=5, max_length=900)
    uncertainty: str = Field(max_length=500)


class Evaluation(StrictModel):
    responses: list[ResponseReview]
    summary: str = Field(min_length=5, max_length=1200)
    next_step: str = Field(min_length=5, max_length=700)
