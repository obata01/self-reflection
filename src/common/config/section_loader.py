"""YAML設定ファイルからセクション定義を読み込むローダー."""

from pathlib import Path

import yaml
from pydantic import BaseModel


class SectionDefinition(BaseModel):
    """セクション定義モデル."""

    name: str
    description: str


class SectionLoader:
    """セクション定義を読み込むローダークラス."""

    def __init__(self, config_path: str = "config/sections.yaml") -> None:
        """SectionLoaderを初期化する.

        Args:
            config_path: セクション定義ファイルのパス
        """
        self.config_path = Path(config_path)

    def load(self, dataset: str) -> list[SectionDefinition]:
        """指定データセットのセクション定義を読み込む.

        Args:
            dataset: データセット名

        Returns:
            セクション定義のリスト
        """
        data = yaml.safe_load(self.config_path.read_text())
        sections = data.get(dataset, [])
        return [SectionDefinition(**s) for s in sections]
