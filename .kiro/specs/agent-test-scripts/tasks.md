# Implementation Plan: Agent Test Scripts

## Overview

3つのエージェント（Generator、Reflector、Curator）の動作確認スクリプトをsrc/scripts/ディレクトリに作成する.
各スクリプトは既存パターンに準拠し、DIコンテナ経由でエージェントを取得してLLM APIを呼び出す.

## Tasks

- [x] 1. Generator動作確認スクリプトの作成
  - [x] 1.1 src/scripts/run_generator.py を作成する
    - sys.path設定、dotenv読み込み、src.common.lib.logging.getLogger()の共通初期化
    - DIコンテナの初期化と設定注入（load_config → container.config.from_dict）
    - container.generator_agent() でエージェント取得
    - サンプルクエリ（appworldデータセット）でagent.run()を呼び出し
    - Trajectoryのquery、status、generated_answer、reasoning_steps、used_bullet_idsを表示
    - try-exceptでエラーハンドリング（ログ出力 + sys.exit(1)）
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 4.1, 4.2, 4.3, 4.4, 4.5_

- [x] 2. Reflector動作確認スクリプトの作成
  - [x] 2.1 src/scripts/run_reflector.py を作成する
    - 共通初期化処理（1.1と同じパターン）
    - まずGeneratorでTrajectoryを生成（Reflectorの入力として必要）
    - container.reflector_agent() でReflectorエージェント取得
    - サンプルのground_truth、test_reportを用意
    - reflector.run(trajectory, ground_truth, test_report, dataset) を呼び出し
    - ReflectionResultの各Insight（key_insight、reasoning、error_identification）を表示
    - 各BulletEvaluation（bullet_id、tag、reason）を表示
    - try-exceptでエラーハンドリング
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 4.1, 4.2, 4.3, 4.4, 4.5_

- [x] 3. Curator動作確認スクリプトの作成
  - [x] 3.1 src/scripts/run_curator.py を作成する
    - 共通初期化処理（1.1と同じパターン）
    - ダミーのReflectionResult（Insightを含む）を構築
    - container.curator_agent() でCuratorエージェント取得
    - curator.run(reflection_result, dataset) を呼び出し
    - CurationResultの各DeltaContextItem（type、section、content、reasoning）を表示
    - bullets_before、bullets_after、summaryを表示
    - try-exceptでエラーハンドリング
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 4.1, 4.2, 4.3, 4.4, 4.5_

- [x] 4. カスタムlogging実装の作成
  - src/common/lib/logging.py にgetLogger()関数を実装
  - 自動的にlogging.basicConfig()を実行してロガーを返す

- [x] 5. スクリプトのsrc/scripts/への移動
  - scriptsディレクトリをsrc/配下に移動
  - 全スクリプトでカスタムloggingを使用するように更新

- [x] 6. 最終チェックポイント
  - 3つのスクリプトが正しい構文で作成されていることを確認済み
  - 既存スクリプトのパターン（sys.path、logging、main()、if __name__）に準拠していることを確認済み
  - カスタムlogging（getLogger）の使用を確認済み

## Bug Fixes

- [x] 7. DIコンテナの設定アクセス方法の修正 (2026-02-09)
  - [x] 7.1 `src/common/di/container.py` でブラケット記法を使用
    - `config.llm.provider` → `config.llm["provider"]`
    - `config.llm.model` → `config.llm["model"]`
    - `config.llm.api_key` → `config.llm["api_key"]`
    - _Issue: `provider` キー名が dependency_injector で衝突_

- [x] 8. HybridSearch引数順序の修正 (2026-02-09)
  - [x] 8.1 `src/application/agents/generator.py:214` の引数順序を修正
    - `search(playbook, search_query)` → `search(search_query, playbook)`
    - _Issue: メソッドシグネチャと引数順序が不一致_

- [x] 9. 不要スクリプトの削除 (2026-02-09)
  - [x] 9.1 `src/scripts/verify_jcommonsenseqa.py` を削除
  - [x] 9.2 `src/scripts/example_usage.py` を削除
  - [x] 9.3 `build/lib/scripts/` 配下の同名ファイルも削除

## Notes

- PoCフェーズのため、自動テストは不要
- 各スクリプトは独立して実行可能
- LLM APIを実際に呼び出すため、.envにOPENAI_API_KEYの設定が必要
- appworldデータセットを使用（Playbookが存在しない場合は空のPlaybookで動作）
