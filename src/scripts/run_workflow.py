"""JCommonsenseQAデータセットに対するワークフロー実行スクリプト.

train.jsonlの先頭N件に対して推論パイプラインを実行し、正解率を算出する.

Usage:
    # 推論のみ (Generate → Judge)
    python src/scripts/run_workflow.py --mode infer

    # フルパイプライン (Generate → Reflect → Curate)
    python src/scripts/run_workflow.py --mode full

    # 件数指定
    python src/scripts/run_workflow.py --mode infer --limit 10

    # ステージ別バッチ実行 (中間結果をファイルに保存)
    python src/scripts/run_workflow.py --mode batch-infer          # 全件推論 → infer.jsonl
    python src/scripts/run_workflow.py --mode batch-reflect        # infer.jsonl → reflect.jsonl
    python src/scripts/run_workflow.py --mode batch-curate         # reflect.jsonl → Playbook更新
"""

import argparse
import json
import sys
from pathlib import Path

from dotenv import load_dotenv

from src.application.agents.curator import CuratorAgent
from src.application.agents.generator import GeneratorAgent
from src.application.agents.reflector import ReflectorAgent
from src.common.config.settings import load_config
from src.common.defs.insight import ReflectionResult
from src.common.defs.trajectory import Trajectory
from src.common.di.container import Container
from src.common.lib.logging import getLogger
from src.components.dataset_loader.models import QuestionRecord

logger = getLogger(__name__)

DATASET = "jcommonsenseqa"
DATA_PATH = Path("data/datasets/jcommonsenseqa/train.jsonl")
DEFAULT_LIMIT = 5

RESULTS_DIR = Path("data/results/jcommonsenseqa")
INFER_OUTPUT = RESULTS_DIR / "infer.jsonl"
REFLECT_OUTPUT = RESULTS_DIR / "reflect.jsonl"


def parse_args() -> argparse.Namespace:
    """コマンドライン引数をパースする."""
    parser = argparse.ArgumentParser(
        description="JCommonsenseQAワークフロー実行",
    )
    parser.add_argument(
        "--mode",
        choices=["infer", "full", "batch-infer", "batch-reflect", "batch-curate"],
        default="full",
        help=(
            "infer: 推論+正解率のみ, full: フルパイプライン, "
            "batch-infer/batch-reflect/batch-curate: ステージ別バッチ実行 (default: full)"
        ),
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help=f"処理する問題数 (infer/fullのdefault: {DEFAULT_LIMIT}, batch系: 全件)",
    )
    return parser.parse_args()


def setup() -> Container:
    """DIコンテナを初期化して返す."""
    load_dotenv()
    config = load_config()
    container = Container()
    container.config.from_dict(config.model_dump())
    return container


def load_questions(path: Path, limit: int | None = None) -> list[QuestionRecord]:
    """JSONLファイルからQuestionRecordを読み込む. limitがNoneなら全件."""
    records: list[QuestionRecord] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            if limit is not None and len(records) >= limit:
                break
            records.append(QuestionRecord(**json.loads(line)))
    return records


def generate(generator: GeneratorAgent, record: QuestionRecord) -> Trajectory:
    """GeneratorAgentでクエリから回答を生成する."""
    query = record.to_query()
    return generator.run(query, DATASET)


def judge_answer(trajectory: Trajectory, record: QuestionRecord) -> bool:
    """生成回答に正解選択肢テキストが含まれているかで正誤判定する."""
    return record.correct_answer in trajectory.generated_answer


def build_test_report(is_correct: bool, record: QuestionRecord) -> str:
    """正誤判定結果からtest_report文字列を生成する."""
    if is_correct:
        return "正解"
    return f"不正解: 正解は「{record.correct_answer}」"


def reflect(
    reflector: ReflectorAgent,
    trajectory: Trajectory,
    record: QuestionRecord,
    test_report: str,
) -> ReflectionResult:
    """ReflectorAgentでTrajectoryを分析しReflectionResultを返す."""
    return reflector.run(
        trajectory=trajectory,
        ground_truth=record.correct_answer,
        test_report=test_report,
        dataset=DATASET,
    )


def curate(curator: CuratorAgent, reflection_result: ReflectionResult):
    """CuratorAgentでPlaybookを更新しCurationResultを返す."""
    return curator.run(
        reflection_result=reflection_result,
        dataset=DATASET,
    )


