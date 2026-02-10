"""Reflectorの分析結果を表すデータモデルの定義."""

from typing import Literal

from pydantic import BaseModel


class Insight(BaseModel):
    """Reflectorの分析結果を表すモデル."""

    reasoning: str
    error_identification: str
    root_cause_analysis: str
    correct_approach: str
    key_insight: str


class InsightsResponse(BaseModel):
    """LLMからのInsightリストを受け取るラッパーモデル."""

    insights: list[Insight]


class BulletEvaluation(BaseModel):
    """Bulletに対する評価タグを表すモデル."""

    bullet_id: str
    tag: Literal["helpful", "harmful", "neutral"]
    reason: str


class ReflectionResult(BaseModel):
    """Reflectorの出力全体を表すモデル."""

    insights: list[Insight]
    bullet_evaluations: list[BulletEvaluation]
    trajectory_query: str
    trajectory_dataset: str
    iteration_count: int = 1
