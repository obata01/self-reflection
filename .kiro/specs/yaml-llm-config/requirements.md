# 要件定義書

## はじめに

YAML設定ファイルによるLLMクライアント管理機能. 現在の単一LLMクライアント構成から、複数プロバイダ・複数クライアントを名前ベースで解決できる構成へ拡張する. `config/app.yaml` にYAML形式で定義し、Pydanticモデルでバリデーションし、DIコンテナから名前指定で取得可能にする.

## 用語集

- **App_YAML**: `config/app.yaml` に配置されるアプリケーション設定ファイル. LLMクライアント定義を含む.
- **YAML_Loader**: App_YAMLを読み込み、Pydanticモデルに変換するコンポーネント.
- **LLM_Config_Schema**: App_YAMLのLLMクライアント設定を表現するPydantic BaseModelの集合.
- **Chat_Client_Entry**: 個別のLLMクライアント定義. name、provider固有のconfig、default_paramsを持つ.
- **Provider**: LLMサービスの提供元（openai / bedrock / azure）.
- **DI_Container**: dependency-injectorベースの依存性注入コンテナ. 名前ベースでLLMクライアントを解決する.
- **Chat_Model_Registry**: 複数のChatModelインスタンスを名前で管理する辞書型のレジストリ.
- **Env_Reference**: YAML内で `_env` サフィックスのフィールドにより環境変数名を参照する仕組み.

## 要件

### 要件 1: YAML設定ファイルの定義と配置

**ユーザーストーリー:** 開発者として、LLMクライアントの設定をYAMLファイルで一元管理したい. これにより、コード変更なしにプロバイダやモデルの追加・変更ができる.

#### 受入基準

1. THE App_YAML SHALL `config/app.yaml` に配置され、`llms.chat_clients` キー配下にプロバイダ別のクライアント定義リストを保持する.
2. WHEN App_YAMLにChat_Client_Entryが定義される場合、THE Chat_Client_Entry SHALL name、config、default_paramsの3フィールドを持つ.
3. WHEN プロバイダがbedrockの場合、THE Chat_Client_Entry SHALL configにmodel_idとregion_nameを含む.
4. WHEN プロバイダがazureの場合、THE Chat_Client_Entry SHALL configにmodel、azure_deployment、azure_endpoint_env、api_key_env、openai_api_versionを含む.
5. WHEN プロバイダがopenaiの場合、THE Chat_Client_Entry SHALL configにmodelとapi_key_envを含む.

### 要件 2: PydanticスキーマによるYAMLバリデーション

**ユーザーストーリー:** 開発者として、YAML設定の構造をPydanticモデルで厳密に定義したい. これにより、設定ミスを起動時に検出できる.

#### 受入基準

1. THE LLM_Config_Schema SHALL `src/common/schema/` 配下にPydantic BaseModelとして定義される.
2. WHEN App_YAMLが読み込まれた場合、THE YAML_Loader SHALL YAMLの内容をLLM_Config_Schemaでバリデーションする.
3. IF App_YAMLのバリデーションに失敗した場合、THEN THE YAML_Loader SHALL Pydantic ValidationErrorを発生させ、不正なフィールドの情報を含める.
4. THE LLM_Config_Schema SHALL プロバイダごとに異なるconfigフィールド構造を許容するため、config部分をdict[str, Any]型で定義する.
5. WHEN default_paramsが省略された場合、THE LLM_Config_Schema SHALL 空の辞書をデフォルト値として使用する.

### 要件 3: YAML設定ファイルの読み込み

**ユーザーストーリー:** 開発者として、YAML設定ファイルを読み込んでPydanticモデルに変換する仕組みが欲しい. これにより、型安全に設定値を利用できる.

#### 受入基準

1. THE YAML_Loader SHALL `config/app.yaml` を読み込み、LLM_Config_Schemaのインスタンスを返す.
2. IF App_YAMLファイルが存在しない場合、THEN THE YAML_Loader SHALL FileNotFoundErrorを発生させ、ファイルパスを含むエラーメッセージを提供する.
3. IF App_YAMLのYAML構文が不正な場合、THEN THE YAML_Loader SHALL yaml.YAMLErrorをそのまま伝播させる.
4. THE YAML_Loader SHALL 既存のSectionLoaderと同様のパターン（Pathベースのファイル読み込み + yaml.safe_load + Pydanticモデル変換）に従う.

### 要件 4: 環境変数の解決

**ユーザーストーリー:** 開発者として、APIキーやエンドポイントなどの機密情報をYAMLに直接記載せず、環境変数で管理したい. これにより、セキュリティを確保しつつ設定を柔軟に管理できる.

#### 受入基準

1. WHEN Chat_Client_Entryのconfigに `_env` サフィックスのフィールドが含まれる場合、THE YAML_Loader SHALL そのフィールド値を環境変数名として解釈し、`os.getenv()` で実行時に解決する.
2. WHEN 参照された環境変数が未設定の場合、THE YAML_Loader SHALL Noneを返し、エラーを発生させない（bedrockのように環境変数不要なプロバイダが存在するため）.
3. THE YAML_Loader SHALL `_env` サフィックスのフィールドを解決後、サフィックスを除いたキー名で値を提供する（例: `api_key_env` → `api_key` として解決値を提供）.

### 要件 5: DIコンテナへの複数LLMクライアント登録

**ユーザーストーリー:** 開発者として、DIコンテナから名前を指定してLLMクライアントを取得したい. これにより、エージェントごとに異なるLLMを使い分けられる.

#### 受入基準

1. THE DI_Container SHALL App_YAMLから読み込んだ全Chat_Client_Entryに対応するChatModelインスタンスをChat_Model_Registryに登録する.
2. WHEN Chat_Model_Registryからクライアントが要求された場合、THE DI_Container SHALL Chat_Client_Entryのnameフィールドをキーとしてインスタンスを返す.
3. IF 存在しないnameが指定された場合、THEN THE DI_Container SHALL KeyErrorを発生させ、指定されたnameと利用可能なname一覧を含むエラーメッセージを提供する.
4. THE DI_Container SHALL 各ChatModelインスタンスをSingletonとして管理し、同一nameに対して同一インスタンスを返す.
5. THE DI_Container SHALL 既存のchat_modelプロバイダとの後方互換性を維持し、既存のllm_clientプロバイダを引き続き動作させる.
6. THE DI_Container SHALL 既存の `create_chat_model` ファクトリ関数を活用してChatModelインスタンスを生成する.

### 要件 6: LLMクライアントのデフォルトパラメータ適用

**ユーザーストーリー:** 開発者として、YAMLで定義したdefault_params（temperature、max_tokens等）をChatModel生成時に適用したい. これにより、モデルごとの推論パラメータを設定ファイルで管理できる.

#### 受入基準

1. WHEN ChatModelが生成される場合、THE DI_Container SHALL Chat_Client_Entryのdefault_paramsをcreate_chat_modelのkwargsとして渡す.
2. WHEN default_paramsにNone値のフィールドが含まれる場合、THE DI_Container SHALL そのフィールドをkwargsから除外する.
