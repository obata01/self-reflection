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
| `--limit N` | 処理する問題数 | `5` |