"""app.yaml設定ファイルの読み込みとChatModelレジストリ構築."""

import os
from collections.abc import Generator
from pathlib import Path
from typing import Any

import yaml
from langchain_core.language_models import BaseChatModel

from src.common.schema.llm_config import AppYamlConfig, ChatClientEntry
from src.components.llm_client.client import create_chat_model


class AppConfigLoader:
    """app.yaml設定ファイルを読み込むローダー."""

    def __init__(self, config_path: str = "config/app.yaml") -> None:
        """AppConfigLoaderを初期化する.

        Args:
            config_path: 設定ファイルのパス
        """
        self.config_path = Path(config_path)

    def load(self) -> AppYamlConfig:
        """YAMLを読み込みPydanticモデルに変換する."""
        if not self.config_path.exists():
            msg = f"設定ファイルが見つからない: {self.config_path}"
            raise FileNotFoundError(msg)
        data = yaml.safe_load(self.config_path.read_text())
        return AppYamlConfig(**data)


def resolve_env_vars(config: dict[str, Any]) -> dict[str, Any]:
    """_envサフィックスのフィールドを環境変数で解決する."""
    resolved = {}
    for key, value in config.items():
        if key.endswith("_env"):
            resolved_key = key[:-4]  # "_env" を除去
            resolved[resolved_key] = os.getenv(str(value))
        else:
            resolved[key] = value
    return resolved


def _iter_provider_entries(app_config: AppYamlConfig) -> Generator[tuple[str, list[ChatClientEntry]]]:
    """プロバイダ名とエントリリストのペアをイテレートする."""
    clients = app_config.llms.chat_clients
    yield "bedrock", clients.bedrock
    yield "azure", clients.azure
    yield "openai", clients.openai


def build_chat_model_registry(app_config: AppYamlConfig) -> dict[str, BaseChatModel]:
    """AppYamlConfigから全ChatModelインスタンスを生成しレジストリを構築する."""
    registry: dict[str, BaseChatModel] = {}
    for provider, entries in _iter_provider_entries(app_config):
        for entry in entries:
            resolved_config = resolve_env_vars(entry.config)
            params = {k: v for k, v in entry.default_params.items() if v is not None}
            model_name = resolved_config.pop("model", resolved_config.pop("model_id", ""))
            model = create_chat_model(
                provider=provider,
                model=model_name,
                **resolved_config,
                **params,
            )
            registry[entry.name] = model
    return registry
