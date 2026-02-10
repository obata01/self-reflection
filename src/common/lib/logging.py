"""ロギング設定ユーティリティ."""

import logging


def getLogger(name: str) -> logging.Logger:
    """指定された名前のロガーを取得する.

    呼び出し時にlogging.basicConfig()を実行してから、ロガーを返す.

    Args:
        name: ロガー名（通常は__name__を使用）

    Returns:
        ロガーインスタンス
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    return logging.getLogger(name)
