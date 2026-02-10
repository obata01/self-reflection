"""FastAPIアプリケーションのエントリポイント."""

from fastapi import FastAPI

from src.application.workflows.reflection_workflow import ReflectionWorkflow
from src.common.config.settings import load_config
from src.common.di.container import Container
from src.common.schema.api import WorkflowRequest, WorkflowResponse


def create_app() -> FastAPI:
    """FastAPIアプリケーションを生成する.

    Returns:
        FastAPIインスタンス
    """
    app = FastAPI(title="Self-Reflection System")

    container = Container()
    config = load_config()
    container.config.from_dict(config.model_dump())
    app.state.container = container

    return app


app = create_app()


@app.get("/health")
def health() -> dict[str, str]:
    """ヘルスチェックエンドポイント.

    Returns:
        ステータス情報
    """
    return {"status": "ok"}


@app.post("/workflow/run", response_model=WorkflowResponse)
def run_workflow(request: WorkflowRequest) -> WorkflowResponse:
    """ワークフロー実行エンドポイント.

    Args:
        request: ワークフロー実行リクエスト

    Returns:
        ワークフロー実行結果
    """
    container: Container = app.state.container

    workflow = ReflectionWorkflow(
        playbook_store=container.playbook_store(),
        hybrid_search=container.hybrid_search(),
        llm_client=container.llm_client(),
    )

    graph = workflow.build()
    result = graph.invoke(
        {
            "query": request.query,
            "dataset": request.dataset,
            "playbook": None,
            "search_results": [],
            "llm_response": None,
        }
    )

    return WorkflowResponse(
        llm_response=result["llm_response"],
        search_results_count=len(result["search_results"]),
    )
