# 要件定義書

## はじめに

JCommonsenseQAデータセット（Hugging Face: sbintuitions/JCommonsenseQA）を取得し、プロジェクトのdataディレクトリに保存するデータセットローダーを構築する. Generatorエージェント等が後から利用できるよう、統一的なインターフェースでデータにアクセスできるようにする.

## 用語集

- **Dataset_Loader**: JCommonsenseQAデータセットをHugging Faceから取得し、ローカルに保存するコンポーネント
- **Task_Loader**: 保存済みデータセットからタスク（問題）を読み込み、Generatorエージェント等に提供するコンポーネント
- **Question_Record**: 1件の常識問題を表すデータ構造. q_id, question, choice0〜choice4, labelを含む
- **Split**: データセットの分割単位. train（8,940件）とvalidation（1,120件）が存在する
- **NFKC_Normalizer**: Unicode NFKC正規化を行う処理. question/choice*フィールドに適用する

## 要件

### 要件1: データセットの取得と保存

**ユーザーストーリー:** 開発者として、JCommonsenseQAデータセットをHugging Faceから取得してローカルに保存したい. これにより、オフラインでもデータにアクセスできるようにする.

#### 受け入れ基準

1. WHEN Dataset_Loaderがデータセット取得を実行した場合, THE Dataset_Loader SHALL Hugging FaceからJCommonsenseQAのtrain splitとvalidation splitの両方をParquet形式で取得する
2. WHEN Dataset_Loaderがデータを保存する場合, THE Dataset_Loader SHALL data/datasets/jcommonsenseqa/ ディレクトリにsplit別のJSONLファイルとして保存する
3. WHEN Dataset_Loaderがデータを保存する場合, THE Dataset_Loader SHALL 各レコードのquestionフィールドとchoice0〜choice4フィールドにNFKC正規化を適用する
4. WHEN 保存先ディレクトリが存在しない場合, THE Dataset_Loader SHALL ディレクトリを自動作成する
5. WHEN データセット取得中にネットワークエラーが発生した場合, THEN THE Dataset_Loader SHALL エラー内容をログに記録し、適切な例外を送出する

### 要件2: データモデルの定義

**ユーザーストーリー:** 開発者として、JCommonsenseQAのレコードを型安全に扱いたい. これにより、データの整合性を保証する.

#### 受け入れ基準

1. THE Question_Record SHALL q_id（str）, question（str）, choice0〜choice4（str）, label（int）のフィールドを持つPydanticモデルとして定義される
2. WHEN Question_Recordのlabelフィールドに0〜4の範囲外の値が設定された場合, THEN THE Question_Record SHALL バリデーションエラーを送出する
3. THE Question_Record SHALL labelフィールドの値に対応するchoiceフィールドの値を返すプロパティを提供する

### 要件3: タスクの読み込みと提供

**ユーザーストーリー:** 開発者として、保存済みデータセットからタスクを読み込んでGeneratorエージェント等に提供したい. これにより、データセットを使った検証を実行できるようにする.

#### 受け入れ基準

1. WHEN Task_LoaderがSplit名を指定してデータを読み込む場合, THE Task_Loader SHALL 指定されたsplitのJSONLファイルからQuestion_Recordのリストを返す
2. WHEN Task_Loaderが存在しないsplitを指定された場合, THEN THE Task_Loader SHALL 適切な例外を送出する
3. WHEN Task_Loaderがタスクを提供する場合, THE Task_Loader SHALL Question_Recordをクエリ文字列（question + 選択肢のフォーマット済みテキスト）に変換するメソッドを提供する
4. WHEN Task_Loaderが正解判定を行う場合, THE Task_Loader SHALL Generatorの回答とQuestion_Recordのlabelを比較して正誤を判定するメソッドを提供する

### 要件4: データセットのJSONLシリアライズ

**ユーザーストーリー:** 開発者として、データセットをJSONL形式で保存・読み込みしたい. これにより、データの永続化と再利用を可能にする.

#### 受け入れ基準

1. WHEN Dataset_LoaderがQuestion_RecordをJSONLファイルに保存する場合, THE Dataset_Loader SHALL 各行が1つのQuestion_RecordのJSON表現となるJSONLフォーマットで書き出す
2. WHEN Task_LoaderがJSONLファイルからデータを読み込む場合, THE Task_Loader SHALL 各行をQuestion_Recordにデシリアライズする
3. FOR ALL 有効なQuestion_Recordのリストに対して, JSONLへのシリアライズ後にデシリアライズした結果は元のリストと等価である（ラウンドトリップ特性）
