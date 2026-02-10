"""Generatorの推論過程を記録するTrajectoryモデルの定義."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class Trajectory(BaseModel):
    """Generatorの推論過程を記録するモデル."""

    query: str
    dataset: str
    generated_answer: str
    reasoning_steps: list[str]
    used_bullet_ids: list[str]
    status: Literal["success", "failure"]
    error_message: str | None = None
    created_at: datetime = Field(default_factory=datetime.now)
