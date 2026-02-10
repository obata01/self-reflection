---
inclusion: always
---

# プロジェクト構成

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
├── scripts/             # エージェント動作確認スクリプト
│   ├── run_generator.py
│   ├── run_reflector.py
│   ├── run_curator.py
│   └── ...
├── main.py              # FastAPIエントリポイント
└── gunicorn.conf.py     # Gunicorn設定
tests/                   # テストコード
config/                  # 設定ファイル（YAML等）
prompts/                 # プロンプトテンプレート
```

## アーキテクチャ方針

- シンプルな2層（application + components）+ common構成
- 高度なDDDパターンは採用しない
- `components/` は外部ライブラリのみに依存し、application層には依存しない（コピペで動くレベル）
- `application/` は `components/` をimportしてビジネスロジックを組み立てる（逆方向の依存はない）
- `common/` は設定とDIを提供し、components/applicationの両方から参照される
- FastAPIは `src/main.py` に配置する（presentation層は設けない）
- 依存性注入（dependency-injector）でコンポーネント間を疎結合にする
- LLMClientはファクトリ関数でプロバイダ（OpenAI / Bedrock / Azure等）を出し分けるシンプルな設計

## データファイル構成

```
data/playbooks/          # Playbook JSONファイル（データセット別）
```

## 設定・ルール

- ruff.toml: line-length=120, select=ALL（一部ignore）
- testsディレクトリはruffの対象外

## 現フェーズの方針

- 現在は本番実装ではなく検証（PoC）フェーズである.
- テストコードは基本不要. 書く場合も最低限にとどめること.
- 動作確認は手動実行やスクリプトベースで十分とする.
