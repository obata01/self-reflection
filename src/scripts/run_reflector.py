"""Reflectorエージェント動作確認スクリプト."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

from src.common.config.settings import load_config
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


def main() -> None:
    """Reflectorエージェントの動作確認を行う."""
    try:
        logger.info("Initializing container...")
        container = setup()

        logger.info("Getting GeneratorAgent...")
        generator = container.generator_agent()

        # サンプルクエリでTrajectoryを生成
        query = "日本で一番高い山は何ですか？"
        dataset = "appworld"

        logger.info("Running GeneratorAgent to create Trajectory...")
        logger.info("Query: %s", query)
        logger.info("Dataset: %s", dataset)

        trajectory = generator.run(query, dataset)
        logger.info("Trajectory created with status: %s", trajectory.status)

        # サンプルのground_truthとtest_report
        ground_truth = "富士山"
        test_report = "不正解: 生成された回答が正解と一致しない"

        logger.info("Getting ReflectorAgent...")
        reflector = container.reflector_agent()

        logger.info("Running ReflectorAgent...")
        logger.info("Ground Truth: %s", ground_truth)
        logger.info("Test Report: %s", test_report)

        reflection_result = reflector.run(
            trajectory=trajectory,
            ground_truth=ground_truth,
            test_report=test_report,
            dataset=dataset,
        )

        # 結果表示
        logger.info("=" * 60)
        logger.info("ReflectionResult")
        logger.info("=" * 60)

        # Insights表示
        logger.info("Insights (%s items):", len(reflection_result.insights))
        for i, insight in enumerate(reflection_result.insights, start=1):
            logger.info("\n[Insight %s]", i)
            logger.info("  Key Insight: %s", insight.key_insight)
            logger.info("  Reasoning: %s", insight.reasoning)
            logger.info("  Error Identification: %s", insight.error_identification)
            logger.info("  Root Cause Analysis: %s", insight.root_cause_analysis)
            logger.info("  Correct Approach: %s", insight.correct_approach)

        # BulletEvaluations表示
        logger.info("\nBullet Evaluations (%s items):", len(reflection_result.bullet_evaluations))
        for i, evaluation in enumerate(reflection_result.bullet_evaluations, start=1):
            logger.info("\n[Evaluation %s]", i)
            logger.info("  Bullet ID: %s", evaluation.bullet_id)
            logger.info("  Tag: %s", evaluation.tag)
            logger.info("  Reason: %s", evaluation.reason)

        logger.info("\nTrajectory Query: %s", reflection_result.trajectory_query)
        logger.info("Trajectory Dataset: %s", reflection_result.trajectory_dataset)
        logger.info("Iteration Count: %s", reflection_result.iteration_count)
        logger.info("=" * 60)

    except Exception:
        logger.exception("Failed to run ReflectorAgent")
        sys.exit(1)


if __name__ == "__main__":
    main()
