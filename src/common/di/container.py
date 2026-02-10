"""依存性注入コンテナの定義."""

from dependency_injector import containers, providers
from langchain_openai import OpenAIEmbeddings

from src.application.agents.curator import CuratorAgent, CuratorPromptBuilder
from src.application.agents.generator import GeneratorAgent, PromptBuilder
from src.application.agents.reflector import (
    ReflectorAgent,
    ReflectorPromptBuilder,
)
from src.components.hybrid_search.embedding_client import EmbeddingClient
from src.components.hybrid_search.search import HybridSearch
from src.components.llm_client.client import LLMClient, create_chat_model
from src.components.playbook_store.store import PlaybookStore


class Container(containers.DeclarativeContainer):
    """アプリケーション全体のDIコンテナ."""

    config = providers.Configuration()

    chat_model = providers.Singleton(
        create_chat_model,
        provider=config.llm["provider"],
        model=config.llm["model"],
        api_key=config.llm["api_key"],
    )

    embedding_model = providers.Singleton(
        OpenAIEmbeddings,
        model=config.embedding.model,
        api_key=config.embedding.api_key,
    )

    playbook_store = providers.Singleton(
        PlaybookStore,
        data_dir=config.playbook.data_dir,
    )

    embedding_client = providers.Singleton(
        EmbeddingClient,
        model=embedding_model,
    )

    hybrid_search = providers.Singleton(
        HybridSearch,
        embedding_client=embedding_client,
        alpha=config.search.alpha,
    )

    llm_client = providers.Singleton(
        LLMClient,
        chat_model=chat_model,
    )

    prompt_builder = providers.Singleton(
        PromptBuilder,
        prompts_dir="prompts/generator",
    )

    generator_agent = providers.Factory(
        GeneratorAgent,
        playbook_store=playbook_store,
        hybrid_search=hybrid_search,
        llm_client=llm_client,
        prompt_builder=prompt_builder,
    )

    reflector_prompt_builder = providers.Singleton(
        ReflectorPromptBuilder,
        prompts_dir="prompts/reflector",
    )

    reflector_agent = providers.Factory(
        ReflectorAgent,
        llm_client=llm_client,
        prompt_builder=reflector_prompt_builder,
        playbook_store=playbook_store,
    )

    curator_prompt_builder = providers.Singleton(
        CuratorPromptBuilder,
        prompts_dir="prompts/curator",
    )

    curator_agent = providers.Factory(
        CuratorAgent,
        llm_client=llm_client,
        prompt_builder=curator_prompt_builder,
        playbook_store=playbook_store,
    )
