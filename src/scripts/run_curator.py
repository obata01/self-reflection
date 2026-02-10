"""Curatorエージェント動作確認スクリプト."""

import sys

from dotenv import load_dotenv

from src.common.config.settings import load_config
from src.common.defs.insight import BulletEvaluation, Insight, ReflectionResult
from src.common.di.container import Container
from src.common.lib.logging import getLogger

logger = getLogger(__name__)


def setup() -> Container:
    """DIコンテナを初期化して返す."""
    load_dotenv()
    config = load_config()
    container = Container()
    container.config.from_dict(config.model_dump())
    return container


def create_dummy_reflection_result() -> ReflectionResult:
    """テスト用のダミーReflectionResultを生成する."""
    # ダミーのInsightを作成
    dummy_insight = Insight(
        reasoning="クエリに対して適切な知識を取得できなかった",
        error_identification="山の名前に関する知識が不足していた",
        root_cause_analysis="Playbookに日本の地理に関する基礎知識が不足している",
        correct_approach="日本の主要な山に関する知識を追加すべき",
        key_insight="基礎的な地理情報をPlaybookに追加する必要がある",
    )

    # ダミーのBulletEvaluationを作成
    dummy_evaluation = BulletEvaluation(
        bullet_id="dummy-bullet-001",
        tag="neutral",
        reason="この質問には関連性が低かった",
    )

    return ReflectionResult(
        insights=[dummy_insight],
        bullet_evaluations=[dummy_evaluation],
        trajectory_query="日本で一番高い山は何ですか？",
        trajectory_dataset="appworld",
        iteration_count=1,
    )


def main() -> None:
    """Curatorエージェントの動作確認を行う."""
    try:
        logger.info("Initializing container...")
        container = setup()

        # ダミーのReflectionResultを作成
        logger.info("Creating dummy ReflectionResult...")
        reflection_result = create_dummy_reflection_result()

        dataset = "appworld"

        logger.info("Getting CuratorAgent...")
        curator = container.curator_agent()

        logger.info("Running CuratorAgent...")
        logger.info("Dataset: %s", dataset)
        logger.info("Input Insights: %s items", len(reflection_result.insights))
        logger.info("Input BulletEvaluations: %s items", len(reflection_result.bullet_evaluations))

        curation_result = curator.run(
            reflection_result=reflection_result,
            dataset=dataset,
        )

        # 結果表示
        logger.info("=" * 60)
        logger.info("CurationResult")
        logger.info("=" * 60)

        # Deltas表示
        logger.info("Delta Context Items (%s items):", len(curation_result.deltas))
        for i, delta in enumerate(curation_result.deltas, start=1):
            logger.info("\n[Delta %s]", i)
            logger.info("  Type: %s", delta.type)
            logger.info("  Section: %s", delta.section)
            logger.info("  Content: %s", delta.content)
            logger.info("  Reasoning: %s", delta.reasoning)
            if delta.bullet_id:
                logger.info("  Bullet ID: %s", delta.bullet_id)

        logger.info("\nBullets Before: %s", curation_result.bullets_before)
        logger.info("Bullets After: %s", curation_result.bullets_after)
        logger.info("Summary: %s", curation_result.summary)
        logger.info("=" * 60)

    except Exception:
        logger.exception("Failed to run CuratorAgent")
        sys.exit(1)


if __name__ == "__main__":
    main()
