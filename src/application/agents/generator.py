"""Generatorエージェントとプロンプト構築の実装."""

import logging
import textwrap
from pathlib import Path

from pydantic import BaseModel, Field

from src.common.defs.trajectory import Trajectory
from src.components.hybrid_search.models import SearchQuery
from src.components.hybrid_search.search import HybridSearch
from src.components.llm_client.client import LLMClient
from src.components.playbook_store.models import Bullet, Playbook
from src.components.playbook_store.store import PlaybookStore

logger = logging.getLogger(__name__)


class GenerationResponse(BaseModel):
    """Generatorの構造化出力モデル."""

    reasoning: str = Field(
        description="回答に至るまでの思考過程をステップバイステップで記述する",
    )
    answer: str = Field(
        description="最終的な回答テキスト。選択肢がある場合は選択肢のテキストをそのまま含める",
    )


class PromptBuilder:
    """プロンプトテンプレートの読み込みと構築を行うビルダー."""

    def __init__(self, prompts_dir: str = "prompts/generator") -> None:
        """PromptBuilderを初期化する.

        Args:
            prompts_dir: プロンプトテンプレートディレクトリのパス
        """
        self.prompts_dir = Path(prompts_dir)

    def build(self, query: str, bullets: list[Bullet], dataset: str) -> str:
        """クエリと検索結果からプロンプト文字列を構築する.

        データセット固有のテンプレートが存在すればそれを使用し、
        存在しなければデフォルトテンプレートを使用する.

        Args:
            query: 入力クエリ
            bullets: 検索結果のBulletリスト
            dataset: データセット名

        Returns:
            構築されたプロンプト文字列
        """
        template = self._load_template(dataset)
        context = self._format_context(bullets)
        return template.format(context=context, query=query)

    def _load_template(self, dataset: str) -> str:
        """テンプレートファイルを読み込む.

        データセット固有のテンプレートが存在すればそれを使用し、
        存在しなければデフォルトテンプレートを使用する.
        デフォルトも存在しない場合はハードコードのフォールバックを使用する.

        Args:
            dataset: データセット名

        Returns:
            テンプレート文字列
        """
        dataset_template_path = self.prompts_dir / f"{dataset}.txt"
        default_template_path = self.prompts_dir / "default.txt"

        if dataset_template_path.exists():
            return dataset_template_path.read_text(encoding="utf-8")

        if default_template_path.exists():
            return default_template_path.read_text(encoding="utf-8")

        logger.warning(
            "No template file found for dataset '%s' or default. Using fallback template.",
            dataset,
        )
        return self._fallback_template()

    def _fallback_template(self) -> str:
        """ハードコードのフォールバックテンプレートを返す.

        Returns:
            フォールバックテンプレート文字列
        """
        return textwrap.dedent(
            """
            以下の知識ベースを参考にして、タスクに回答してください.

            ## 知識ベース
            {context}

            ## タスク
            {query}

            ## 回答
            """
        ).strip()

    def _format_context(self, bullets: list[Bullet]) -> str:
        """Bulletリストをコンテキスト文字列にフォーマットする.

        Args:
            bullets: Bulletリスト

        Returns:
            改行区切りのコンテキスト文字列
        """
        if not bullets:
            return "(知識ベースは空です)"

        return "\n\n".join(
            f"[{bullet.section}] {bullet.content}" for bullet in bullets
        )


class GeneratorAgent:
    """タスク実行・推論を行うエージェント."""

    def __init__(
        self,
        playbook_store: PlaybookStore,
        hybrid_search: HybridSearch,
        llm_client: LLMClient,
        prompt_builder: PromptBuilder,
    ) -> None:
        """GeneratorAgentを初期化する.

        Args:
            playbook_store: Playbook永続化ストア
            hybrid_search: ハイブリッド検索エンジン
            llm_client: LLMクライアント
            prompt_builder: プロンプト構築ビルダー
        """
        self.playbook_store = playbook_store
        self.hybrid_search = hybrid_search
        self.llm_client = llm_client
        self.prompt_builder = prompt_builder

    def run(self, query: str, dataset: str) -> Trajectory:
        """クエリを実行しTrajectoryを返す.

        処理フロー:
        1. PlaybookStoreからPlaybook読み込み
        2. HybridSearchで関連Bullet検索
        3. PromptBuilderでプロンプト構築
        4. LLMClientでタスク実行
        5. Trajectory生成・返却

        Args:
            query: 入力クエリ
            dataset: データセット名

        Returns:
            推論過程を記録したTrajectory
        """
        reasoning_steps: list[str] = []
        used_bullet_ids: list[str] = []

        try:
            reasoning_steps.append(f"Playbookを読み込み中: dataset={dataset}")
            playbook = self.playbook_store.load(dataset)

            reasoning_steps.append("ハイブリッド検索で関連知識を取得中")
            search_results = self._search_playbook(query, playbook)
            used_bullet_ids = [result.bullet.id for result in search_results]
            bullets = [result.bullet for result in search_results]

            reasoning_steps.append(f"{len(bullets)}件のBulletを取得")
            reasoning_steps.append("プロンプトを構築中")
            prompt = self.prompt_builder.build(query, bullets, dataset)

            reasoning_steps.append("LLMにリクエストを送信中")
            response = self._invoke_llm(prompt)

            reasoning_steps.append(f"LLM推論過程: {response.reasoning}")
            reasoning_steps.append("推論完了")

            return Trajectory(
                query=query,
                dataset=dataset,
                generated_answer=response.answer,
                reasoning_steps=reasoning_steps,
                used_bullet_ids=used_bullet_ids,
                status="success",
                error_message=None,
            )

        except Exception as e:
            logger.exception("GeneratorAgent execution failed")
            error_message = f"{type(e).__name__}: {e!s}"
            reasoning_steps.append(f"エラーが発生: {error_message}")

            return Trajectory(
                query=query,
                dataset=dataset,
                generated_answer="",
                reasoning_steps=reasoning_steps,
                used_bullet_ids=used_bullet_ids,
                status="failure",
                error_message=error_message,
            )

    def _search_playbook(
        self,
        query: str,
        playbook: Playbook,
    ) -> list:
        """Playbookから関連Bulletを検索する.

        Args:
            query: 検索クエリ
            playbook: Playbook

        Returns:
            検索結果のリスト
        """
        search_query = SearchQuery(query_text=query, top_k=10)
        return self.hybrid_search.search(search_query, playbook)

    def _invoke_llm(self, prompt: str) -> GenerationResponse:
        """LLMにプロンプトを送信し構造化された応答を取得する.

        Args:
            prompt: プロンプト文字列

        Returns:
            構造化されたLLMの応答

        Raises:
            Exception: LLMリクエストが失敗した場合
        """
        return self.llm_client.invoke_structured_with_template(
            template=prompt,
            variables={},
            schema=GenerationResponse,
        )
