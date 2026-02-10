"""自己反省システムの動作確認スクリプト."""

import os

from src.application.workflows.reflection_workflow import ReflectionWorkflow
from src.common.config.settings import load_config
from src.common.di.container import Container
from src.common.lib.logging import getLogger
from src.components.hybrid_search.models import SearchQuery
from src.components.hybrid_search.search import HybridSearch
from src.components.llm_client.client import LLMClient
from src.components.playbook_store.models import Bullet, Playbook
from src.components.playbook_store.store import PlaybookStore

logger = getLogger(__name__)

TEST_DATASET = "test_dataset"


def _create_sample_playbook() -> Playbook:
    """サンプルPlaybookを作成する."""
    return Playbook(
        bullets=[
            Bullet(
                id="test-001",
                section="strategies_and_hard_rules",
                content="時間に敏感なトランザクションでは、現在時刻を基準に日時範囲を指定する",
                searchable_text="時間 トランザクション 現在時刻 日時範囲",
                keywords=["datetime", "range", "transaction"],
                helpful=5,
                harmful=0,
                source_trajectory="test_trajectory",
            ),
            Bullet(
                id="test-002",
                section="error_recovery",
                content="API呼び出しが失敗した場合、リトライ前に待機時間を設ける",
                searchable_text="API 失敗 リトライ 待機時間",
                keywords=["api", "retry", "error"],
                helpful=3,
                harmful=1,
                source_trajectory="test_trajectory",
            ),
        ]
    )


def _verify_playbook_store(playbook_store: PlaybookStore) -> Playbook:
    """PlaybookStoreの保存・読み込みを検証する."""
    logger.info("3. サンプルPlaybookの作成と保存...")
    sample_playbook = _create_sample_playbook()
    playbook_store.save(TEST_DATASET, sample_playbook)
    logger.info("   サンプルPlaybookを保存しました ✓")

    logger.info("4. Playbookの読み込み...")
    loaded_playbook = playbook_store.load(TEST_DATASET)
    logger.info("   Bullets数: %d ✓", len(loaded_playbook.bullets))
    return loaded_playbook


def _verify_hybrid_search(
    hybrid_search: HybridSearch, playbook: Playbook
) -> None:
    """ハイブリッド検索を検証する."""
    logger.info("5. ハイブリッド検索のテスト...")
    query = SearchQuery(query_text="API エラー処理", top_k=5)
    results = hybrid_search.search(query, playbook)
    logger.info("   検索結果: %d件 ✓", len(results))
    for i, result in enumerate(results, 1):
        logger.info(
            "   [%d] %s (combined: %.3f, vector: %.3f, bm25: %.3f)",
            i,
            result.bullet.id,
            result.combined_score,
            result.vector_score,
            result.bm25_score,
        )


def _verify_llm_client(llm_client: LLMClient) -> None:
    """LLMClientを検証する."""
    logger.info("6. LLMClientのテスト...")
    try:
        response = llm_client.invoke_with_template(
            "次の質問に簡潔に答えてください: {question}",
            {"question": "自己反省システムとは何ですか？"},
        )
        logger.info("   LLM応答（最初の100文字）: %s... ✓", response[:100])
    except Exception:
        logger.exception("   LLMリクエストエラー")


def _verify_workflow(
    playbook_store: PlaybookStore,
    hybrid_search: HybridSearch,
    llm_client: LLMClient,
) -> None:
    """ワークフローの実行を検証する."""
    logger.info("7. ワークフローの実行...")
    workflow = ReflectionWorkflow(
        playbook_store=playbook_store,
        hybrid_search=hybrid_search,
        llm_client=llm_client,
    )
    graph = workflow.build()
    try:
        result = graph.invoke(
            {
                "query": "APIエラーの対処方法は？",
                "dataset": TEST_DATASET,
                "playbook": None,
                "search_results": [],
                "llm_response": None,
            }
        )
        logger.info("   検索結果: %d件", len(result["search_results"]))
        logger.info("   LLM応答（最初の100文字）: %s... ✓", result["llm_response"][:100])
    except Exception:
        logger.exception("   ワークフロー実行エラー")


def main() -> None:
    """動作確認のメイン処理."""
    logger.info("=== 自己反省システム基盤 動作確認 ===")

    if not os.getenv("OPENAI_API_KEY"):
        logger.warning("OPENAI_API_KEYが設定されていません")
        logger.warning("環境変数を設定してから実行してください")
        return

    config = load_config()
    container = Container()
    container.config.from_dict(config.model_dump())
    logger.info("1. DIコンテナの初期化... ✓")

    playbook_store = container.playbook_store()
    logger.info("2. PlaybookStoreの初期化... ✓")

    loaded_playbook = _verify_playbook_store(playbook_store)

    hybrid_search = container.hybrid_search()
    _verify_hybrid_search(hybrid_search, loaded_playbook)

    llm_client = container.llm_client()
    _verify_llm_client(llm_client)

    _verify_workflow(playbook_store, hybrid_search, llm_client)

    logger.info("=== すべての動作確認が完了しました ===")


if __name__ == "__main__":
    main()
