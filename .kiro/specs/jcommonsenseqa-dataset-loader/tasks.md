# 実装計画: JCommonsenseQA データセットローダー

## 概要

JCommonsenseQAデータセットの取得・保存・読み込み機能を、components層に2つのパッケージ（dataset_loader, task_loader）として実装する. PoCフェーズのためシンプルな実装を優先する.

## タスク

- [X] 1. QuestionRecordモデルの実装
  - [X] 1.1 `src/components/dataset_loader/models.py` にQuestionRecord Pydanticモデルを作成する
    - q_id, question, choice0〜choice4, label フィールドを定義
    - labelのバリデーション（0〜4の範囲）を `Field(ge=0, le=4)` で実装
    - correct_answer プロパティ（labelに対応するchoice値を返す）を実装
    - to_query メソッド（question + 選択肢のフォーマット済みテキストを返す）を実装
    - `src/components/dataset_loader/__init__.py` を作成
    - _Requirements: 2.1, 2.2, 2.3, 3.3_
  - [ ]* 1.2 QuestionRecordのプロパティテストを作成する
    - `tests/test_question_record.py` にHypothesisを使ったテストを実装
    - **Property 2: labelバリデーション**
    - **Property 3: correct_answerと正解判定の一貫性**
    - **Property 4: to_queryの完全性**
    - **Validates: Requirements 2.2, 2.3, 3.3**

- [X] 2. DatasetLoaderの実装
  - [X] 2.1 `src/components/dataset_loader/loader.py` にDatasetLoaderクラスを作成する
    - `__init__` でoutput_dirを受け取る（デフォルト: `data/datasets/jcommonsenseqa`）
    - `fetch_and_save` メソッド: HFからtrain/validationを取得し、NFKC正規化してJSONL保存
    - `_fetch_split` メソッド: pandas.read_parquetでHFからsplit取得、QuestionRecordリストに変換
    - `_normalize_nfkc` メソッド: unicodedata.normalize('NFKC', text) を適用
    - `_save_jsonl` メソッド: QuestionRecordリストをJSONLファイルに書き出し
    - ディレクトリ自動作成（pathlib.Path.mkdir(parents=True, exist_ok=True)）
    - ネットワークエラー時のログ出力と例外送出
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 4.1_
  - [ ]* 2.2 NFKC正規化のプロパティテストを作成する
    - `tests/test_dataset_loader.py` にHypothesisを使ったテストを実装
    - **Property 1: NFKC正規化の冪等性**
    - **Validates: Requirements 1.3**

- [ ] 3. チェックポイント - QuestionRecordとDatasetLoaderの動作確認
  - 全テストが通ることを確認し、疑問があればユーザーに確認する.

- [X] 4. TaskLoaderの実装
  - [X] 4.1 `src/components/task_loader/loader.py` にTaskLoaderクラスを作成する
    - `__init__` でdata_dirを受け取る（デフォルト: `data/datasets/jcommonsenseqa`）
    - `load` メソッド: 指定splitのJSONLファイルからQuestionRecordリストを読み込み
    - `evaluate` メソッド: Generatorの回答とQuestionRecordのlabelを比較して正誤判定
    - 存在しないsplit指定時のFileNotFoundError送出
    - `src/components/task_loader/__init__.py` を作成
    - _Requirements: 3.1, 3.2, 3.4, 4.2_
  - [ ]* 4.2 JSONLラウンドトリップのプロパティテストを作成する
    - `tests/test_task_loader.py` にHypothesisを使ったテストを実装
    - **Property 5: JSONLラウンドトリップ**
    - **Validates: Requirements 4.1, 4.2, 4.3**

- [X] 5. データ取得スクリプトの作成
  - [X] 5.1 `scripts/fetch_jcommonsenseqa.py` にデータ取得用のCLIスクリプトを作成する
    - DatasetLoaderを使ってデータを取得・保存する
    - 実行結果（件数等）をログ出力する
    - `python scripts/fetch_jcommonsenseqa.py` で実行可能にする
    - _Requirements: 1.1, 1.2_

- [ ] 6. 最終チェックポイント - 全体の動作確認
  - 全テストが通ることを確認し、疑問があればユーザーに確認する.

## 備考

- `*` 付きのタスクはオプション（PoCフェーズのためスキップ可能）
- 各タスクは対応する要件への参照を含む
- チェックポイントで段階的に動作を検証する
- プロパティテストはHypothesisライブラリを使用する
