# Requirements Document: Self-Reflection System（基盤構築）

## Introduction

ACE（Agentic Context Engineering）フレームワークに基づく自己内省システムの基盤を構築する.
本スペックではアプリケーション基盤（DIコンテナ、LangGraph基盤、LLMリクエスト処理、Playbook永続化、ハイブリッド検索、FastAPI）の構築をスコープとする.
各エージェント（Generator / Reflector / Curator）の実装は次のスペックで行う.
現在はPoC（概念実証）フェーズであり、動作確認は手動実行やスクリプトベースで行う.
FastAPIは `src/main.py` に直接配置し、presentation層は設けない.

## Goals

- Playbookの永続化（PlaybookStore）とデータモデルを実装する
- ハイブリッド検索（Numpyベクトル近傍探索 + BM25）の基盤を構築する
- LangChainを使用したLLMリクエスト処理の基盤を構築する（プロバイダ切り替え可能）
- LangGraphワークフローの基盤（ノード定義・接続の仕組み）を構築する
- dependency-injectorによるDIコンテナを構築する
- FastAPI + Uvicornによるアプリケーション基盤を構築し、APIからワークフローを実行可能にする
- 上記を統合し、PythonスクリプトまたはAPI経由でLLMへのリクエストを送り何かしら生成できる状態にする

## Non-goals

- 各エージェント（Generator / Reflector / Curator）の本格的な実装（次のスペック）
- Web UIの構築
- 本番環境向けのスケーラビリティ・高可用性
- 網羅的なテストコードの整備（PoCフェーズのため最低限）
- AutoManual/H²R研究ベースのInsightフォーマットへの拡張
- 高度なDDDパターン（Repository Protocol等）の適用

## Glossary

- **Playbook**: 知識ベース全体. Bulletのコンテナ. データセットごとにJSONファイルで管理される
- **Bullet**: 個別の知識単位. helpful/harmfulカウンターによる信頼度スコアを持つ
- **Section**: Bulletの分類カテゴリ. データセットごとに設定ファイルで定義可能
- **Delta_Context_Item**: Curatorが生成するPlaybookへの更新差分（ADD/UPDATE/DELETE）
- **Hybrid_Search**: Numpyベクトル近傍探索とBM25全文検索を組み合わせた検索方式
- **Workflow**: LangGraphで定義されるエージェント間の処理フロー
- **DI_Container**: dependency-injectorで構築する依存性注入コンテナ
- **LLM_Client**: LangChainを使用したLLMリクエスト処理クライアント
- **FastAPI_App**: FastAPI + Uvicornで構築するAPIアプリケーション

## Requirements

### Requirement 1: データモデルの定義

**User Story:** 開発者として、Playbook・Bullet・DeltaContextItem等のデータモデルをPydanticモデルとして定義したい. これにより、データの型安全性とバリデーションを確保できる.

#### Acceptance Criteria

1. THE Bullet SHALL id, section, content, searchable_text, keywords, helpful, harmful, source_trajectoryの各フィールドをPydanticモデルとして持つ
2. THE Bullet SHALL helpful数とharmful数から信頼度スコア（confidence_score）を算出するプロパティを持つ
3. THE Playbook SHALL metadata（作成日時、更新日時）とBulletのリストをフィールドとして持つ
4. THE Delta_Context_Item SHALL type（ADD/UPDATE/DELETE）, section, bullet_id, content, reasoningの各フィールドを持つ
5. THE SearchQuery SHALL query_text, top_k, section_filter, min_confidenceの各フィールドを持つ
6. THE SearchResult SHALL bullet, vector_score, bm25_score, combined_scoreの各フィールドを持つ

### Requirement 2: Playbookの永続化

**User Story:** 開発者として、PlaybookをJSON形式でファイルに永続化・読み込みしたい. これにより、データセット別に独立した知識ベースを管理できる.

#### Acceptance Criteria

1. THE PlaybookStore SHALL データセットごとに独立したJSONファイルとしてPlaybookを保存する
2. WHEN PlaybookStoreがPlaybookを読み込む場合, THE PlaybookStore SHALL JSONファイルからPlaybook構造を復元する
3. WHEN PlaybookStoreがPlaybookを保存する場合, THE PlaybookStore SHALL PlaybookをJSON形式でシリアライズしてファイルに書き出す
4. WHEN 指定されたPlaybookファイルが存在しない場合, THE PlaybookStore SHALL 空のPlaybookを新規作成して返却する

### Requirement 3: セクション定義の管理

**User Story:** 開発者として、Bulletの分類に使うセクションをデータセットごとにYAML設定ファイルで定義・管理したい.

#### Acceptance Criteria

