"""LangChain ChatModelを使用したLLMリクエストクライアント."""

import logging
from typing import Any, TypeVar

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


def create_chat_model(provider: str, model: str, **kwargs) -> BaseChatModel:  # noqa: ANN003
    """プロバイダ名からChatModelを生成するファクトリ.

    Args:
        provider: プロバイダ名（openai / bedrock / azure）
        model: モデル名
        **kwargs: 追加のキーワード引数

    Returns:
        ChatModelインスタンス

    Raises:
        ValueError: 未知のプロバイダが指定された場合
    """
    if provider == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(model=model, **kwargs)
    if provider == "bedrock":
        from langchain_aws import ChatBedrock

        return ChatBedrock(model_id=model, **kwargs)
    if provider == "azure":
        from langchain_openai import AzureChatOpenAI

        return AzureChatOpenAI(model=model, **kwargs)
    msg = f"Unknown provider: {provider}"
    raise ValueError(msg)


class LLMClient:
    """LangChainのChatModelをラップするクライアントクラス."""

    def __init__(self, chat_model: BaseChatModel) -> None:
        """LLMClientを初期化する.

        Args:
            chat_model: LangChainのChatModel
        """
        self.chat_model = chat_model

    def invoke(self, messages: list[BaseMessage]) -> AIMessage:
        """メッセージリストでLLMにリクエストを送信する.

        Args:
            messages: メッセージリスト

        Returns:
            LLMの応答メッセージ

        Raises:
            Exception: LLMリクエストが失敗した場合
        """
        try:
            return self.chat_model.invoke(messages)
        except Exception:
            logger.exception("LLM request failed")
            raise

    def invoke_with_template(self, template: str, variables: dict[str, str]) -> str:
        """テンプレートを使用してLLMにリクエストを送信する.

        Args:
            template: プロンプトテンプレート
            variables: テンプレート変数

        Returns:
            LLMの応答文字列

        Raises:
            Exception: LLMリクエストが失敗した場合
        """
        try:
            prompt = ChatPromptTemplate.from_template(template)
            chain = prompt | self.chat_model | StrOutputParser()
            return chain.invoke(variables)
        except Exception:
            logger.exception("LLM request with template failed")
            raise

    def invoke_structured(
        self,
        messages: list[BaseMessage],
        schema: type[T],
    ) -> T:
        """メッセージリストでLLMにリクエストを送信し、構造化された出力を得る.

        Args:
            messages: メッセージリスト
            schema: 出力スキーマ（Pydantic BaseModel）

        Returns:
            構造化されたLLMの応答

        Raises:
            Exception: LLMリクエストが失敗した場合
        """
        try:
            structured_llm = self.chat_model.with_structured_output(schema)
            return structured_llm.invoke(messages)
        except Exception:
            logger.exception("Structured LLM request failed")
            raise

    def invoke_structured_with_template(
        self,
        template: str,
        variables: dict[str, Any],
        schema: type[T],
    ) -> T:
        """テンプレートを使用してLLMにリクエストを送信し、構造化された出力を得る.

        Args:
            template: プロンプトテンプレート
            variables: テンプレート変数
            schema: 出力スキーマ（Pydantic BaseModel）

        Returns:
            構造化されたLLMの応答

        Raises:
            Exception: LLMリクエストが失敗した場合
        """
        try:
            prompt = ChatPromptTemplate.from_template(template)
            structured_llm = self.chat_model.with_structured_output(schema)
            chain = prompt | structured_llm
            return chain.invoke(variables)
        except Exception:
            logger.exception("Structured LLM request with template failed")
            raise
