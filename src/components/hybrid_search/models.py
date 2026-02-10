"""ハイブリッド検索用のモデル定義."""

from pydantic import BaseModel

from src.components.playbook_store.models import Bullet


class SearchQuery(BaseModel):
    """検索クエリを表すモデル."""

    query_text: str
    top_k: int = 10
    section_filter: list[str] | None = None
    min_confidence: float = 0.3


class SearchResult(BaseModel):
    """検索結果を表すモデル."""

    bullet: Bullet
    vector_score: float
    bm25_score: float
    combined_score: float
