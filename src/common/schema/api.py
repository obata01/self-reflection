"""APIリクエスト/レスポンススキーマ."""

from pydantic import BaseModel


class WorkflowRequest(BaseModel):
    """ワークフロー実行リクエスト."""

    query: str
    dataset: str = "appworld"


class WorkflowResponse(BaseModel):
    """ワークフロー実行レスポンス."""

    llm_response: str
    search_results_count: int
