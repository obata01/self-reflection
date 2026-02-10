"""Curatorエージェントとプロンプト構築の実装."""

import logging
import textwrap
import uuid
from pathlib import Path

import yaml

from src.common.defs.curation import CurationResult, DeltasResponse
from src.common.defs.insight import BulletEvaluation, Insight
from src.components.llm_client.client import LLMClient
from src.components.playbook_store.models import Bullet, DeltaContextItem, Playbook
from src.components.playbook_store.store import PlaybookStore

logger = logging.getLogger(__name__)


class CuratorPromptBuilder:
    """Curator用プロンプトテンプレートの読み込みと構築を行うビルダー."""

    def __init__(self, prompts_dir: str = "prompts/curator") -> None:
        """CuratorPromptBuilderを初期化する.

        Args:
            prompts_dir: プロンプトテンプレートディレクトリのパス
        """
        self.prompts_dir = Path(prompts_dir)

    def build(
        self,
        insights: list[Insight],
        bullets: list[Bullet],
        sections: list[dict],
        dataset: str,
    ) -> str:
        """Delta生成用プロンプト文字列を構築する.

        データセット固有のテンプレートが存在すればそれを使用し、
        存在しなければデフォルトテンプレートを使用する.

        Args:
            insights: Insightリスト
            bullets: 現在のPlaybookのBulletリスト
            sections: セクション定義リスト
            dataset: データセット名

        Returns:
            構築されたプロンプト文字列
        """
        template = self._load_template(dataset)
        insights_text = self._format_insights(insights)
        bullets_text = self._format_bullets(bullets)
        sections_text = self._format_sections(sections)

        return template.format(
            insights=insights_text,
            bullets=bullets_text,
            sections=sections_text,
        )

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
            あなたはPlaybookのキュレーターです.
            以下のInsightsを分析し、Playbookへの更新操作を決定してください.

            Insights:
            {insights}

            現在のPlaybook:
            {bullets}

            利用可能なセクション:
            {sections}

            各Insightについて、ADD/UPDATE/DELETE操作を決定してください.
            """
        ).strip()

    def _format_insights(self, insights: list[Insight]) -> str:
        """Insightリストをフォーマットする.

        Args:
            insights: Insightリスト

        Returns:
            改行区切りのInsight文字列
        """
        if not insights:
            return "(Insightsはありません)"

        return "\n\n".join(
            f"- 教訓: {insight.key_insight}\n"
            f"  思考: {insight.reasoning}\n"
            f"  エラー: {insight.error_identification}\n"
            f"  原因: {insight.root_cause_analysis}\n"
            f"  正解: {insight.correct_approach}"
            for insight in insights
        )

    def _format_bullets(self, bullets: list[Bullet]) -> str:
        """Bulletリストをフォーマットする.

        Args:
            bullets: Bulletリスト

        Returns:
            改行区切りのBullet文字列
        """
        if not bullets:
            return "(Bulletはありません)"

        return "\n\n".join(
            f"[{bullet.id}] {bullet.section}\n{bullet.content}" for bullet in bullets
        )

    def _format_sections(self, sections: list[dict]) -> str:
        """セクション定義リストをフォーマットする.

        Args:
            sections: セクション定義リスト

        Returns:
            改行区切りのセクション文字列
        """
        if not sections:
            return "(セクション定義はありません)"

        return "\n".join(
            f"- {section['name']}: {section.get('description', '')}"
            for section in sections
        )


class CuratorAgent:
    """InsightsからDelta Context Itemsを生成し、Playbookを更新するエージェント."""

    def __init__(
        self,
        llm_client: LLMClient,
        prompt_builder: CuratorPromptBuilder,
        playbook_store: PlaybookStore,
    ) -> None:
        """CuratorAgentを初期化する.

        Args:
            llm_client: LLMクライアント
            prompt_builder: プロンプト構築ビルダー
            playbook_store: Playbook永続化ストア
        """
        self.llm_client = llm_client
        self.prompt_builder = prompt_builder
        self.playbook_store = playbook_store

    def run(
        self,
        reflection_result,
        dataset: str,
    ) -> CurationResult:
        """ReflectionResultを基にPlaybookを更新しCurationResultを返す.

        処理フロー:
            1. PlaybookStoreからPlaybook読み込み
            2. InsightsからDelta Context Items生成（LLM使用）
            3. BulletEvaluationでカウンター更新
            4. Delta Context ItemsをPlaybookにマージ
            5. PlaybookStoreで永続化
            6. CurationResult生成・返却

        Args:
            reflection_result: ReflectionResult
            dataset: データセット名

        Returns:
            キュレーション結果のCurationResult
        """
        try:
            # 1. Playbookを読み込み
            playbook = self.playbook_store.load(dataset)
            bullets_before = len(playbook.bullets)

            # 2. セクション定義を読み込み
            sections = self._load_sections(dataset)

            # 3. Delta Context Itemsを生成
            deltas = self._generate_deltas(
                reflection_result.insights,
                playbook,
                sections,
                dataset,
            )

            # 4. BulletEvaluationでカウンター更新
            self._apply_bullet_evaluations(
                reflection_result.bullet_evaluations,
                playbook,
            )

            # 5. Delta Context ItemsをPlaybookにマージ
            self._merge_deltas(deltas, playbook)

            # 6. PlaybookStoreで永続化
            self.playbook_store.save(dataset, playbook)

            # 7. CurationResultを生成
            bullets_after = len(playbook.bullets)
            summary = self._generate_summary(deltas)

            return CurationResult(
                deltas=deltas,
                bullets_before=bullets_before,
                bullets_after=bullets_after,
                summary=summary,
            )

        except Exception:
            logger.exception("CuratorAgent execution failed")
            # エラー時は空の結果を返す
            bullets_count = len(playbook.bullets) if playbook else 0
            return CurationResult(
                deltas=[],
                bullets_before=bullets_count,
                bullets_after=bullets_count,
                summary="エラーが発生しました",
            )

    def _generate_deltas(
        self,
        insights: list[Insight],
        playbook: Playbook,
        sections: list[dict],
        dataset: str,
    ) -> list[DeltaContextItem]:
        """LLMを使用してInsightsからDelta Context Itemsを生成する.

        Args:
            insights: Insightリスト
            playbook: 現在のPlaybook
            sections: セクション定義リスト
            dataset: データセット名

        Returns:
            DeltaContextItemリスト
        """
        if not insights:
            logger.info("No insights to process")
            return []

        try:
            # プロンプトを構築
            prompt = self.prompt_builder.build(
                insights,
                playbook.bullets,
                sections,
                dataset,
            )

            # Structured Outputでリクエスト
            response = self.llm_client.invoke_structured_with_template(
                template=prompt,
                variables={},
                schema=DeltasResponse,
            )

            return response.deltas

        except Exception:
            logger.exception("Failed to generate deltas")
            return []

    def _apply_bullet_evaluations(
        self,
        bullet_evaluations: list[BulletEvaluation],
        playbook: Playbook,
    ) -> None:
        """BulletEvaluationに基づいてPlaybook内のBulletカウンターを更新する.

        Args:
            bullet_evaluations: BulletEvaluationリスト
            playbook: Playbook
        """
        if not bullet_evaluations:
            logger.info("No bullet evaluations to apply")
            return

        bullet_map = {bullet.id: bullet for bullet in playbook.bullets}

        for evaluation in bullet_evaluations:
            if evaluation.bullet_id not in bullet_map:
                logger.warning(
                    "Bullet ID %s not found in playbook, skipping evaluation",
                    evaluation.bullet_id,
                )
                continue

            bullet = bullet_map[evaluation.bullet_id]

            if evaluation.tag == "helpful":
                bullet.helpful += 1
            elif evaluation.tag == "harmful":
                bullet.harmful += 1

    def _merge_deltas(
        self,
        deltas: list[DeltaContextItem],
        playbook: Playbook,
    ) -> None:
        """Delta Context ItemsをPlaybookに適用する.

        Args:
            deltas: DeltaContextItemリスト
            playbook: Playbook
        """
        if not deltas:
            logger.info("No deltas to merge")
            return

        bullet_map = {bullet.id: bullet for bullet in playbook.bullets}

        for delta in deltas:
            if delta.type == "ADD":
                new_bullet = Bullet(
                    id=self._generate_bullet_id(),
                    section=delta.section,
                    content=delta.content,
                    searchable_text=delta.content,
                    keywords=[],
                    helpful=0,
                    harmful=0,
                    source_trajectory="",
                )
                playbook.bullets.append(new_bullet)
                logger.info("Added new bullet: %s", new_bullet.id)

            elif delta.type == "UPDATE":
                if delta.bullet_id is None or delta.bullet_id not in bullet_map:
                    logger.warning(
                        "Bullet ID %s not found for UPDATE, skipping",
                        delta.bullet_id,
                    )
                    continue

                bullet = bullet_map[delta.bullet_id]
                bullet.content = delta.content
                bullet.searchable_text = delta.content
                logger.info("Updated bullet: %s", delta.bullet_id)

            elif delta.type == "DELETE":
                if delta.bullet_id is None or delta.bullet_id not in bullet_map:
                    logger.warning(
                        "Bullet ID %s not found for DELETE, skipping",
                        delta.bullet_id,
                    )
                    continue

                playbook.bullets = [
                    b for b in playbook.bullets if b.id != delta.bullet_id
                ]
                logger.info("Deleted bullet: %s", delta.bullet_id)

    def _load_sections(self, dataset: str) -> list[dict]:
        """config/sections.yamlからセクション定義を読み込む.

        Args:
            dataset: データセット名

        Returns:
            セクション定義リスト
        """
        sections_path = Path("config/sections.yaml")

        if not sections_path.exists():
            logger.warning("sections.yaml not found at %s", sections_path)
            return []

        try:
            with sections_path.open(encoding="utf-8") as f:
                sections_data = yaml.safe_load(f)

            if not sections_data or dataset not in sections_data:
                logger.warning("No sections found for dataset '%s'", dataset)
                return []

            return sections_data[dataset]

        except Exception:
            logger.exception("Failed to load sections from %s", sections_path)
            return []

    def _generate_bullet_id(self) -> str:
        """新しいBulletに一意のIDを生成する.

        Returns:
            一意のBullet ID
        """
        return str(uuid.uuid4())

    def _generate_summary(self, deltas: list[DeltaContextItem]) -> str:
        """処理サマリーを生成する.

        Args:
            deltas: DeltaContextItemリスト

        Returns:
            サマリー文字列
        """
        add_count = sum(1 for d in deltas if d.type == "ADD")
        update_count = sum(1 for d in deltas if d.type == "UPDATE")
        delete_count = sum(1 for d in deltas if d.type == "DELETE")

        return f"ADD: {add_count}, UPDATE: {update_count}, DELETE: {delete_count}"
