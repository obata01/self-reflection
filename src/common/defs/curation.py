"""Curatorの出力を表すデータモデルの定義."""

from pydantic import BaseModel

from src.components.playbook_store.models import DeltaContextItem


class DeltasResponse(BaseModel):
    """LLMからのDeltaContextItemリストを受け取るラッパーモデル."""

    deltas: list[DeltaContextItem]


class CurationResult(BaseModel):
    """Curatorの出力全体を表すモデル."""

    deltas: list[DeltaContextItem]
    bullets_before: int
    bullets_after: int
    summary: str
