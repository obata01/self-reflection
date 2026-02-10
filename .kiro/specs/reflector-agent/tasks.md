# 実装計画: Reflectorエージェント

## 概要

Reflectorエージェントの実装を、データモデル定義 → プロンプト管理 → エージェント本体 → DI統合の順で進める. 各ステップは前のステップの成果物に依存する. GeneratorAgentと同様の構成・粒度で実装する.

## タスク

- [ ] 1. Insight関連データモデルの定義
  - [ ] 1.1 `src/common/defs/insight.py` にInsight、BulletEvaluation、ReflectionResultモデルを作成する
    - Insight: reasoning, error_identification, root_cause_analysis, correct_approach, key_insight（全てstr）
    - BulletEvaluation: bullet_id（str）, tag（Literal["helpful", "harmful", "neutral"]）, reason（str）
    - ReflectionResult: insights（list[Insight]）, bullet_evaluations（list[BulletEvaluation]）, trajectory_query（str）, trajectory_dataset（str）, iteration_count（int, デフォルト1）
    - 全モデルはPydantic BaseModelを継承
    - `src/common/defs/__init__.py` にInsight, BulletEvaluation, ReflectionResultをエクスポート
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 2.1, 2.2, 2.3, 3.1, 3.2, 3.3_
  - [ ]* 1.2 データモデルのプロパティテストを作成する
    - `tests/test_insight.py` に配置
    - **Property 1: データモデルシリアライゼーションのラウンドトリップ**
    - **Validates: Requirements 1.1, 1.3, 1.4, 2.1, 2.3, 3.1, 3.3**
    - **Property 2: データモデルの型バリデーション**
    - **Validates: Requirements 1.2, 2.2, 3.2**

- [ ] 2. Reflector用プロンプトテンプレート管理の実装
  - [ ] 2.1 デフォルトプロンプトテンプレートファイルを作成する
    - `prompts/reflector/default.txt` にデフォルトテンプレートを配置
    - テンプレート変数: `{generated_answer}`, `{ground_truth}`, `{test_report}`, `{reasoning_steps}`, `{used_bullets}`, `{previous_insights}`
    - _Requirements: 4.4_
  - [ ] 2.2 `src/application/agents/reflector.py` にReflectorPromptBuilderクラスを実装する
    - コンストラクタで `prompts_dir` を受け取る（デフォルト: "prompts/reflector"）
    - `build(trajectory, ground_truth, test_report, used_bullets, dataset, previous_insights)` メソッド: テンプレートにTrajectory情報とBullet内容を注入してプロンプト文字列を返す
    - `build_evaluation_prompt(trajectory, ground_truth, bullet)` メソッド: Bullet評価用プロンプトを構築する
    - `_load_template(dataset)` メソッド: データセット固有テンプレートを優先し、なければデフォルトを使用. デフォルトもなければハードコードのフォールバック
    - _Requirements: 4.1, 4.2, 4.3, 4.4_
  - [ ]* 2.3 ReflectorPromptBuilderのプロパティテストを作成する
    - `tests/test_reflector.py` に配置
    - **Property 3: プロンプト構築時のコンテンツ包含**
    - **Validates: Requirements 4.2**

- [ ] 3. ReflectorAgentの実装
  - [ ] 3.1 `src/application/agents/reflector.py` にReflectorAgentクラスを実装する
    - コンストラクタで LLMClient, ReflectorPromptBuilder, PlaybookStore を受け取る
    - `run(trajectory, ground_truth, test_report, dataset, max_iterations=1)` メソッド: Playbook読み込み → Bullet解決 → プロンプト構築 → LLM分析 → Insight抽出 → Bullet評価 → ReflectionResult生成
    - `_extract_insights(llm_response)` メソッド: LLM応答のJSON文字列からInsightリストをパース. パース失敗時は空リストを返す
    - `_evaluate_bullets(trajectory, ground_truth, used_bullets)` メソッド: 各BulletについてLLMで評価を実行しBulletEvaluationリストを返す
    - `_resolve_bullets(bullet_ids, playbook)` メソッド: Bullet IDリストからBulletオブジェクトを取得. 存在しないIDはスキップ
    - LLMリクエスト失敗時は空のInsightsリストを持つReflectionResultを返す（例外を伝播させない）
    - used_bullet_idsが空の場合はBullet評価をスキップ
    - max_iterations > 1の場合は反復改善を実行（前回のInsightsを次回の入力に含める）
    - _Requirements: 5.1, 5.2, 5.3, 6.1, 6.2, 6.3, 7.1, 7.2, 7.3, 8.1, 8.2, 8.3_
  - [ ]* 3.2 ReflectorAgentのプロパティテストを作成する
    - `tests/test_reflector.py` に配置
    - **Property 4: Insight JSONパースの正当性**
    - **Validates: Requirements 5.2**

- [ ] 4. チェックポイント - 動作確認
  - ReflectorAgentの単体動作を確認する. テストが通ること、または手動実行で期待通りの動作を確認する. 問題があればユーザーに確認する.

- [ ] 5. DIコンテナへの統合
  - [ ] 5.1 `src/common/di/container.py` にReflectorAgent関連のプロバイダを追加する
    - ReflectorPromptBuilderをSingletonプロバイダとして登録
    - ReflectorAgentをFactoryプロバイダとして登録
    - 既存のllm_client, playbook_storeを依存として注入
    - _Requirements: 9.1, 9.2_
  - [ ] 5.2 `src/application/agents/__init__.py` にReflectorAgentをエクスポートする
    - _Requirements: 9.1_

- [ ] 6. 最終チェックポイント - 全体動作確認
  - 全てのテストが通ること、またはDIコンテナ経由でReflectorAgentが正しく動作することを確認する. 問題があればユーザーに確認する.

## 備考

- `*` 付きのタスクはオプションであり、PoCフェーズではスキップ可能
- 各タスクは特定の要件にトレーサビリティを持つ
- チェックポイントで段階的に動作を検証する
- プロパティテストはhypothesisライブラリを使用する
