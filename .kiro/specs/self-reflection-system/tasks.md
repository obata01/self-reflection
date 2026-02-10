# Implementation Plan: Self-Reflection System（基盤構築）

## Overview

ACE自己内省システムの基盤を段階的に構築する. データモデル → 永続化 → 検索 → LLMクライアント → 設定・DI → ワークフロー → FastAPI → 動作確認の順で実装する. componentsは他に依存しない独立したコンポーネントとして構築し、applicationがcomponentsをimportしてビジネスロジックを組み立てる. FastAPIは `src/main.py` に直接配置し、presentation層は設けない.

## Tasks

- [ ] 1. データモデルとPlaybookStoreの実装
  - [ ] 1.1 Bullet, PlaybookMetadata, Playbook, DeltaContextItemのPydanticモデルを作成する
    - `src/components/playbook_store/models.py` に定義
    - Bulletにconfidence_scoreのcomputed_fieldを実装
    - `src/components/playbook_store/__init__.py` を作成
    - 全クラスにGoogle Style Docstring（日本語）を記述
    - _Requirements: 1.1, 1.2, 1.3, 1.4_
  - [ ] 1.2 PlaybookStoreを実装する
    - `src/components/playbook_store/store.py` に実装
    - JSON形式での保存・読み込み、存在しないファイルの場合は空Playbook返却
    - `data/playbooks/` ディレクトリを作成（.gitkeep）
    - _Requirements: 2.1, 2.2, 2.3, 2.4_
  - [ ]* 1.3 Playbookシリアライゼーションのラウンドトリッププロパティテストを作成する
    - `tests/test_playbook_store.py` に配置
    - **Property 3: Playbookシリアライゼーションのラウンドトリップ**
    - **Validates: Requirements 2.1, 2.2, 2.3**

- [ ] 2. セクション定義の作成
  - [ ] 2.1 セクション定義ファイルとローダーを作成する
    - `config/sections.yaml` にappworld等のサンプルセクション定義を記述
    - `src/common/config/section_loader.py` にSectionDefinitionモデルとSectionLoaderを実装
    - `src/common/__init__.py`, `src/common/config/__init__.py` を作成
    - _Requirements: 3.1, 3.2_

- [ ] 3. ハイブリッド検索の実装
  - [ ] 3.1 EmbeddingClientを実装する
    - `src/components/hybrid_search/embedding_client.py` に実装
    - LangChainのEmbeddingsモデルをラップ
    - `src/components/hybrid_search/__init__.py` を作成
    - _Requirements: 4.1_
  - [ ] 3.2 SearchQuery, SearchResultモデルを作成する
    - `src/components/hybrid_search/models.py` に定義
    - _Requirements: 1.5, 1.6_
  - [ ] 3.3 HybridSearchを実装する
    - `src/components/hybrid_search/search.py` に実装
    - Numpyベクトル近傍探索 + rank-bm25によるBM25検索
    - スコア統合、フィルタリング、top_k件の降順ソート返却
    - pyproject.tomlにrank-bm25を依存追加
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7_
  - [ ]* 3.4 検索フィルタリングとソートのプロパティテストを作成する
    - `tests/test_hybrid_search.py` に配置
    - **Property 5: 検索結果のフィルタリング**
    - **Property 6: 検索結果のソートとtop_k制約**
    - **Validates: Requirements 4.4, 4.5, 4.6**

- [ ] 4. LLMクライアントの実装
  - [ ] 4.1 LLMClientとファクトリ関数を実装する
    - `src/components/llm_client/client.py` に実装
    - create_chat_model ファクトリ（openai / bedrock / azure対応）
    - invoke, invoke_with_templateメソッド
    - エラー時のログ記録と例外送出
    - `src/components/llm_client/__init__.py` を作成
    - _Requirements: 5.1, 5.2, 5.3_

- [ ] 5. Checkpoint - componentsの動作確認
  - 各componentが独立して動作することを確認する.
  - 問題があればユーザーに確認する.

- [ ] 6. 設定管理とDIコンテナの構築
  - [ ] 6.1 設定モデルと読み込みロジックを実装する
    - `src/common/config/settings.py` にAppConfig等のdataclassを定義
    - 環境変数からの読み込み（load_config関数）
    - _Requirements: 6.2_
  - [ ] 6.2 DIコンテナを実装する
    - `src/common/di/container.py` にdependency-injectorのDeclarativeContainerを定義
    - PlaybookStore, HybridSearch, LLMClient, EmbeddingClientをプロバイダとして登録
    - `src/common/di/__init__.py` を作成
    - _Requirements: 6.1, 6.3_

- [ ] 7. LangGraphワークフロー基盤の実装
  - [ ] 7.1 ワークフローの状態定義とReflectionWorkflowを実装する
    - `src/application/workflows/reflection_workflow.py` に実装
    - WorkflowState（TypedDict）の定義
    - load_playbook → search → generate の3ノード構成
    - `src/application/__init__.py`, `src/application/workflows/__init__.py` を作成
    - _Requirements: 7.1, 7.2, 7.3, 7.4_

- [ ] 8. FastAPIアプリケーション基盤の実装
  - [ ] 8.1 APIスキーマを作成する
    - `src/common/schema/api.py` にWorkflowRequest, WorkflowResponseを定義
    - `src/common/schema/__init__.py` を作成
    - _Requirements: 9.3_
  - [ ] 8.2 FastAPIアプリケーションとエンドポイントを実装する
    - `src/main.py` にFastAPIアプリケーションを実装（presentation層は設けない）
    - GET /health（ヘルスチェック）
    - POST /workflow/run（ワークフロー実行）
    - DIコンテナとの統合
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

- [ ] 9. 統合と動作確認
  - [ ] 9.1 動作確認用スクリプトを作成する
    - 手動実行可能なPythonファイルとして作成
    - DIコンテナの初期化
    - Playbookの読み込み・検索・保存の一連の流れ
    - LLMへのリクエスト送信と応答表示
    - ワークフローの実行
    - _Requirements: 8.1, 8.2, 8.3_
  - [ ] 9.2 各モジュールの__init__.pyとパッケージ構成を整備する
    - 必要な__init__.pyファイルの作成
    - importパスの整理

- [ ] 10. Final checkpoint - 全体の動作確認
  - 動作確認スクリプトを実行し、LLMへのリクエスト送信・応答取得が正常に動作することを確認する.
  - FastAPIのヘルスチェックとワークフロー実行エンドポイントの動作を確認する.
  - 問題があればユーザーに確認する.

## Notes

- タスクに `*` が付いているものはオプション（PoCフェーズのため省略可能）
- 各タスクは前のタスクの成果物に依存する順序で構成
- チェックポイントで段階的に動作確認を行う
- pyproject.tomlへのrank-bm25依存追加が必要（タスク3.3で実施）
- テストコードは `tests/` ディレクトリに配置する（`src/` 内には置かない）
- FastAPIは `src/main.py` に直接配置する（presentation層は設けない）
- 全てのクラスとパブリックメソッドにGoogle Style Docstring（日本語）を記述する
