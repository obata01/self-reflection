# 要件定義: Reflectorエージェント

## はじめに

Reflectorエージェントは、ACE（Agentic Context Engineering）フレームワークにおける自己内省エージェントである. Generatorが生成したTrajectory（推論過程）を受け取り、正解データ（Ground Truth）やテスト結果と比較して、成功/失敗を分析し、教訓（Insights）を抽出する. また、Playbookの各Bulletに対してhelpful/harmful/neutralの評価タグを付与する. 抽出されたInsightsは後続のCuratorエージェントに渡され、Playbookの更新に使用される.

## 用語集

- **Reflector**: 成功/失敗を分析し、教訓（Insights）を抽出するエージェント. Trajectory + Ground Truth + Test Reportを入力とし、Insightsを出力する.
- **Trajectory**: Generatorの推論過程の記録. クエリ、生成結果、推論ステップ、使用されたBulletの参照を含む.
- **Insight**: Reflectorの分析結果. 思考過程、エラー特定、根本原因分析、正しいアプローチ、教訓を含む中間生成物.
- **BulletEvaluation**: Bulletに対するhelpful/harmful/neutralの評価タグ. Reflectorが各Bulletの有用性を判定した結果.
- **GroundTruth**: タスクの正解データ. 正解コードやテスト結果を含む.
- **Playbook**: 知識ベース全体. Bulletのコンテナ.
- **Bullet**: 個別の知識単位. helpful/harmfulカウンターによる信頼度スコアを持つ.
- **LLMClient**: LangChainのChatModelをラップするクライアント.
- **PromptBuilder**: プロンプトテンプレートの読み込みと構築を行うビルダー.
- **ReflectionResult**: Reflectorの出力全体. InsightsとBulletEvaluationのリストを含む.

## 要件

### 要件1: Insightデータモデルの定義

**ユーザーストーリー:** 開発者として、Reflectorの分析結果を構造化されたデータとして記録したい. それにより、後続のCuratorエージェントが分析可能な形式でInsightsを受け取れるようにする.

#### 受入基準

1. THE Insight モデル SHALL 思考過程（reasoning）、エラー特定（error_identification）、根本原因分析（root_cause_analysis）、正しいアプローチ（correct_approach）、教訓（key_insight）をフィールドとして保持する.
2. THE Insight モデル SHALL Pydantic BaseModelを継承し、型安全なバリデーションを提供する.
3. WHEN Insight が生成された場合、THE Insight モデル SHALL JSON形式でシリアライズ可能である.
4. WHEN Insight をJSON形式でシリアライズし、再度デシリアライズした場合、THE Insight モデル SHALL 元のオブジェクトと等価なオブジェクトを復元する.

### 要件2: BulletEvaluationデータモデルの定義

**ユーザーストーリー:** 開発者として、Reflectorが各Bulletの有用性を評価した結果を構造化されたデータとして記録したい. それにより、Bulletの信頼度スコアの更新に使用できるようにする.

#### 受入基準

1. THE BulletEvaluation モデル SHALL Bullet ID、評価タグ（helpful/harmful/neutral）、評価理由をフィールドとして保持する.
2. THE BulletEvaluation モデル SHALL Pydantic BaseModelを継承し、型安全なバリデーションを提供する.
3. WHEN BulletEvaluation をJSON形式でシリアライズし、再度デシリアライズした場合、THE BulletEvaluation モデル SHALL 元のオブジェクトと等価なオブジェクトを復元する.

### 要件3: ReflectionResultデータモデルの定義

**ユーザーストーリー:** 開発者として、Reflectorの出力全体（InsightsとBulletEvaluation）を一つの構造体として扱いたい. それにより、後続処理への受け渡しを簡潔にする.

#### 受入基準

1. THE ReflectionResult モデル SHALL Insightのリスト、BulletEvaluationのリスト、元のTrajectoryへの参照をフィールドとして保持する.
2. THE ReflectionResult モデル SHALL Pydantic BaseModelを継承し、型安全なバリデーションを提供する.
3. WHEN ReflectionResult をJSON形式でシリアライズし、再度デシリアライズした場合、THE ReflectionResult モデル SHALL 元のオブジェクトと等価なオブジェクトを復元する.

### 要件4: Reflector用プロンプトテンプレート管理

