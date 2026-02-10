# 実装計画: Curatorエージェント

## 概要

Curatorエージェントの実装を、データモデル定義 → プロンプト管理 → マージロジック → エージェント本体 → DI統合の順で進める. 各ステップは前のステップの成果物に依存する. GeneratorAgent、ReflectorAgentと同様の構成・粒度で実装する.

## タスク

- [ ] 1. CurationResultデータモデルの定義
  - [ ] 1.1 `src/common/defs/curation.py` にCurationResultモデルを作成する
    - CurationResult: deltas（list[DeltaContextItem]）, bullets_before（int）, bullets_after（int）, summary（str）
    - Pydantic BaseModelを継承
    - `src/common/defs/__init__.py` にCurationResultをエクスポート追加
    - _Requirements: 1.1, 1.2, 1.3_
  - [ ]* 1.2 CurationResultのプロパティテストを作成する
    - `tests/test_curation.py` に配置
    - **Property 1: CurationResultシリアライゼーションのラウンドトリップ**
    - **Validates: Requirements 1.1, 1.3**
    - **Property 2: CurationResultの型バリデーション**
    - **Validates: Requirements 1.2**

- [ ] 2. Curator用プロンプトテンプレート管理の実装
  - [ ] 2.1 デフォルトプロンプトテンプレートファイルを作成する
    - `prompts/curator/default.txt` にデフォルトテンプレートを配置
    - テンプレート変数: `{insights}`, `{bullets}`, `{sections}`
    - _Requirements: 6.4_
  - [ ] 2.2 `src/application/agents/curator.py` にCuratorPromptBuilderクラスを実装する
    - コンストラクタで `prompts_dir` を受け取る（デフォルト: "prompts/curator"）
    - `build(insights, bullets, sections, dataset)` メソッド: テンプレートにInsights、Bullet一覧、セクション定義を注入してプロンプト文字列を返す
    - `_load_template(dataset)` メソッド: データセット固有テンプレートを優先し、なければデフォルトを使用. デフォルトもなければハードコードのフォールバック
    - _Requirements: 6.1, 6.2, 6.3, 6.4_
  - [ ]* 2.3 CuratorPromptBuilderのプロパティテストを作成する
    - `tests/test_curator.py` に配置
    - **Property 7: プロンプト構築時のコンテンツ包含**
    - **Validates: Requirements 6.2**

- [ ] 3. Playbook マージロジックの実装
  - [ ] 3.1 `src/application/agents/curator.py` にマージ関連メソッドを実装する
    - `_apply_bullet_evaluations(bullet_evaluations, playbook)` メソッド: BulletEvaluationに基づいてhelpful/harmfulカウンターを更新. 存在しないbullet_idはスキップ
    - `_merge_deltas(deltas, playbook)` メソッド: ADD（新Bullet生成・ID付与・追加）、UPDATE（content/searchable_text更新）、DELETE（Bullet削除）を実行. 存在しないbullet_idの操作はスキップしログ記録
    - `_generate_bullet_id()` メソッド: UUID等で一意のIDを生成
    - `_load_sections(dataset)` メソッド: config/sections.yamlからセクション定義を読み込み. 存在しない場合は空リスト
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 5.1, 5.2, 5.3, 5.4, 8.1, 8.2_
  - [ ]* 3.2 マージロジックのプロパティテストを作成する
    - `tests/test_curator.py` に配置
    - **Property 3: BulletEvaluation適用によるカウンター更新**
    - **Validates: Requirements 4.1, 4.2, 4.3**
    - **Property 4: ADD操作によるBullet追加**
    - **Validates: Requirements 5.1**
    - **Property 5: UPDATE操作によるBullet更新**
    - **Validates: Requirements 5.2**
    - **Property 6: DELETE操作によるBullet削除**
    - **Validates: Requirements 5.3**

- [ ] 4. チェックポイント - マージロジックの動作確認
  - マージロジック（カウンター更新、ADD/UPDATE/DELETE）の単体動作を確認する. テストが通ること、または手動実行で期待通りの動作を確認する. 問題があればユーザーに確認する.

- [ ] 5. CuratorAgentの実装
  - [ ] 5.1 `src/application/agents/curator.py` にCuratorAgentクラスを実装する
    - コンストラクタで LLMClient, CuratorPromptBuilder, PlaybookStore を受け取る
    - `run(reflection_result, dataset)` メソッド: Playbook読み込み → セクション定義読み込み → Delta生成（LLM使用） → カウンター更新 → マージ → 永続化 → CurationResult生成
    - `_generate_deltas(insights, playbook, sections, dataset)` メソッド: LLMにプロンプトを送信しDeltaContextItemリストを生成. Insightsが空なら空リストを返す. LLM失敗時・パース失敗時は空リストを返す
    - LLMリクエスト失敗時は空のDeltaContextItemリストを持つCurationResultを返す（例外を伝播させない）
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 3.1, 3.2, 5.5, 7.1, 7.2, 7.3, 8.3_

- [ ] 6. DIコンテナへの統合
  - [ ] 6.1 `src/common/di/container.py` にCuratorAgent関連のプロバイダを追加する
    - CuratorPromptBuilderをSingletonプロバイダとして登録
    - CuratorAgentをFactoryプロバイダとして登録
    - 既存のllm_client, playbook_storeを依存として注入
    - _Requirements: 9.1, 9.2_
  - [ ] 6.2 `src/application/agents/__init__.py` にCuratorAgentをエクスポートする
    - _Requirements: 9.1_

- [ ] 7. 最終チェックポイント - 全体動作確認
  - 全てのテストが通ること、またはDIコンテナ経由でCuratorAgentが正しく動作することを確認する. 問題があればユーザーに確認する.

## 備考

- `*` 付きのタスクはオプションであり、PoCフェーズではスキップ可能
- 各タスクは特定の要件にトレーサビリティを持つ
- チェックポイントで段階的に動作を検証する
- プロパティテストはhypothesisライブラリを使用する
- DeltaContextItemモデルは既にplaybook_store/models.pyに存在するため新規作成は不要
