"""JCommonsenseQA データセット取得・保存."""

import json
import logging
import unicodedata
from pathlib import Path

import pandas as pd

from src.components.dataset_loader.models import QuestionRecord

logger = logging.getLogger(__name__)


class DatasetLoader:
    """JCommonsenseQAデータセットをHugging Faceから取得し、ローカルに保存する.

    Attributes:
        output_dir: データセット保存先ディレクトリ
    """

    def __init__(self, output_dir: str = "data/datasets/jcommonsenseqa") -> None:
        """DatasetLoaderを初期化する.

        Args:
            output_dir: データセット保存先ディレクトリパス
        """
        self.output_dir = Path(output_dir)

    def fetch_and_save(self) -> dict[str, int]:
        """HFからデータ取得、NFKC正規化、JSONL保存.

        Returns:
            split名→件数のdict

        Raises:
            Exception: データ取得中にエラーが発生した場合
        """
        self.output_dir.mkdir(parents=True, exist_ok=True)

        results = {}
        for split in ["train", "validation"]:
            try:
                logger.info(f"Fetching {split} split from Hugging Face...")
                records = self._fetch_split(split)
                logger.info(f"Fetched {len(records)} records from {split} split")

                self._save_jsonl(records, split)
                results[split] = len(records)
                logger.info(f"Saved {split} split to {self.output_dir / f'{split}.jsonl'}")

            except Exception as e:
                logger.error(f"Failed to fetch {split} split: {e}")
                raise

        return results

    def _fetch_split(self, split: str) -> list[QuestionRecord]:
        """指定splitをHFから取得しQuestionRecordリストに変換.

        Args:
            split: データセットのsplit名（train or validation）

        Returns:
            QuestionRecordのリスト
        """
        url = f"https://huggingface.co/datasets/sbintuitions/JCommonsenseQA/resolve/refs%2Fconvert%2Fparquet/default/{split}/0000.parquet"
        df = pd.read_parquet(url)

        records = []
        for _, row in df.iterrows():
            record = QuestionRecord(
                q_id=str(row["q_id"]),
                question=self._normalize_nfkc(row["question"]),
                choice0=self._normalize_nfkc(row["choice0"]),
                choice1=self._normalize_nfkc(row["choice1"]),
                choice2=self._normalize_nfkc(row["choice2"]),
                choice3=self._normalize_nfkc(row["choice3"]),
                choice4=self._normalize_nfkc(row["choice4"]),
                label=int(row["label"]),
            )
            records.append(record)

        return records

    def _normalize_nfkc(self, text: str) -> str:
        """NFKC正規化を適用.

        Args:
            text: 正規化対象の文字列

        Returns:
            NFKC正規化済みの文字列
        """
        return unicodedata.normalize("NFKC", text)

    def _save_jsonl(self, records: list[QuestionRecord], split: str) -> None:
        """QuestionRecordリストをJSONLファイルに保存.

        Args:
            records: 保存するQuestionRecordのリスト
            split: split名（ファイル名に使用）
        """
        output_path = self.output_dir / f"{split}.jsonl"
        with output_path.open("w", encoding="utf-8") as f:
            for record in records:
                f.write(record.model_dump_json() + "\n")