def save_infer_results(
    results: list[dict],
    path: Path = INFER_OUTPUT,
) -> None:
    """推論結果リストをJSONLで保存する."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False, default=str) + "\n")
    logger.info("Saved %d infer results to %s", len(results), path)


def load_infer_results(
    path: Path = INFER_OUTPUT,
    limit: int | None = None,
) -> list[dict]:
    """JSONLから推論結果を読み込む. trajectoryはTrajectoryに復元する."""
    results: list[dict] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            if limit is not None and len(results) >= limit:
                break
            record = json.loads(line)
            record["trajectory"] = Trajectory(**record["trajectory"])
            results.append(record)
    logger.info("Loaded %d infer results from %s", len(results), path)
    return results


def save_reflect_results(
    results: list[dict],
    path: Path = REFLECT_OUTPUT,
) -> None:
    """リフレクション結果リストをJSONLで保存する."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False, default=str) + "\n")
    logger.info("Saved %d reflect results to %s", len(results), path)


def load_reflect_results(
    path: Path = REFLECT_OUTPUT,
    limit: int | None = None,
) -> list[dict]:
    """JSONLからリフレクション結果を読み込む. reflection_resultはReflectionResultに復元する."""
    results: list[dict] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            if limit is not None and len(results) >= limit:
                break
            record = json.loads(line)
            record["reflection_result"] = ReflectionResult(
                **record["reflection_result"],
            )
            results.append(record)
    logger.info("Loaded %d reflect results from %s", len(results), path)
    return results


def run_infer(
    record: QuestionRecord,
    generator: GeneratorAgent,
) -> bool:
    """推論のみ実行し正誤を返す."""
    trajectory = generate(generator, record)
    if trajectory.status == "failure":
        logger.error("  Generation failed: %s", trajectory.error_message)
        return False

    is_correct = judge_answer(trajectory, record)

    logger.info("  生成回答: %s", trajectory.generated_answer[:80])
    logger.info("  正解: %s  判定: %s", record.correct_answer, "正解" if is_correct else "不正解")

    return is_correct


def run_full(
    record: QuestionRecord,
    generator: GeneratorAgent,
    reflector: ReflectorAgent,
    curator: CuratorAgent,
) -> bool:
    """フルパイプライン(Generate → Reflect → Curate)を実行し正誤を返す."""
    trajectory = generate(generator, record)
    if trajectory.status == "failure":
        logger.error("  Generation failed: %s", trajectory.error_message)
        return False

    is_correct = judge_answer(trajectory, record)
    test_report = build_test_report(is_correct, record)

    logger.info("  生成回答: %s", trajectory.generated_answer[:80])
    logger.info("  正解: %s  判定: %s", record.correct_answer, test_report)

    reflection_result = reflect(reflector, trajectory, record, test_report)
    logger.info(
        "  Reflection: insights=%d, bullet_evaluations=%d",
        len(reflection_result.insights),
        len(reflection_result.bullet_evaluations),
    )

    curation_result = curate(curator, reflection_result)
    logger.info(
        "  Curation: %s (bullets: %d -> %d)",
        curation_result.summary,
        curation_result.bullets_before,
        curation_result.bullets_after,
    )

    return is_correct


def run_batch_infer(
    questions: list[QuestionRecord],
    generator: GeneratorAgent,
) -> None:
    """全件推論してinfer.jsonlに保存する."""
    results: list[dict] = []
    correct_count = 0
    for i, record in enumerate(questions, 1):
        logger.info(
            "=== [%d/%d] q_id=%s: %s ===",
            i,
            len(questions),
            record.q_id,
            record.question[:50],
        )
        trajectory = generate(generator, record)
        if trajectory.status == "failure":
            logger.error("  Generation failed: %s", trajectory.error_message)
            is_correct = False
            test_report = "不正解: 生成失敗"
        else:
            is_correct = judge_answer(trajectory, record)
            test_report = build_test_report(is_correct, record)
            logger.info("  生成回答: %s", trajectory.generated_answer[:80])
            logger.info("  正解: %s  判定: %s", record.correct_answer, test_report)

        if is_correct:
            correct_count += 1
        results.append({
            "q_id": record.q_id,
            "correct_answer": record.correct_answer,
            "is_correct": is_correct,
            "test_report": test_report,
            "trajectory": trajectory.model_dump(mode="json"),
        })

    save_infer_results(results)
    accuracy = correct_count / len(questions) * 100 if questions else 0.0
    logger.info("=" * 60)
    logger.info(
        "Batch infer: %d / %d correct (%.1f%%)",
        correct_count,
        len(questions),
        accuracy,
    )
    logger.info("=" * 60)