**ユーザーストーリー:** 開発者として、Reflectorが使用するプロンプトテンプレートをデータセットごとにカスタマイズしたい. それにより、様々なタスクドメインに対応した分析が可能になる.

#### 受入基準

1. THE PromptBuilder SHALL データセット名を指定してReflector用プロンプトテンプレートファイルを読み込む.
2. WHEN プロンプトテンプレートにTrajectory、Ground Truth、テスト結果、現在のPlaybookのBulletを注入する場合、THE PromptBuilder SHALL テンプレート変数を正しく展開した文字列を返す.
3. IF 指定されたデータセットのテンプレートファイルが存在しない場合、THEN THE PromptBuilder SHALL デフォルトテンプレートを使用する.
4. THE PromptBuilder SHALL テンプレートファイルをprompts/reflector/ディレクトリから読み込む.

### 要件5: LLMによる分析実行

**ユーザーストーリー:** 開発者として、ReflectorがLLMを使用してTrajectoryを分析し、Insightsを抽出したい. それにより、エラーの根本原因と改善策を自動的に特定する.

#### 受入基準

1. WHEN Trajectory、Ground Truth、テスト結果が準備された場合、THE Reflector SHALL LLMClientを使用してプロンプトを送信し、分析結果を取得する.
2. WHEN LLMの応答が得られた場合、THE Reflector SHALL 応答をInsightオブジェクトのリストとして構造化する.
3. IF LLMリクエストが失敗した場合、THEN THE Reflector SHALL エラー情報を含むReflectionResultを生成し、空のInsightsリストを返す.

### 要件6: Bullet評価タグの付与

**ユーザーストーリー:** 開発者として、ReflectorがTrajectoryで使用された各Bulletの有用性を評価したい. それにより、Playbookの知識品質を継続的に改善する.

#### 受入基準

1. WHEN Trajectoryに使用されたBullet IDリストが含まれる場合、THE Reflector SHALL 各BulletについてLLMを使用してhelpful/harmful/neutralの評価を行う.
2. WHEN Bullet評価が完了した場合、THE Reflector SHALL BulletEvaluationオブジェクトのリストとして結果を返す.
3. WHEN Trajectoryに使用されたBulletが存在しない場合、THE Reflector SHALL 空のBulletEvaluationリストを返す.

### 要件7: Reflectorエージェントの統合処理フロー

**ユーザーストーリー:** 開発者として、Reflectorの処理フロー全体（プロンプト構築 → LLM分析 → Insight抽出 → Bullet評価 → ReflectionResult生成）を一貫して実行したい. それにより、単一のメソッド呼び出しで分析が完了する.

#### 受入基準

1. WHEN ReflectorにTrajectory、Ground Truth文字列、テスト結果文字列、データセット名が与えられた場合、THE Reflector SHALL プロンプト構築、LLM分析、Insight抽出、Bullet評価の一連の処理を順次実行する.
2. THE Reflector SHALL 依存コンポーネント（LLMClient、PromptBuilder、PlaybookStore）をコンストラクタで受け取り、疎結合な構成とする.
3. WHEN Reflectorが実行を完了した場合、THE Reflector SHALL 完全なReflectionResultオブジェクトを返す.

### 要件8: 反復改善（Iterative Refinement）

**ユーザーストーリー:** 開発者として、Reflectorの分析を複数回繰り返すオプションを持ちたい. それにより、より深い洞察を得ることが可能になる.

#### 受入基準

1. WHERE 反復改善オプションが有効な場合、THE Reflector SHALL 指定された回数だけ分析を繰り返し、前回のInsightsを次回の入力に含める.
2. WHERE 反復改善オプションが有効な場合、THE Reflector SHALL 最終イテレーションのInsightsをReflectionResultに含める.
3. WHEN 反復回数が指定されない場合、THE Reflector SHALL デフォルトで1回（反復なし）の分析を実行する.

### 要件9: DIコンテナへの登録

**ユーザーストーリー:** 開発者として、Reflectorエージェントを既存のDIコンテナに登録したい. それにより、アプリケーション全体で一貫した依存性管理を行う.

#### 受入基準

1. THE Container SHALL ReflectorAgentをプロバイダとして登録する.
2. WHEN ContainerからReflectorAgentを取得する場合、THE Container SHALL 必要な依存コンポーネント（LLMClient、PlaybookStore）を自動的に注入する.
