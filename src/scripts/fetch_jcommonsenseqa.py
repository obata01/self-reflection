"""JCommonsenseQAデータセット取得スクリプト."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.common.lib.logging import getLogger
from src.components.dataset_loader import DatasetLoader

logger = getLogger(__name__)


def main() -> None:
    """JCommonsenseQAデータセットを取得して保存する."""
    loader = DatasetLoader()

    logger.info("Starting JCommonsenseQA dataset download...")
    try:
        results = loader.fetch_and_save()

        logger.info("=" * 50)
        logger.info("Dataset download completed successfully!")
        logger.info("=" * 50)
        for split, count in results.items():
            logger.info("  %s: %s records", split, count)
        logger.info("=" * 50)

    except Exception:
        logger.exception("Failed to download dataset")
        sys.exit(1)


if __name__ == "__main__":
    main()
