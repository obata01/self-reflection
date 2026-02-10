"""YAML LLMクライアント設定のPydanticスキーマ."""

from typing import Any

from pydantic import BaseModel, Field


class ChatClientEntry(BaseModel):
    """個別のLLMクライアント定義."""

    name: str
    config: dict[str, Any]
    default_params: dict[str, Any] = Field(default_factory=dict)


class ChatClientsConfig(BaseModel):
    """プロバイダ別クライアント定義."""

    bedrock: list[ChatClientEntry] = Field(default_factory=list)
    azure: list[ChatClientEntry] = Field(default_factory=list)
    openai: list[ChatClientEntry] = Field(default_factory=list)


class LLMsConfig(BaseModel):
    """LLMs設定のルート."""

    chat_clients: ChatClientsConfig


class AppYamlConfig(BaseModel):
    """app.yaml全体のルートモデル."""

    llms: LLMsConfig
