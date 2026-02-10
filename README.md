# self-reflection

## 動作確認スクリプト

各エージェントの動作を個別にテストするスクリプトが用意されています。

### 前提条件

`.env`ファイルに`OPENAI_API_KEY`を設定してください。

### スクリプト一覧

```bash
# Generatorエージェントのテスト
python src/scripts/run_generator.py

# Reflectorエージェントのテスト
python src/scripts/run_reflector.py

# Curatorエージェントのテスト
python src/scripts/run_curator.py

# データセット取得
python src/scripts/fetch_jcommonsenseqa.py
```

各スクリプトは独立して実行可能で、LLM APIを実際に呼び出してエージェントの動作を確認できます。

### ワークフロー実行

JCommonsenseQAデータセットに対してパイプラインを実行し、正解率を算出します。

```bash
# 推論のみ (Generate → Judge)
python src/scripts/run_workflow.py --mode infer

# フルパイプライン (Generate → Reflect → Curate)
python src/scripts/run_workflow.py --mode full

# 件数指定 (デフォルト: 5件)
python src/scripts/run_workflow.py --mode infer --limit 10
```

| オプション | 説明 | デフォルト |
|---|---|---|
| `--mode infer` | 推論+正解率のみ | - |
| `--mode full` | Reflect/Curateを含むフルパイプライン | `full` |
| `--mode batch-infer` | 全件推論し結果をファイルに保存 | - |
| `--mode batch-reflect` | 保存済み推論結果から全件リフレクション | - |
| `--mode batch-curate` | 保存済みリフレクション結果から全件キュレーション | - |
| `--limit N` | 処理する問題数 (`infer`/`full`: 5, `batch-*`: 全件) | モードによる |

### ステージ別バッチ実行

各ステージの中間結果をファイルに保存し、ステージごとに独立して実行できます。

```bash
# 1. 全件推論 → data/results/jcommonsenseqa/infer.jsonl に保存
python src/scripts/run_workflow.py --mode batch-infer

# 2. 推論結果を読み込みリフレクション → data/results/jcommonsenseqa/reflect.jsonl に保存
python src/scripts/run_workflow.py --mode batch-reflect

# 3. リフレクション結果を読み込みキュレーション → Playbook更新
python src/scripts/run_workflow.py --mode batch-curate
```

`--limit` で件数を絞ってテストすることもできます。

```bash
python src/scripts/run_workflow.py --mode batch-infer --limit 10
python src/scripts/run_workflow.py --mode batch-reflect --limit 10
python src/scripts/run_workflow.py --mode batch-curate --limit 10
```