"""JCommonsenseQA タスク読み込み・提供."""

import json
import logging
from pathlib import Path

from src.components.dataset_loader.models import QuestionRecord

logger = logging.getLogger(__name__)


class TaskLoader:
    """保存済みJSONLファイルからQuestionRecordを読み込み、提供する.

    Attributes:
        data_dir: データセット保存先ディレクトリ
    """

    def __init__(self, data_dir: str = "data/datasets/jcommonsenseqa") -> None:
        """TaskLoaderを初期化する.

        Args:
            data_dir: データセット保存先ディレクトリパス
        """
        self.data_dir = Path(data_dir)

    def load(self, split: str) -> list[QuestionRecord]:
        """指定splitのJSONLファイルからQuestionRecordリストを読み込む.

        Args:
            split: データセットのsplit名（train or validation）

        Returns:
            QuestionRecordのリスト

        Raises:
            FileNotFoundError: 指定されたsplitのファイルが存在しない場合
        """
        file_path = self.data_dir / f"{split}.jsonl"

        if not file_path.exists():
            msg = f"Split file not found: {file_path}"
            logger.error(msg)
            raise FileNotFoundError(msg)

        records = []
        with file_path.open("r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, start=1):
                try:
                    data = json.loads(line)
                    record = QuestionRecord(**data)
                    records.append(record)
                except (json.JSONDecodeError, ValueError) as e:
                    msg = f"Failed to parse line {line_num} in {file_path}: {e}"
                    logger.error(msg)
                    raise ValueError(msg) from e

        logger.info(f"Loaded {len(records)} records from {split} split")
        return records

    def evaluate(self, record: QuestionRecord, answer: str) -> bool:
        """Generatorの回答とlabelを比較して正誤判定.

        Args:
            record: QuestionRecord
            answer: Generatorの回答

        Returns:
            正解の場合True、不正解の場合False
        """
        return answer == record.correct_answer
