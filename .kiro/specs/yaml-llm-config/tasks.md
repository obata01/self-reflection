# 実装計画: YAML LLMクライアント設定

## 概要

`config/app.yaml` によるLLMクライアント設定の一元管理を実装する. Pydanticスキーマ定義 → YAMLローダー → 環境変数解決 → レジストリ構築 → DIコンテナ拡張の順に段階的に進める.

## タスク

- [ ] 1. Pydanticスキーマとapp.yamlの作成
  - [ ] 1.1 `src/common/schema/llm_config.py` にPydanticモデルを定義する
    - `ChatClientEntry`（name, config: dict[str, Any], default_params: dict[str, Any]）
    - `ChatClientsConfig`（bedrock, azure, openai の各リスト）
    - `LLMsConfig`（chat_clients）
    - `AppYamlConfig`（llms）
    - _Requirements: 1.2, 2.1, 2.4, 2.5_
  - [ ] 1.2 `config/app.yaml` にサンプルLLMクライアント設定を作成する
    - bedrock（sonnet, haiku）、azure（gpt-4o, gpt-4.1, gpt-4.1-mini）、openaiの定義
    - _Requirements: 1.1, 1.3, 1.4, 1.5_
  - [ ]* 1.3 Pydanticスキーマのプロパティテストを書く
    - **Property 2: 有効な設定のバリデーション通過**
    - **Validates: Requirements 1.2, 2.2, 2.4**
    - **Property 3: 不正な設定のバリデーション拒否**
    - **Validates: Requirements 2.3**

- [ ] 2. YAMLローダーと環境変数解決の実装
  - [ ] 2.1 `src/common/config/app_config_loader.py` にAppConfigLoaderクラスを実装する
    - `load()`: YAML読み込み → Pydanticモデル変換
    - `resolve_env_vars()`: `_env` サフィックスフィールドの環境変数解決
    - FileNotFoundError、yaml.YAMLErrorのエラーハンドリング
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 4.1, 4.2, 4.3_
  - [ ]* 2.2 環境変数解決のプロパティテストを書く
    - **Property 4: 環境変数解決とキー名変換**
    - **Validates: Requirements 4.1, 4.3**
  - [ ]* 2.3 YAMLラウンドトリップのプロパティテストを書く
    - **Property 1: YAML設定のラウンドトリップ**
    - **Validates: Requirements 3.1**

- [ ] 3. チェックポイント - スキーマとローダーの動作確認
  - 全テストが通ることを確認し、不明点があればユーザーに質問する.

- [ ] 4. ChatModelレジストリとDIコンテナ拡張
  - [ ] 4.1 `src/common/config/app_config_loader.py` に `build_chat_model_registry` 関数を追加する
    - AppYamlConfigから全ChatModelインスタンスを生成
    - プロバイダ別のイテレーション、環境変数解決、Noneフィルタリング
    - 既存の `create_chat_model` ファクトリを活用
    - _Requirements: 5.1, 5.6, 6.1, 6.2_
  - [ ] 4.2 `src/common/di/container.py` を拡張する
    - `app_config_loader`、`app_yaml_config`、`chat_model_registry` プロバイダを追加
    - `get_chat_model(name)` と `get_llm_client(name)` メソッドを追加
    - 既存の `chat_model` / `llm_client` プロバイダは後方互換性のため維持
    - _Requirements: 5.2, 5.3, 5.4, 5.5_
  - [ ]* 4.3 Noneフィルタリングのプロパティテストを書く
    - **Property 7: Noneパラメータのフィルタリング**
    - **Validates: Requirements 6.2**

- [ ] 5. main.pyの更新と結合
  - [ ] 5.1 `src/main.py` の `create_app` を更新し、YAML設定ベースのコンテナ初期化を追加する
    - AppConfigLoaderによるYAML読み込みをコンテナ初期化フローに組み込む
    - _Requirements: 5.1, 5.5_

- [ ] 6. 最終チェックポイント - 全体の動作確認
  - 全テストが通ることを確認し、不明点があればユーザーに質問する.

## 備考

- `*` 付きのタスクはオプションでスキップ可能
- 各タスクは要件へのトレーサビリティを持つ
- チェックポイントで段階的に検証を行う
- プロパティテストはHypothesisライブラリを使用
- ユニットテストとプロパティテストは `tests/test_llm_config.py` に配置
