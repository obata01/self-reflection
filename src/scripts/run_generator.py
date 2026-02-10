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
        logger.info("Query: %s", query)
        logger.info("Dataset: %s", dataset)

        trajectory = generator.run(query, dataset)

        # 結果表示
        logger.info("=" * 60)
        logger.info("Trajectory Result")
        logger.info("=" * 60)
        logger.info("Query: %s", trajectory.query)
        logger.info("Status: %s", trajectory.status)
        logger.info("Generated Answer: %s", trajectory.generated_answer)
        logger.info("Reasoning Steps (%s steps):", len(trajectory.reasoning_steps))
        for i, step in enumerate(trajectory.reasoning_steps, start=1):
            logger.info("  %s. %s", i, step)
        logger.info("Used Bullet IDs: %s", trajectory.used_bullet_ids)
        if trajectory.error_message:
            logger.info("Error Message: %s", trajectory.error_message)
        logger.info("=" * 60)

    except Exception:
        logger.exception("Failed to run GeneratorAgent")
        sys.exit(1)


if __name__ == "__main__":
    main()
