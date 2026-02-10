"""LangGraphベースの内省ワークフロー."""

from typing import TypedDict

from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph

from src.components.hybrid_search.models import SearchQuery, SearchResult
from src.components.hybrid_search.search import HybridSearch
from src.components.llm_client.client import LLMClient
from src.components.playbook_store.models import Playbook
from src.components.playbook_store.store import PlaybookStore


class WorkflowState(TypedDict):
    """ワークフローの状態定義."""

    query: str
    dataset: str
    playbook: Playbook | None
    search_results: list[SearchResult]
    llm_response: str | None


class ReflectionWorkflow:
    """LangGraphベースの内省ワークフロー."""

    def __init__(
        self,
        playbook_store: PlaybookStore,
        hybrid_search: HybridSearch,
        llm_client: LLMClient,
    ) -> None:
        """ReflectionWorkflowを初期化する.

        Args:
            playbook_store: Playbook永続化ストア
            hybrid_search: ハイブリッド検索エンジン
            llm_client: LLMリクエストクライアント
        """
        self.playbook_store = playbook_store
        self.hybrid_search = hybrid_search
        self.llm_client = llm_client

    def build(self) -> CompiledStateGraph:
        """ワークフローグラフを構築・コンパイルする.

        Returns:
            コンパイル済みStateGraph
        """
        graph = StateGraph(WorkflowState)
        graph.add_node("load_playbook", self._load_playbook)
        graph.add_node("search", self._search)
        graph.add_node("generate", self._generate)
        graph.set_entry_point("load_playbook")
        graph.add_edge("load_playbook", "search")
        graph.add_edge("search", "generate")
        graph.add_edge("generate", END)
        return graph.compile()

    def _load_playbook(self, state: WorkflowState) -> dict:
        """Playbookを読み込むノード.

        Args:
            state: ワークフローの状態

        Returns:
            更新された状態のdict
        """
        playbook = self.playbook_store.load(state["dataset"])
        return {"playbook": playbook}

    def _search(self, state: WorkflowState) -> dict:
        """ハイブリッド検索を実行するノード.

        Args:
            state: ワークフローの状態

        Returns:
            更新された状態のdict
        """
        query = SearchQuery(query_text=state["query"])
        results = self.hybrid_search.search(query, state["playbook"])
        return {"search_results": results}

    def _generate(self, state: WorkflowState) -> dict:
        """LLMで応答を生成するノード.

        Args:
            state: ワークフローの状態

        Returns:
            更新された状態のdict
        """
        context = "\n".join(r.bullet.content for r in state["search_results"])
        template = "Context:\n{context}\n\nQuery: {query}\n\nAnswer:"
        response = self.llm_client.invoke_with_template(
            template, {"context": context, "query": state["query"]}
        )
        return {"llm_response": response}