def run_batch_reflect(
    reflector: ReflectorAgent,
    limit: int | None = None,
) -> None:
    """infer.jsonlを読み込み全件リフレクションしてreflect.jsonlに保存する."""
    infer_records = load_infer_results(limit=limit)
    results: list[dict] = []
    for i, rec in enumerate(infer_records, 1):
        q_id = rec["q_id"]
        trajectory = rec["trajectory"]
        logger.info(
            "=== [%d/%d] q_id=%s ===",
            i,
            len(infer_records),
            q_id,
        )
        reflection_result = reflector.run(
            trajectory=trajectory,
            ground_truth=rec["correct_answer"],
            test_report=rec["test_report"],
            dataset=DATASET,
        )
        logger.info(
            "  Reflection: insights=%d, bullet_evaluations=%d",
            len(reflection_result.insights),
            len(reflection_result.bullet_evaluations),
        )
        results.append({
            "q_id": q_id,
            "reflection_result": reflection_result.model_dump(mode="json"),
        })

    save_reflect_results(results)


def run_batch_curate(
    curator: CuratorAgent,
    limit: int | None = None,
) -> None:
    """reflect.jsonlを読み込み全件キュレーションする."""
    reflect_records = load_reflect_results(limit=limit)
    for i, rec in enumerate(reflect_records, 1):
        q_id = rec["q_id"]
        logger.info(
            "=== [%d/%d] q_id=%s ===",
            i,
            len(reflect_records),
            q_id,
        )
        curation_result = curate(curator, rec["reflection_result"])
        logger.info(
            "  Curation: %s (bullets: %d -> %d)",
            curation_result.summary,
            curation_result.bullets_before,
            curation_result.bullets_after,
        )


def print_summary(results: list[bool]) -> None:
    """正解率のサマリーをログ出力する."""
    correct = sum(results)
    total = len(results)
    accuracy = correct / total * 100 if total > 0 else 0.0
    logger.info("=" * 60)
    logger.info("Results: %d / %d correct (%.1f%%)", correct, total, accuracy)
    logger.info("=" * 60)


def main() -> None:
    """メイン関数."""
    args = parse_args()
    limit = args.limit if args.limit is not None else DEFAULT_LIMIT

    try:
        container = setup()

        if args.mode in ("infer", "full"):
            logger.info("Mode: %s, Limit: %d", args.mode, limit)
            questions = load_questions(DATA_PATH, limit)
            logger.info("Loaded %d questions from %s", len(questions), DATA_PATH)

            generator = container.generator_agent()
            reflector = container.reflector_agent() if args.mode == "full" else None
            curator = container.curator_agent() if args.mode == "full" else None

            results: list[bool] = []
            for i, record in enumerate(questions, 1):
                logger.info(
                    "=== [%d/%d] q_id=%s: %s ===",
                    i,
                    len(questions),
                    record.q_id,
                    record.question[:50],
                )

                if args.mode == "infer":
                    is_correct = run_infer(record, generator)
                else:
                    is_correct = run_full(record, generator, reflector, curator)

                results.append(is_correct)

            print_summary(results)

        elif args.mode == "batch-infer":
            questions = load_questions(DATA_PATH, args.limit)
            logger.info(
                "Mode: batch-infer, Questions: %d",
                len(questions),
            )
            generator = container.generator_agent()
            run_batch_infer(questions, generator)

        elif args.mode == "batch-reflect":
            logger.info("Mode: batch-reflect")
            reflector = container.reflector_agent()
            run_batch_reflect(reflector, limit=args.limit)

        elif args.mode == "batch-curate":
            logger.info("Mode: batch-curate")
            curator = container.curator_agent()
            run_batch_curate(curator, limit=args.limit)

    except Exception as e:
        logger.exception("Workflow execution failed: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
