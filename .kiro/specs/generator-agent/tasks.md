# 実装計画: Generatorエージェント

## 概要

Generatorエージェントの実装を、データモデル定義 → プロンプト管理 → エージェント本体 → DI統合の順で進める. 各ステップは前のステップの成果物に依存する.

## タスク

- [ ] 1. Trajectoryデータモデルの定義
  - [ ] 1.1 `src/common/defs/trajectory.py` にTrajectoryモデルを作成する
    - Pydantic BaseModelを継承
    - フィールド: query, dataset, generated_answer, reasoning_steps, used_bullet_ids, status, error_message, created_at
    - statusはLiteral["success", "failure"]
    - error_messageはOptional（デフォルトNone）
    - created_atはField(default_factory=datetime.now)
    - `src/common/defs/__init__.py` を作成しTrajectoryをエクスポート
    - _Requirements: 1.1, 1.2_
  - [ ]* 1.2 Trajectoryモデルのプロパティテストを作成する
    - `tests/test_trajectory.py` に配置
    - **Property 1: Trajectoryシリアライゼーションのラウンドトリップ**
    - **Validates: Requirements 1.1, 1.3, 1.4**
    - **Property 2: Trajectoryの型バリデーション**
    - **Validates: Requirements 1.2**

- [ ] 2. プロンプトテンプレート管理の実装
  - [ ] 2.1 デフォルトプロンプトテンプレートファイルを作成する
    - `prompts/generator/default.txt` にデフォルトテンプレートを配置
    - テンプレート変数: `{context}`, `{query}`
    - _Requirements: 2.4_
  - [ ] 2.2 `src/application/agents/generator.py` にPromptBuilderクラスを実装する
    - コンストラクタで `prompts_dir` を受け取る（デフォルト: "prompts/generator"）
    - `build(query, bullets, dataset)` メソッド: テンプレートにクエリとBullet内容を注入してプロンプト文字列を返す
    - `_load_template(dataset)` メソッド: データセット固有テンプレートを優先し、なければデフォルトを使用. デフォルトもなければハードコードのフォールバック
    - _Requirements: 2.1, 2.2, 2.3, 2.4_
  - [ ]* 2.3 PromptBuilderのプロパティテストを作成する
    - `tests/test_generator.py` に配置
    - **Property 3: プロンプト構築時のコンテンツ包含**
    - **Validates: Requirements 2.2, 3.2**

- [ ] 3. GeneratorAgentの実装
  - [ ] 3.1 `src/application/agents/generator.py` にGeneratorAgentクラスを実装する
    - コンストラクタで PlaybookStore, HybridSearch, LLMClient, PromptBuilder を受け取る
    - `run(query, dataset)` メソッド: Playbook読み込み → 検索 → プロンプト構築 → LLM実行 → Trajectory生成
    - LLMリクエスト失敗時はstatus="failure"のTrajectoryを返す（例外を伝播させない）
    - 検索失敗時も同様にstatus="failure"のTrajectoryを返す
    - used_bullet_idsに検索結果のBullet IDを記録する
    - _Requirements: 3.1, 3.2, 3.3, 4.1, 4.2, 4.3, 5.1, 5.2, 5.3_
  - [ ]* 3.2 GeneratorAgentのプロパティテストを作成する
    - `tests/test_generator.py` に配置
    - **Property 4: LLM応答からのTrajectory構造化**
    - **Validates: Requirements 4.2, 5.3**

- [ ] 4. チェックポイント - 動作確認
  - GeneratorAgentの単体動作を確認する. テストが通ること、または手動実行で期待通りの動作を確認する. 問題があればユーザーに確認する.

- [ ] 5. DIコンテナへの統合
  - [ ] 5.1 `src/common/di/container.py` にGeneratorAgent関連のプロバイダを追加する
    - PromptBuilderをSingletonプロバイダとして登録
    - GeneratorAgentをFactoryプロバイダとして登録
    - 既存のplaybook_store, hybrid_search, llm_clientを依存として注入
    - _Requirements: 6.1, 6.2_
  - [ ] 5.2 `src/application/agents/__init__.py` にGeneratorAgentをエクスポートする
    - _Requirements: 6.1_

- [ ] 6. 最終チェックポイント - 全体動作確認
  - 全てのテストが通ること、またはDIコンテナ経由でGeneratorAgentが正しく動作することを確認する. 問題があればユーザーに確認する.

## 備考

- `*` 付きのタスクはオプションであり、PoCフェーズではスキップ可能
- 各タスクは特定の要件にトレーサビリティを持つ
- チェックポイントで段階的に動作を検証する
- プロパティテストはhypothesisライブラリを使用する