1. THE Section定義 SHALL config/sections.yamlにデータセット別のセクション名と説明を記述する
2. WHEN 新しいデータセットを追加する場合, THE Section定義 SHALL 設定ファイルにセクション定義を追加するだけで対応可能とする

### Requirement 4: ハイブリッド検索の基盤

**User Story:** 開発者として、Playbookから関連するBulletをハイブリッド検索で取得する基盤を構築したい.

#### Acceptance Criteria

1. WHEN 検索クエリが与えられた場合, THE Hybrid_Search SHALL query_textからembeddingを生成し、Numpyベクトル近傍探索で上位N件を取得する
2. WHEN 検索クエリが与えられた場合, THE Hybrid_Search SHALL BM25でkeywordsおよびsearchable_textを検索しスコアを算出する
3. THE Hybrid_Search SHALL ベクトルスコアとBM25スコアを重み付き線形結合（α * vector_score + (1-α) * bm25_score）で統合する
4. WHEN section_filterが指定された場合, THE Hybrid_Search SHALL 指定されたセクションに属するBulletのみを返却する
5. WHEN min_confidenceが指定された場合, THE Hybrid_Search SHALL 信頼度スコアが閾値以上のBulletのみを返却する
6. THE Hybrid_Search SHALL 統合スコアの降順でtop_k件のSearchResultを返却する
7. WHEN Playbookが空の場合, THE Hybrid_Search SHALL 空のSearchResultリストを返却する

### Requirement 5: LLMリクエスト基盤

**User Story:** 開発者として、LangChainを使用してLLMにリクエストを送信し、応答を取得する基盤を構築したい. プロバイダ（OpenAI / Bedrock / Azure等）はシンプルに切り替え可能にする.

#### Acceptance Criteria

1. THE LLM_Client SHALL LangChainのChatModelを使用してLLMにリクエストを送信する
2. THE LLM_Client SHALL プロバイダ名（openai / bedrock / azure等）を指定するだけでChatModelを出し分けるファクトリ機能を持つ
3. IF LLMへのリクエストが失敗した場合, THEN THE LLM_Client SHALL エラー情報をログに記録し、例外を送出する

### Requirement 6: DIコンテナの構築

**User Story:** 開発者として、dependency-injectorを使用してコンポーネント間の依存関係を管理したい.

#### Acceptance Criteria

1. THE DI_Container SHALL dependency-injectorを使用してPlaybookStore, Hybrid_Search, LLM_Clientを注入可能にする
2. THE DI_Container SHALL 設定ファイルまたは環境変数からLLMプロバイダの設定を読み込む
3. THE DI_Container SHALL コンポーネントのライフサイクル（シングルトン等）を管理する

### Requirement 7: LangGraphワークフロー基盤

**User Story:** 開発者として、LangGraphを使用してエージェント間のワークフローを定義する基盤を構築したい.

#### Acceptance Criteria

1. THE Workflow SHALL LangGraphのStateGraphを使用してノードとエッジを定義する仕組みを提供する
2. THE Workflow SHALL ワークフローの状態（State）をTypedDictまたはPydanticモデルで定義する
3. WHEN ワークフローが実行された場合, THE Workflow SHALL 定義されたノードを順序通りに実行し、状態を受け渡す
4. THE Workflow SHALL 条件分岐（conditional edge）をサポートする

### Requirement 8: 動作確認

**User Story:** 開発者として、構築した基盤を統合し、手動実行やスクリプトベースでLLMへのリクエストを送り動作確認したい.

#### Acceptance Criteria

1. THE 動作確認 SHALL Pythonファイルとして手動実行可能とする
2. WHEN 動作確認が実行された場合, THE 動作確認 SHALL DIコンテナを初期化し、LLMにリクエストを送信して応答を表示する
3. WHEN 動作確認が実行された場合, THE 動作確認 SHALL Playbookの読み込み・検索・保存の一連の流れを実行する

### Requirement 9: FastAPIアプリケーション基盤

**User Story:** 開発者として、FastAPI + Uvicornでアプリケーションを起動し、API経由でワークフローを実行したい. FastAPIは `src/main.py` に直接配置する.

#### Acceptance Criteria

1. THE FastAPI_App SHALL ヘルスチェックエンドポイント（GET /health）を提供する
2. THE FastAPI_App SHALL DIコンテナと統合し、エンドポイントからコンポーネントを利用可能にする
3. WHEN ワークフロー実行エンドポイント（POST /workflow/run）が呼ばれた場合, THE FastAPI_App SHALL LangGraphワークフローを実行し、結果を返却する
4. THE FastAPI_App SHALL Docker + docker-composeで起動可能にする
5. THE FastAPI_App SHALL `src/main.py` にエントリポイントを配置する（presentation層は設けない）

## User Stories

上記各Requirementに記載のUser Storyを参照.

## Out of Scope

