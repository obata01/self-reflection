"""Generatorエージェント動作確認スクリプト."""

import sys

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
    """Generatorエージェントの動作確認を行う."""
    try:
        logger.info("Initializing container...")
        container = setup()

        logger.info("Getting GeneratorAgent...")
        generator = container.generator_agent()

        # サンプルクエリ
        query = "日本で一番高い山は何ですか？"
        dataset = "appworld"

        logger.info("Running GeneratorAgent...")
        logger.info(f"Query: {query}")
        logger.info(f"Dataset: {dataset}")

        trajectory = generator.run(query, dataset)

        # 結果表示
        logger.info("=" * 60)
        logger.info("Trajectory Result")
        logger.info("=" * 60)
        logger.info(f"Query: {trajectory.query}")
        logger.info(f"Status: {trajectory.status}")
        logger.info(f"Generated Answer: {trajectory.generated_answer}")
        logger.info(f"Reasoning Steps ({len(trajectory.reasoning_steps)} steps):")
        for i, step in enumerate(trajectory.reasoning_steps, start=1):
            logger.info(f"  {i}. {step}")
        logger.info(f"Used Bullet IDs: {trajectory.used_bullet_ids}")
        if trajectory.error_message:
            logger.info(f"Error Message: {trajectory.error_message}")
        logger.info("=" * 60)

    except Exception as e:
        logger.exception(f"Failed to run GeneratorAgent: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
