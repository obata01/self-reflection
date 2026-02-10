"""アプリケーション設定の管理."""

import os

from pydantic import BaseModel, Field


class LLMConfig(BaseModel):
    """LLM設定."""

    provider: str = "openai"
    model: str = "gpt-4.1-mini"
    api_key: str = ""


class EmbeddingConfig(BaseModel):
    """Embedding設定."""

    model: str = "text-embedding-3-small"
    api_key: str = ""


class PlaybookConfig(BaseModel):
    """Playbook永続化設定."""

    data_dir: str = "data/playbooks"


class SearchConfig(BaseModel):
    """検索設定."""

    alpha: float = Field(default=0.5, ge=0.0, le=1.0)


class AppConfig(BaseModel):
    """アプリケーション全体の設定."""

    llm: LLMConfig = Field(default_factory=LLMConfig)
    embedding: EmbeddingConfig = Field(default_factory=EmbeddingConfig)
    playbook: PlaybookConfig = Field(default_factory=PlaybookConfig)
    search: SearchConfig = Field(default_factory=SearchConfig)


def load_config() -> AppConfig:
    """環境変数から設定を読み込む.

    Returns:
        アプリケーション設定
    """
    return AppConfig(
        llm=LLMConfig(
            provider=os.getenv("LLM_PROVIDER", "openai"),
            model=os.getenv("LLM_MODEL", "gpt-4.1-mini"),
            api_key=os.getenv("OPENAI_API_KEY", ""),
        ),
        embedding=EmbeddingConfig(
            model=os.getenv("EMBEDDING_MODEL", "text-embedding-3-small"),
            api_key=os.getenv("OPENAI_API_KEY", ""),
        ),
        playbook=PlaybookConfig(
            data_dir=os.getenv("PLAYBOOK_DATA_DIR", "data/playbooks"),
        ),
        search=SearchConfig(
            alpha=float(os.getenv("SEARCH_ALPHA", "0.5")),
        ),
    )
