"""Numpyベクトル近傍探索とBM25を組み合わせたハイブリッド検索エンジン."""

import numpy as np
from rank_bm25 import BM25Okapi

from src.components.hybrid_search.embedding_client import EmbeddingClient
from src.components.hybrid_search.models import SearchQuery, SearchResult
from src.components.playbook_store.models import Bullet, Playbook


class HybridSearch:
    """ハイブリッド検索エンジンクラス.

    Numpyベクトル近傍探索とBM25全文検索を組み合わせて検索する.
    """

    def __init__(self, embedding_client: EmbeddingClient, alpha: float = 0.5) -> None:
        """HybridSearchを初期化する.

        Args:
            embedding_client: embedding生成クライアント
            alpha: ベクトルスコアの重み（0〜1）
        """
        self.embedding_client = embedding_client
        self.alpha = alpha

    def search(self, query: SearchQuery, playbook: Playbook) -> list[SearchResult]:
        """ハイブリッド検索を実行する.

        Args:
            query: 検索クエリ
            playbook: 検索対象のPlaybook

        Returns:
            統合スコア降順のSearchResultリスト
        """
        if not playbook.bullets:
            return []

        candidates = self._filter_candidates(query, playbook.bullets)
        if not candidates:
            return []

        vector_scores = self._vector_search(query.query_text, candidates)
        bm25_scores = self._bm25_search(query.query_text, candidates)
        results = self._combine_scores(candidates, vector_scores, bm25_scores)

        results.sort(key=lambda r: r.combined_score, reverse=True)
        return results[: query.top_k]

    def _filter_candidates(self, query: SearchQuery, bullets: list[Bullet]) -> list[Bullet]:
        """セクションと信頼度スコアでBulletをフィルタリングする.

        Args:
            query: 検索クエリ
            bullets: フィルタリング対象のBulletリスト

        Returns:
            フィルタリング後のBulletリスト
        """
        candidates = bullets
        if query.section_filter:
            candidates = [b for b in candidates if b.section in query.section_filter]
        candidates = [b for b in candidates if b.confidence_score >= query.min_confidence]
        return candidates

    def _vector_search(self, query_text: str, candidates: list[Bullet]) -> list[float]:
        """ベクトル近傍探索を実行してスコアを計算する.

        Args:
            query_text: 検索クエリテキスト
            candidates: 検索対象のBulletリスト

        Returns:
            正規化されたベクトルスコアのリスト
        """
        query_embedding = np.array(self.embedding_client.embed_query(query_text))
        doc_embeddings = np.array(
            self.embedding_client.embed_documents([b.searchable_text for b in candidates])
        )

        norms = np.linalg.norm(doc_embeddings, axis=1) * np.linalg.norm(query_embedding)
        norms = np.where(norms == 0, 1, norms)
        scores = np.dot(doc_embeddings, query_embedding) / norms

        min_s, max_s = scores.min(), scores.max()
        if max_s > min_s:
            scores = (scores - min_s) / (max_s - min_s)
        else:
            scores = np.ones_like(scores) * 0.5

        return scores.tolist()

    def _bm25_search(self, query_text: str, candidates: list[Bullet]) -> list[float]:
        """BM25全文検索を実行してスコアを計算する.

        Args:
            query_text: 検索クエリテキスト
            candidates: 検索対象のBulletリスト

        Returns:
            正規化されたBM25スコアのリスト
        """
        corpus = [b.searchable_text.split() for b in candidates]
        bm25 = BM25Okapi(corpus)
        tokenized_query = query_text.split()
        scores = bm25.get_scores(tokenized_query)

        min_s, max_s = scores.min(), scores.max()
        if max_s > min_s:
            scores = (scores - min_s) / (max_s - min_s)
        else:
            scores = np.ones_like(scores) * 0.5

        return scores.tolist()

    def _combine_scores(
        self,
        candidates: list[Bullet],
        vector_scores: list[float],
        bm25_scores: list[float],
    ) -> list[SearchResult]:
        """ベクトルスコアとBM25スコアを統合する.

        Args:
            candidates: Bulletリスト
            vector_scores: ベクトルスコアリスト
            bm25_scores: BM25スコアリスト

        Returns:
            SearchResultのリスト
        """
        results = []
        for bullet, vs, bs in zip(candidates, vector_scores, bm25_scores):
            combined = self.alpha * vs + (1 - self.alpha) * bs
            results.append(
                SearchResult(
                    bullet=bullet,
                    vector_score=vs,
                    bm25_score=bs,
                    combined_score=combined,
                )
            )
        return results
