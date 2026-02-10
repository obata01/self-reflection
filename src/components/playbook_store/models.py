"""Playbookデータモデルの定義."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, computed_field


class Bullet(BaseModel):
    """個別の知識単位を表すモデル.

    Bulletはhelpful/harmfulカウンターによる信頼度スコアを持つ.
    """

    id: str
    section: str
    content: str
    searchable_text: str
    keywords: list[str] = Field(default_factory=list)
    helpful: int = 0
    harmful: int = 0
    source_trajectory: str = ""

    @computed_field
    @property
    def confidence_score(self) -> float:
        """helpful数とharmful数から信頼度スコアを算出する.

        Returns:
            信頼度スコア（0.0〜1.0）. カウンターが0の場合は0.5を返す.
        """
        total = self.helpful + self.harmful
        if total == 0:
            return 0.5
        return self.helpful / total


class PlaybookMetadata(BaseModel):
    """Playbookのメタデータを表すモデル."""

    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class Playbook(BaseModel):
    """知識ベース全体を表すモデル.

    Bulletのコンテナとしてデータセットごとに管理される.
    """

    metadata: PlaybookMetadata = Field(default_factory=PlaybookMetadata)
    bullets: list[Bullet] = Field(default_factory=list)


class DeltaContextItem(BaseModel):
    """Curatorが生成するPlaybookへの更新差分を表すモデル."""

    type: Literal["ADD", "UPDATE", "DELETE"]
    section: str
    bullet_id: str | None = None
    content: str
    reasoning: str
