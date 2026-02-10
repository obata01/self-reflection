# 要件定義: Curatorエージェント

## はじめに

Curatorエージェントは、ACE（Agentic Context Engineering）フレームワークにおけるキュレーションエージェントである. Reflectorが抽出したInsights（洞察）とBulletEvaluation（Bullet評価）を受け取り、現在のPlaybookと照合して、Delta操作（ADD/UPDATE/DELETE）を決定し、PlaybookをマージするCuratorは、知識ベースの品質を継続的に改善する役割を担う.

## 用語集

- **Curator**: Reflectorの出力を受け取り、Playbookの更新差分（Delta Context Items）を生成・適用するエージェント.
- **Playbook**: 知識ベース全体. Bulletのコンテナ. データセットごとにJSONファイルで管理される.
- **Bullet**: 個別の知識単位. helpful/harmfulカウンターによる信頼度スコアを持つ.
- **DeltaContextItem**: Curatorが生成するPlaybookへの更新差分. ADD/UPDATE/DELETEの操作種別を持つ.
- **CurationResult**: Curatorの出力全体. Delta Context Itemsのリストと更新後のPlaybookを含む.
- **ReflectionResult**: Reflectorの出力全体. InsightsとBulletEvaluationのリストを含む.
- **Insight**: Reflectorの分析結果. 思考過程、エラー特定、根本原因分析、正しいアプローチ、教訓を含む.
- **BulletEvaluation**: Bulletに対するhelpful/harmful/neutralの評価タグ.
- **Section**: Bulletの分類カテゴリ. データセットごとにconfig/sections.yamlで定義される.
- **LLMClient**: LangChainのChatModelをラップするクライアント.
- **PromptBuilder**: プロンプトテンプレートの読み込みと構築を行うビルダー.
- **PlaybookStore**: PlaybookをJSON形式で永続化するストア.
- **HybridSearch**: Numpyベクトル近傍探索とBM25全文検索を組み合わせた検索エンジン.

## 要件

### 要件1: CurationResultデータモデルの定義

**ユーザーストーリー:** 開発者として、Curatorの出力全体（Delta Context Itemsと更新後のPlaybook）を一つの構造体として扱いたい. それにより、後続処理への受け渡しとワークフロー統合を簡潔にする.

#### 受入基準

1. THE CurationResult モデル SHALL DeltaContextItemのリスト、更新前のBullet数、更新後のBullet数、処理サマリーをフィールドとして保持する.
2. THE CurationResult モデル SHALL Pydantic BaseModelを継承し、型安全なバリデーションを提供する.
3. WHEN CurationResult をJSON形式でシリアライズし、再度デシリアライズした場合、THE CurationResult モデル SHALL 元のオブジェクトと等価なオブジェクトを復元する.

### 要件2: InsightsからDelta Context Itemsの生成

**ユーザーストーリー:** 開発者として、ReflectorのInsightsから新しい知識をPlaybookに追加するためのDelta操作を自動生成したい. それにより、学習した教訓を知識ベースに蓄積する.

#### 受入基準

1. WHEN ReflectionResultのInsightsが与えられた場合、THE Curator SHALL LLMを使用して各Insightを分析し、適切なDelta操作（ADD/UPDATE/DELETE）を決定する.
2. WHEN ADD操作が決定された場合、THE Curator SHALL config/sections.yamlで定義されたセクションの中から適切なセクションを選択してDeltaContextItemを生成する.
3. WHEN UPDATE操作が決定された場合、THE Curator SHALL 既存のBullet IDを指定し、更新内容を含むDeltaContextItemを生成する.
4. WHEN DELETE操作が決定された場合、THE Curator SHALL 削除対象のBullet IDを指定したDeltaContextItemを生成する.
5. WHEN Insightsが空の場合、THE Curator SHALL 空のDeltaContextItemリストを返す.

### 要件3: 既存Playbookとの重複検出

**ユーザーストーリー:** 開発者として、新しいInsightが既存のPlaybook知識と重複していないかを検出したい. それにより、知識ベースの冗長性を防ぐ.

#### 受入基準

1. WHEN 新しいInsightのkey_insightが既存Bulletのcontentと意味的に類似している場合、THE Curator SHALL 重複としてADD操作ではなくUPDATE操作を選択する.
2. THE Curator SHALL 重複検出の結果をDeltaContextItemのreasoningフィールドに記録する.

### 要件4: BulletEvaluationに基づくカウンター更新

**ユーザーストーリー:** 開発者として、ReflectorのBulletEvaluation結果に基づいてBulletのhelpful/harmfulカウンターを更新したい. それにより、知識の信頼度スコアを継続的に改善する.