- 各エージェント（Generator / Reflector / Curator）の本格的な推論・分析ロジック
- Web UI
- AutoManual/H²R研究ベースのInsightフォーマット
- embeddingの事前計算・キャッシュの最適化
- Playbook間のマージ・統合機能
- Bulletの自動pruning
- 評価指標のダッシュボード表示
- 網羅的なテストコード
- 高度なDDDパターン（Repository Protocol、ドメインサービス等）

## Open Questions

1. **embedding生成のモデル選定**: searchable_textからembeddingを生成する際、どのモデルを使用するか（OpenAI text-embedding-3-small, AWS Bedrock等）
2. **BM25ライブラリの選定**: Python向けBM25実装として何を使用するか（rank-bm25等）
3. **ハイブリッド検索の重みα**: ベクトルスコアとBM25スコアの統合時の重みαの初期値
4. **LLMプロバイダの優先順位**: OpenAIとAWS Bedrockのどちらをデフォルトとするか
5. **Trajectoryの保存形式**: Trajectoryを永続化するか、メモリ上のみで扱うか
6. **embeddingの保存方式**: pickle以外の選択肢（例: numpy .npy形式）の検討
7. **正解データの形式**: データセットごとの正解データ（Ground Truth）の具体的なフォーマット

## Proposed Architecture

### シンプルな2層（application + components）+ common構成

```
src/
├── common/
│   ├── config/          # 設定ファイル読み込み、環境変数
│   ├── defs/            # 型定義、Enum、Pydanticモデル等の定義
│   ├── di/              # 依存性注入（dependency-injector）
│   ├── exceptions/      # カスタム例外
│   ├── lib/             # ロギング等、全体で使うユーティリティ
│   └── schema/          # APIリクエスト/レスポンススキーマ
├── components/          # 他に依存しない技術コンポーネント（コピペで動くレベル）
│   ├── playbook_store/  # Playbook永続化（JSON）、データモデル
│   ├── hybrid_search/   # ハイブリッド検索エンジン
│   └── llm_client/      # LangChain LLMクライアント（ファクトリ付き）
├── application/
│   ├── agents/          # Generator, Reflector, Curator
│   ├── workflows/       # LangGraphワークフロー定義
│   └── services/        # ユースケース
├── main.py              # FastAPIエントリポイント
└── gunicorn.conf.py     # Gunicorn設定
tests/                   # テストコード
config/                  # 設定ファイル（YAML等）
prompts/                 # プロンプトテンプレート
```

### 依存関係

- `components/` → 外部ライブラリのみに依存. application層には依存しない
- `application/` → `components/` をimportしてビジネスロジックを組み立てる
- `common/` → 設定とDIを提供. components, applicationの両方から参照される
- FastAPIは `src/main.py` に直接配置する（presentation層は設けない）

## Data Model

### Bullet

| フィールド | 型 | 説明 |
|-----------|-----|------|
| id | str | 一意識別子（例: "shr-00001"） |
| section | str | セクション名 |
| content | str | 知識の内容 |
| searchable_text | str | 検索対象テキスト |
| keywords | list[str] | BM25用キーワード |
| helpful | int | 有用カウンター（デフォルト: 0） |
| harmful | int | 有害カウンター（デフォルト: 0） |
| source_trajectory | str | 生成元の軌跡ID |

### Playbook

| フィールド | 型 | 説明 |
|-----------|-----|------|
| metadata | PlaybookMetadata | 作成日時、更新日時 |
| bullets | list[Bullet] | Bulletのリスト |

### DeltaContextItem

| フィールド | 型 | 説明 |
|-----------|-----|------|
| type | Literal["ADD", "UPDATE", "DELETE"] | 操作種別 |
| section | str | 対象セクション |
| bullet_id | Optional[str] | 対象BulletのID |
| content | str | 新しい/更新内容 |
| reasoning | str | 変更理由 |

### SearchQuery / SearchResult

SearchQuery:

| フィールド | 型 | 説明 |
|-----------|-----|------|
| query_text | str | 検索クエリ |
| top_k | int | 取得件数（デフォルト: 10） |
| section_filter | list[str] \| None | セクションフィルタ |
| min_confidence | float | 最低信頼度（デフォルト: 0.3） |

SearchResult:

| フィールド | 型 | 説明 |
|-----------|-----|------|
| bullet | Bullet | 検索結果のBullet |
| vector_score | float | ベクトル類似度 |
| bm25_score | float | BM25スコア |
| combined_score | float | 統合スコア |

## API

PoCフェーズの基本エンドポイント:

| エンドポイント | メソッド | 説明 |
|--------------|---------|------|
| /health | GET | ヘルスチェック |
| /workflow/run | POST | ワークフロー実行 |

## UI

UIは提供しない. API経由または手動実行で動作確認する.
