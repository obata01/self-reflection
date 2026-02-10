"""Playbookの永続化を担当するストア."""

import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from src.components.playbook_store.models import Playbook

JST = ZoneInfo("Asia/Tokyo")


class PlaybookStore:
    """PlaybookをJSON形式で永続化するストアクラス."""

    def __init__(self, data_dir: str = "data/playbooks") -> None:
        """PlaybookStoreを初期化する.

        Args:
            data_dir: Playbookファイルの保存ディレクトリ
        """
        self.data_dir = Path(data_dir)

    def load(self, dataset: str) -> Playbook:
        """指定データセットのPlaybookを読み込む.

        Args:
            dataset: データセット名

        Returns:
            Playbookオブジェクト. ファイルが存在しない場合は空のPlaybook.
        """
        path = self.data_dir / f"{dataset}.json"
        if not path.exists():
            return Playbook()
        data = json.loads(path.read_text())
        return Playbook.model_validate(data)

    def save(self, dataset: str, playbook: Playbook) -> None:
        """PlaybookをJSONファイルに保存する.

        Args:
            dataset: データセット名
            playbook: 保存するPlaybook
        """
        self.data_dir.mkdir(parents=True, exist_ok=True)
        path = self.data_dir / f"{dataset}.json"
        playbook.metadata.updated_at = datetime.now(tz=JST)
        path.write_text(playbook.model_dump_json(indent=2))
