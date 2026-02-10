"""Reflectorエージェントとプロンプト構築の実装."""

import logging
import textwrap
from pathlib import Path

from src.common.defs.insight import (
    BulletEvaluation,
    Insight,
    InsightsResponse,
    ReflectionResult,
)
from src.common.defs.trajectory import Trajectory
from src.components.llm_client.client import LLMClient
from src.components.playbook_store.models import Bullet, Playbook
from src.components.playbook_store.store import PlaybookStore

logger = logging.getLogger(__name__)


class ReflectorPromptBuilder:
    """Reflector用プロンプトテンプレートの読み込みと構築を行うビルダー."""

    def __init__(self, prompts_dir: str = "prompts/reflector") -> None:
        """ReflectorPromptBuilderを初期化する.

        Args:
            prompts_dir: プロンプトテンプレートディレクトリのパス
        """
        self.prompts_dir = Path(prompts_dir)

    def build(  # noqa: PLR0913
        self,
        trajectory: Trajectory,
        ground_truth: str,
        test_report: str,
        used_bullets: list[Bullet],
        dataset: str,
        previous_insights: list[Insight] | None = None,
    ) -> str:
        """分析用プロンプト文字列を構築する.

        データセット固有のテンプレートが存在すればそれを使用し、
        存在しなければデフォルトテンプレートを使用する.
        反復改善時はprevious_insightsを含める.

        Args:
            trajectory: 分析対象のTrajectory
            ground_truth: 正解データ
            test_report: テスト結果
            used_bullets: 使用されたBulletリスト
            dataset: データセット名
            previous_insights: 前回の分析結果（反復改善時）

        Returns:
            構築されたプロンプト文字列
        """
        template = self._load_template(dataset)
        reasoning_steps = self._format_reasoning_steps(trajectory.reasoning_steps)
        bullets_text = self._format_bullets(used_bullets)
        previous_insights_section = self._format_previous_insights(previous_insights)

        return template.format(
            generated_answer=trajectory.generated_answer,
            ground_truth=ground_truth,
            test_report=test_report,
            reasoning_steps=reasoning_steps,
            used_bullets=bullets_text,
            previous_insights_section=previous_insights_section,
        )

    def build_evaluation_prompt(
        self,
        trajectory: Trajectory,
        ground_truth: str,
        bullet: Bullet,
    ) -> str:
        """Bullet評価用プロンプト文字列を構築する.

        Args:
            trajectory: 分析対象のTrajectory
            ground_truth: 正解データ
            bullet: 評価対象のBullet

        Returns:
            構築されたプロンプト文字列
        """
        template = self._load_evaluation_template()
        return template.format(
            query=trajectory.query,
            generated_answer=trajectory.generated_answer,
            ground_truth=ground_truth,
            bullet_id=bullet.id,
            bullet_section=bullet.section,
            bullet_content=bullet.content,
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

    def _load_evaluation_template(self) -> str:
        """Bullet評価用テンプレートファイルを読み込む.

        Returns:
            テンプレート文字列
        """
        evaluation_template_path = self.prompts_dir / "bullet_evaluation.txt"

        if evaluation_template_path.exists():
            return evaluation_template_path.read_text(encoding="utf-8")

        logger.warning("No evaluation template file found. Using fallback template.")
        return self._fallback_evaluation_template()

    def _fallback_template(self) -> str:
        """ハードコードのフォールバックテンプレートを返す.

        Returns:
            フォールバックテンプレート文字列
        """
        return textwrap.dedent(
            """Trajectoryを分析し、エラーの根本原因を特定してください.

            ## 生成結果
            {generated_answer}

            ## 正解
            {ground_truth}

            ## テスト結果
            {test_report}

            ## 推論過程
            {reasoning_steps}

            ## 使用した知識
            {used_bullets}

            {previous_insights_section}

            分析結果を返してください.
            """
        )

    def _fallback_evaluation_template(self) -> str:
        """Bullet評価用のフォールバックテンプレートを返す.

        Returns:
            フォールバックテンプレート文字列
        """
        return textwrap.dedent("""
            Bulletの有用性を評価してください.

            タスク: {query}
            生成結果: {generated_answer}
            正解: {ground_truth}

            Bullet ID: {bullet_id}
            内容: {bullet_content}

            helpful/harmful/neutralのいずれかで評価してください.
            """
        )

    def _format_reasoning_steps(self, steps: list[str]) -> str:
        """推論ステップをフォーマットする.

        Args:
            steps: 推論ステップリスト

        Returns:
            改行区切りの推論ステップ文字列
        """
        if not steps:
            return "(推論ステップは記録されていません)"

        return "\n".join(f"{i + 1}. {step}" for i, step in enumerate(steps))

    def _format_bullets(self, bullets: list[Bullet]) -> str:
        """Bulletリストをフォーマットする.

        Args:
            bullets: Bulletリスト

        Returns:
            改行区切りのBullet文字列
        """
        if not bullets:
            return "(使用されたBulletはありません)"

        return "\n\n".join(
            f"[{bullet.id}] {bullet.section}\n{bullet.content}" for bullet in bullets
        )

    def _format_previous_insights(
        self,
        previous_insights: list[Insight] | None,
    ) -> str:
        """前回の分析結果をフォーマットする.

        Args:
            previous_insights: 前回のInsightリスト

        Returns:
            フォーマットされた文字列
        """
        if not previous_insights:
            return ""

        insights_text = "\n\n".join(
            f"- 思考: {insight.reasoning}\n"
            f"- エラー: {insight.error_identification}\n"
            f"- 原因: {insight.root_cause_analysis}\n"
            f"- 正解: {insight.correct_approach}\n"
            f"- 教訓: {insight.key_insight}"
            for insight in previous_insights
        )

        return textwrap.dedent(f"""
            ## 前回の分析結果（反復改善）
            {insights_text}

            前回の分析を踏まえて、さらに深い洞察を提供してください.
            """
        )


class ReflectorAgent:
    """Trajectoryを分析し、Insightsを抽出するエージェント."""

    def __init__(
        self,
        llm_client: LLMClient,
        prompt_builder: ReflectorPromptBuilder,
        playbook_store: PlaybookStore,
    ) -> None:
        """ReflectorAgentを初期化する.

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
        trajectory: Trajectory,
        ground_truth: str,
        test_report: str,
        dataset: str,
        max_iterations: int = 1,
    ) -> ReflectionResult:
        """Trajectoryを分析しReflectionResultを返す.

        処理フロー:
            1. PlaybookStoreからPlaybook読み込み
            2. used_bullet_idsに対応するBulletを取得
            3. PromptBuilderでプロンプト構築
            4. LLMClientで分析実行
            5. Insightsをパース
            6. BulletEvaluationを生成
            7. (オプション) 反復改善
            8. ReflectionResult生成・返却

        Args:
            trajectory: 分析対象のTrajectory
            ground_truth: 正解データ
            test_report: テスト結果
            dataset: データセット名
            max_iterations: 反復改善の最大回数

        Returns:
            分析結果のReflectionResult
        """
        try:
            # 1. Playbookを読み込み
            playbook = self.playbook_store.load(dataset)

            # 2. 使用されたBulletを取得
            used_bullets = self._resolve_bullets(
                trajectory.used_bullet_ids,
                playbook,
            )

            # 3-5. 反復改善を実行
            insights = self._extract_insights_iteratively(
                trajectory,
                ground_truth,
                test_report,
                used_bullets,
                dataset,
                max_iterations,
            )

            # 6. Bullet評価を生成
            bullet_evaluations = self._evaluate_bullets(
                trajectory,
                ground_truth,
                used_bullets,
            )

            # 7. ReflectionResultを返す
            return ReflectionResult(
                insights=insights,
                bullet_evaluations=bullet_evaluations,
                trajectory_query=trajectory.query,
                trajectory_dataset=trajectory.dataset,
                iteration_count=max_iterations,
            )

        except Exception:
            logger.exception("ReflectorAgent execution failed")
            # エラー時は空の結果を返す
            return ReflectionResult(
                insights=[],
                bullet_evaluations=[],
                trajectory_query=trajectory.query,
                trajectory_dataset=trajectory.dataset,
                iteration_count=0,
            )

    def _extract_insights_iteratively(  # noqa: PLR0913
        self,
        trajectory: Trajectory,
        ground_truth: str,
        test_report: str,
        used_bullets: list[Bullet],
        dataset: str,
        max_iterations: int,
    ) -> list[Insight]:
        """反復的にInsightsを抽出する.

        Args:
            trajectory: 分析対象のTrajectory
            ground_truth: 正解データ
            test_report: テスト結果
            used_bullets: 使用されたBulletリスト
            dataset: データセット名
            max_iterations: 最大反復回数

        Returns:
            抽出されたInsightリスト
        """
        previous_insights: list[Insight] | None = None

        for i in range(max_iterations):
            logger.info("Extracting insights (iteration %d/%d)", i + 1, max_iterations)

            insights = self._extract_insights(
                trajectory,
                ground_truth,
                test_report,
                used_bullets,
                dataset,
                previous_insights,
            )

            if i < max_iterations - 1:
                # 最終イテレーション以外は次のイテレーションに渡す
                previous_insights = insights

        return insights

    def _extract_insights(  # noqa: PLR0913
        self,
        trajectory: Trajectory,
        ground_truth: str,
        test_report: str,
        used_bullets: list[Bullet],
        dataset: str,
        previous_insights: list[Insight] | None = None,
    ) -> list[Insight]:
        """LLM応答からInsightリストをパースする.

        Args:
            trajectory: 分析対象のTrajectory
            ground_truth: 正解データ
            test_report: テスト結果
            used_bullets: 使用されたBulletリスト
            dataset: データセット名
            previous_insights: 前回のInsightリスト

        Returns:
            抽出されたInsightリスト
        """
        try:
            # プロンプトを構築
            prompt = self.prompt_builder.build(
                trajectory,
                ground_truth,
                test_report,
                used_bullets,
                dataset,
                previous_insights,
            )

            # Structured Outputでリクエスト
            response = self.llm_client.invoke_structured_with_template(
                template=prompt,
                variables={},
                schema=InsightsResponse,
            )

            return response.insights  # noqa: TRY300

        except Exception:
            logger.exception("Failed to extract insights")
            return []

    def _evaluate_bullets(
        self,
        trajectory: Trajectory,
        ground_truth: str,
        used_bullets: list[Bullet],
    ) -> list[BulletEvaluation]:
        """使用されたBulletの有用性を評価する.

        Args:
            trajectory: 分析対象のTrajectory
            ground_truth: 正解データ
            used_bullets: 使用されたBulletリスト

        Returns:
            Bullet評価のリスト
        """
        if not used_bullets:
            logger.info("No bullets to evaluate")
            return []

        evaluations: list[BulletEvaluation] = []

        for bullet in used_bullets:
            try:
                evaluation = self._evaluate_single_bullet(
                    trajectory,
                    ground_truth,
                    bullet,
                )
                evaluations.append(evaluation)
            except Exception:
                logger.exception("Failed to evaluate bullet %s", bullet.id)
                # 評価失敗時はneutralとして扱う
                evaluations.append(
                    BulletEvaluation(
                        bullet_id=bullet.id,
                        tag="neutral",
                        reason="評価中にエラーが発生しました",
                    )
                )

        return evaluations

    def _evaluate_single_bullet(
        self,
        trajectory: Trajectory,
        ground_truth: str,
        bullet: Bullet,
    ) -> BulletEvaluation:
        """単一のBulletを評価する.

        Args:
            trajectory: 分析対象のTrajectory
            ground_truth: 正解データ
            bullet: 評価対象のBullet

        Returns:
            Bullet評価
        """
        prompt = self.prompt_builder.build_evaluation_prompt(
            trajectory,
            ground_truth,
            bullet,
        )

        # Structured Outputでリクエスト
        evaluation = self.llm_client.invoke_structured_with_template(
            template=prompt,
            variables={},
            schema=BulletEvaluation,
        )

        # bullet_idを設定（LLMが返さない場合があるため）
        evaluation.bullet_id = bullet.id

        return evaluation

    def _resolve_bullets(
        self,
        bullet_ids: list[str],
        playbook: Playbook,
    ) -> list[Bullet]:
        """Bullet IDリストからBulletオブジェクトを取得する.

        Args:
            bullet_ids: Bullet IDリスト
            playbook: Playbook

        Returns:
            Bulletオブジェクトのリスト
        """
        if not bullet_ids:
            return []

        # PlaybookからBullet IDでBulletを検索
        bullet_map = {bullet.id: bullet for bullet in playbook.bullets}
        resolved_bullets = []

        for bullet_id in bullet_ids:
            if bullet_id in bullet_map:
                resolved_bullets.append(bullet_map[bullet_id])
            else:
                logger.warning("Bullet ID %s not found in playbook", bullet_id)

        return resolved_bullets
