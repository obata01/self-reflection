# 要件定義: Generatorエージェント

## はじめに

Generatorエージェントは、ACE（Agentic Context Engineering）フレームワークにおけるタスク実行・推論エージェントである. Query（タスク）とPlaybook（知識ベース）を入力として受け取り、Playbookからハイブリッド検索で関連知識を取得し、LLMを用いてタスクを実行し、推論過程（Trajectory）を出力する. 将来的に別のエージェントに置き換わる可能性があるため、インターフェースを明確に定義し疎結合な設計とする.

## 用語集

- **Generator**: タスク実行・推論を行うエージェント. Query + Playbookを入力とし、Trajectoryを出力する.
- **Playbook**: 知識ベース全体. Bulletのコンテナ. データセットごとにJSONファイルで管理される.
- **Bullet**: 個別の知識単位. helpful/harmfulカウンターによる信頼度スコアを持つ.
- **Trajectory**: Generatorの推論過程の記録. 生成結果と推論ステップを含む.
- **HybridSearch**: Numpyベクトル近傍探索とBM25全文検索を組み合わせた検索エンジン.
- **LLMClient**: LangChainのChatModelをラップするクライアント.
- **PromptTemplate**: プロンプトテンプレート. データセットごとにカスタマイズ可能.
- **SearchQuery**: ハイブリッド検索のクエリモデル.
- **SearchResult**: ハイブリッド検索の結果モデル.

## 要件

### 要件1: Trajectoryデータモデルの定義

**ユーザーストーリー:** 開発者として、Generatorの推論過程を構造化されたデータとして記録したい. それにより、後続のReflectorエージェントが分析可能な形式でTrajectoryを受け取れるようにする.

#### 受入基準

1. THE Trajectory モデル SHALL クエリ、生成結果、推論ステップ、使用されたBulletの参照、成功/失敗ステータスをフィールドとして保持する.
2. THE Trajectory モデル SHALL Pydantic BaseModelを継承し、型安全なバリデーションを提供する.
3. WHEN Trajectory が生成された場合、THE Trajectory モデル SHALL JSON形式でシリアライズ可能である.
4. WHEN Trajectory をJSON形式でシリアライズし、再度デシリアライズした場合、THE Trajectory モデル SHALL 元のオブジェクトと等価なオブジェクトを復元する.

### 要件2: プロンプトテンプレート管理

**ユーザーストーリー:** 開発者として、データセットごとに異なるプロンプトテンプレートを使用したい. それにより、様々なタスクドメインに対応できるようにする.

#### 受入基準

1. THE PromptBuilder SHALL データセット名を指定してプロンプトテンプレートファイルを読み込む.
2. WHEN プロンプトテンプレートにクエリと検索結果のBulletを注入する場合、THE PromptBuilder SHALL テンプレート変数を正しく展開した文字列を返す.
3. IF 指定されたデータセットのテンプレートファイルが存在しない場合、THEN THE PromptBuilder SHALL デフォルトテンプレートを使用する.
4. THE PromptBuilder SHALL テンプレートファイルをprompts/ディレクトリから読み込む.

### 要件3: Playbook検索と知識注入

**ユーザーストーリー:** 開発者として、Generatorがタスクに関連する知識のみをPlaybookから取得して使用したい. それにより、LLMのコンテキストウィンドウを効率的に活用する.

#### 受入基準

1. WHEN クエリが与えられた場合、THE Generator SHALL HybridSearchを使用してPlaybookから関連Bulletを検索する.
2. WHEN 検索結果が得られた場合、THE Generator SHALL 検索結果のBulletをプロンプトに注入する.
3. WHEN Playbookが空の場合、THE Generator SHALL 検索結果なしでプロンプトを構築し、LLMにリクエストを送信する.

### 要件4: LLMによるタスク実行

**ユーザーストーリー:** 開発者として、GeneratorがLLMを使用してタスクを実行し、推論結果を得たい. それにより、Playbookの知識を活用した高品質な回答を生成する.

#### 受入基準

1. WHEN クエリと検索結果が準備された場合、THE Generator SHALL LLMClientを使用してプロンプトを送信し、応答を取得する.
2. WHEN LLMの応答が得られた場合、THE Generator SHALL 応答をTrajectoryオブジェクトとして構造化する.
3. IF LLMリクエストが失敗した場合、THEN THE Generator SHALL エラー情報を含むTrajectoryを生成し、失敗ステータスを設定する.

### 要件5: Generatorエージェントの統合処理フロー

**ユーザーストーリー:** 開発者として、Generatorの処理フロー全体（Playbook読み込み → 検索 → プロンプト構築 → LLM実行 → Trajectory生成）を一貫して実行したい. それにより、単一のメソッド呼び出しでタスク実行が完了する.

#### 受入基準

1. WHEN Generatorにクエリとデータセット名が与えられた場合、THE Generator SHALL Playbook読み込み、ハイブリッド検索、プロンプト構築、LLM実行、Trajectory生成の一連の処理を順次実行する.
2. THE Generator SHALL 依存コンポーネント（PlaybookStore、HybridSearch、LLMClient、PromptBuilder）をコンストラクタで受け取り、疎結合な構成とする.
3. WHEN Generatorが実行を完了した場合、THE Generator SHALL 完全なTrajectoryオブジェクトを返す.

### 要件6: DIコンテナへの登録

**ユーザーストーリー:** 開発者として、Generatorエージェントを既存のDIコンテナに登録したい. それにより、アプリケーション全体で一貫した依存性管理を行う.

#### 受入基準

1. THE Container SHALL GeneratorAgentをプロバイダとして登録する.
2. WHEN ContainerからGeneratorAgentを取得する場合、THE Container SHALL 必要な依存コンポーネント（PlaybookStore、HybridSearch、LLMClient）を自動的に注入する.
