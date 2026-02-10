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
        logger.info(f"Query: {query}")
        logger.info(f"Dataset: {dataset}")

        trajectory = generator.run(query, dataset)
        logger.info(f"Trajectory created with status: {trajectory.status}")

        # サンプルのground_truthとtest_report
        ground_truth = "富士山"
        test_report = "不正解: 生成された回答が正解と一致しない"

        logger.info("Getting ReflectorAgent...")
        reflector = container.reflector_agent()

        logger.info("Running ReflectorAgent...")
        logger.info(f"Ground Truth: {ground_truth}")
        logger.info(f"Test Report: {test_report}")

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
        logger.info(f"Insights ({len(reflection_result.insights)} items):")
        for i, insight in enumerate(reflection_result.insights, start=1):
            logger.info(f"\n[Insight {i}]")
            logger.info(f"  Key Insight: {insight.key_insight}")
            logger.info(f"  Reasoning: {insight.reasoning}")
            logger.info(f"  Error Identification: {insight.error_identification}")
            logger.info(f"  Root Cause Analysis: {insight.root_cause_analysis}")
            logger.info(f"  Correct Approach: {insight.correct_approach}")

        # BulletEvaluations表示
        logger.info(f"\nBullet Evaluations ({len(reflection_result.bullet_evaluations)} items):")
        for i, eval in enumerate(reflection_result.bullet_evaluations, start=1):
            logger.info(f"\n[Evaluation {i}]")
            logger.info(f"  Bullet ID: {eval.bullet_id}")
            logger.info(f"  Tag: {eval.tag}")
            logger.info(f"  Reason: {eval.reason}")

        logger.info(f"\nTrajectory Query: {reflection_result.trajectory_query}")
        logger.info(f"Trajectory Dataset: {reflection_result.trajectory_dataset}")
        logger.info(f"Iteration Count: {reflection_result.iteration_count}")
        logger.info("=" * 60)

    except Exception as e:
        logger.exception(f"Failed to run ReflectorAgent: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