#### 受入基準

1. WHEN BulletEvaluationのtagが"helpful"の場合、THE Curator SHALL 対象BulletのhelpfulカウンターをPlaybook内で1増加させる.
2. WHEN BulletEvaluationのtagが"harmful"の場合、THE Curator SHALL 対象BulletのharmfulカウンターをPlaybook内で1増加させる.
3. WHEN BulletEvaluationのtagが"neutral"の場合、THE Curator SHALL 対象Bulletのカウンターを変更しない.
4. WHEN BulletEvaluationのbullet_idがPlaybook内に存在しない場合、THE Curator SHALL 該当評価をスキップする.

### 要件5: Delta Context ItemsのPlaybookへのマージ

**ユーザーストーリー:** 開発者として、生成されたDelta Context Itemsを現在のPlaybookに適用したい. それにより、知識ベースを更新する.

#### 受入基準

1. WHEN ADD操作のDeltaContextItemが適用される場合、THE Curator SHALL 新しいBulletを生成し、一意のIDを付与してPlaybookに追加する.
2. WHEN UPDATE操作のDeltaContextItemが適用される場合、THE Curator SHALL 指定されたBullet IDのcontentとsearchable_textを更新する.
3. WHEN DELETE操作のDeltaContextItemが適用される場合、THE Curator SHALL 指定されたBullet IDのBulletをPlaybookから削除する.
4. IF UPDATE操作またはDELETE操作で指定されたBullet IDがPlaybook内に存在しない場合、THEN THE Curator SHALL 該当操作をスキップしログに記録する.
5. WHEN マージが完了した場合、THE Curator SHALL PlaybookStoreのsaveメソッドを使用してPlaybookを永続化する.

### 要件6: Curator用プロンプトテンプレート管理

**ユーザーストーリー:** 開発者として、Curatorが使用するプロンプトテンプレートをデータセットごとにカスタマイズしたい. それにより、様々なタスクドメインに対応したキュレーションが可能になる.

#### 受入基準

1. THE PromptBuilder SHALL データセット名を指定してCurator用プロンプトテンプレートファイルを読み込む.
2. WHEN プロンプトテンプレートにInsights、現在のPlaybookのBullet、セクション定義を注入する場合、THE PromptBuilder SHALL テンプレート変数を正しく展開した文字列を返す.
3. IF 指定されたデータセットのテンプレートファイルが存在しない場合、THEN THE PromptBuilder SHALL デフォルトテンプレートを使用する.
4. THE PromptBuilder SHALL テンプレートファイルをprompts/curator/ディレクトリから読み込む.

### 要件7: Curatorエージェントの統合処理フロー

**ユーザーストーリー:** 開発者として、Curatorの処理フロー全体（Insight分析 → 重複検出 → Delta生成 → カウンター更新 → マージ → 永続化）を一貫して実行したい. それにより、単一のメソッド呼び出しでPlaybook更新が完了する.

#### 受入基準

1. WHEN CuratorにReflectionResultとデータセット名が与えられた場合、THE Curator SHALL Playbook読み込み、Delta生成、カウンター更新、マージ、永続化の一連の処理を順次実行する.
2. THE Curator SHALL 依存コンポーネント（LLMClient、PromptBuilder、PlaybookStore）をコンストラクタで受け取り、疎結合な構成とする.
3. WHEN Curatorが実行を完了した場合、THE Curator SHALL 完全なCurationResultオブジェクトを返す.

### 要件8: セクション定義の読み込み

**ユーザーストーリー:** 開発者として、データセットごとのセクション定義をconfig/sections.yamlから読み込みたい. それにより、ADD操作時に適切なセクションを指定できるようにする.

#### 受入基準

1. THE Curator SHALL config/sections.yamlからデータセットに対応するセクション定義を読み込む.
2. WHEN 指定されたデータセットのセクション定義が存在しない場合、THE Curator SHALL 空のセクションリストとして処理を続行する.
3. THE Curator SHALL セクション名と説明をLLMプロンプトに含め、適切なセクション選択を支援する.

### 要件9: DIコンテナへの登録

**ユーザーストーリー:** 開発者として、Curatorエージェントを既存のDIコンテナに登録したい. それにより、アプリケーション全体で一貫した依存性管理を行う.

#### 受入基準

1. THE Container SHALL CuratorAgentをプロバイダとして登録する.
2. WHEN ContainerからCuratorAgentを取得する場合、THE Container SHALL 必要な依存コンポーネント（LLMClient、PlaybookStore）を自動的に注入する.
