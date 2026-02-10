"""JCommonsenseQA データモデル定義."""

from pydantic import BaseModel, Field, field_validator


class QuestionRecord(BaseModel):
    """JCommonsenseQA の1件の問題を表すデータモデル.

    Attributes:
        q_id: 質問ID
        question: 質問文（NFKC正規化済み）
        choice0: 選択肢0（NFKC正規化済み）
        choice1: 選択肢1（NFKC正規化済み）
        choice2: 選択肢2（NFKC正規化済み）
        choice3: 選択肢3（NFKC正規化済み）
        choice4: 選択肢4（NFKC正規化済み）
        label: 正解選択肢のインデックス（0〜4）
    """

    q_id: str
    question: str
    choice0: str
    choice1: str
    choice2: str
    choice3: str
    choice4: str
    label: int = Field(ge=0, le=4)

    @field_validator("q_id", mode="before")
    @classmethod
    def _coerce_q_id_to_str(cls, v: object) -> str:
        return str(v)

    @property
    def correct_answer(self) -> str:
        """labelに対応するchoiceの値を返す.

        Returns:
            正解選択肢のテキスト
        """
        return getattr(self, f"choice{self.label}")

    def to_query(self) -> str:
        """Question + 選択肢をフォーマットしたクエリ文字列を返す.

        Returns:
            フォーマット済みクエリ文字列
        """
        choices = "\n".join([f"  {i}: {getattr(self, f'choice{i}')}" for i in range(5)])
        return f"質問: {self.question}\n選択肢:\n{choices}"
