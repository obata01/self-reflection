"""LangChain Embeddingsモデルのラッパー."""

from langchain_core.embeddings import Embeddings


class EmbeddingClient:
    """LangChainのEmbeddingsモデルをラップするクライアントクラス."""

    def __init__(self, model: Embeddings) -> None:
        """EmbeddingClientを初期化する.

        Args:
            model: LangChainのEmbeddingsモデル
        """
        self.model = model

    def embed_query(self, text: str) -> list[float]:
        """クエリテキストのembeddingを生成する.

        Args:
            text: クエリテキスト

        Returns:
            embeddingベクトル
        """
        return self.model.embed_query(text)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """複数ドキュメントのembeddingを生成する.

        Args:
            texts: ドキュメントテキストのリスト

        Returns:
            embeddingベクトルのリスト
        """
        return self.model.embed_documents(texts)
