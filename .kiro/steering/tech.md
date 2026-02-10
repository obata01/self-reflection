---
inclusion: always
---

# 技術スタック

## 言語・ランタイム

- Python 3.13
- パッケージ管理: uv（pip互換）

## 主要ライブラリ

- LangChain: LLMへのリクエスト処理
- LangGraph: エージェント間ワークフロー（各エージェントをノードとして接続）
- langchain-openai / langchain-aws: LLMプロバイダ
- Pydantic: データバリデーション・モデル定義
- FastAPI + Uvicorn: API（オプション）
- dependency-injector: DI
- PyYAML: 設定ファイル管理
- NumPy: ベクトル近傍探索
- Pandas / Matplotlib / Seaborn: データ分析・可視化

## 開発ツール

- Linter/Formatter: ruff（設定は `ruff.toml`）
- テスト: pytest, pytest-asyncio
- HTTPクライアント: httpx（テスト用）

## インフラ

- Docker + docker-compose
- サービス名: `reflection`
- PYTHONPATH: `/app` および `/app/src`

## 環境変数（.envで管理）

- OPENAI_API_KEY
- LANGCHAIN_API_KEY

## よく使うコマンド

```bash
# リント
make lint

# フォーマット
make format

# 依存関係更新
make update

# Docker起動
docker compose up -d

# テスト実行
docker compose exec reflection pytest
```
