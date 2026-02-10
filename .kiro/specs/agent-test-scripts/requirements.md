# Requirements Document

## Introduction

Curator、Generator、Reflectorの3つのエージェントを個別にテスト実行するための簡易スクリプトをsrc/scriptsディレクトリに追加する.
PoCフェーズにおける動作確認用途であり、LLM APIを実際に呼び出して一通りの動作を検証できることを目的とする.

## Glossary

- **Test_Script**: エージェントの動作確認を行うPythonスクリプト. src/scripts/ディレクトリに配置される.
- **Generator_Agent**: Query + Playbookを入力とし、Trajectory（推論過程）を出力するエージェント.
- **Reflector_Agent**: Trajectory + ground_truth + test_reportを入力とし、ReflectionResult（教訓・Bullet評価）を出力するエージェント.
- **Curator_Agent**: ReflectionResultを入力とし、CurationResult（Playbook更新差分）を出力するエージェント.
- **DI_Container**: dependency-injectorベースの依存性注入コンテナ. 各エージェントのインスタンス生成を管理する.
- **Playbook**: 知識ベース全体. BulletのコンテナとしてデータセットごとにJSON形式で管理される.
- **Trajectory**: Generatorの推論過程を記録するデータモデル.
- **ReflectionResult**: Reflectorの分析結果を表すデータモデル.
- **CurationResult**: Curatorの出力を表すデータモデル.

## Requirements

### Requirement 1: Generator動作確認スクリプト

**User Story:** 開発者として、Generatorエージェントの動作を手軽に確認したい. クエリを与えてTrajectoryが正常に生成されることを検証できるようにする.

#### Acceptance Criteria

1. WHEN Test_Script が実行された場合, THE Test_Script SHALL dotenvを使用して.envファイルから環境変数を読み込む
2. WHEN Test_Script が実行された場合, THE Test_Script SHALL DI_Containerを初期化し、設定を読み込む
3. WHEN Generator_Agent にクエリとデータセット名を渡した場合, THE Test_Script SHALL Generator_Agent.run()を呼び出しTrajectoryを取得する
4. WHEN Trajectory が取得された場合, THE Test_Script SHALL Trajectoryのquery、status、generated_answer、reasoning_steps、used_bullet_idsを表示する
5. IF Generator_Agent の実行中にエラーが発生した場合, THEN THE Test_Script SHALL エラー内容をログに出力し、異常終了する

### Requirement 2: Reflector動作確認スクリプト

**User Story:** 開発者として、Reflectorエージェントの動作を手軽に確認したい. Trajectoryと正解データを与えてReflectionResultが正常に生成されることを検証できるようにする.

#### Acceptance Criteria

1. WHEN Test_Script が実行された場合, THE Test_Script SHALL dotenvを使用して.envファイルから環境変数を読み込む
2. WHEN Test_Script が実行された場合, THE Test_Script SHALL DI_Containerを初期化し、設定を読み込む
3. WHEN Reflector_Agent にTrajectory、ground_truth、test_reportを渡した場合, THE Test_Script SHALL Reflector_Agent.run()を呼び出しReflectionResultを取得する
4. WHEN ReflectionResult が取得された場合, THE Test_Script SHALL 各Insightのkey_insight、reasoning、error_identificationを表示する
5. WHEN ReflectionResult が取得された場合, THE Test_Script SHALL 各BulletEvaluationのbullet_id、tag、reasonを表示する
6. IF Reflector_Agent の実行中にエラーが発生した場合, THEN THE Test_Script SHALL エラー内容をログに出力し、異常終了する

### Requirement 3: Curator動作確認スクリプト

**User Story:** 開発者として、Curatorエージェントの動作を手軽に確認したい. ReflectionResultを与えてCurationResultが正常に生成されることを検証できるようにする.

#### Acceptance Criteria

1. WHEN Test_Script が実行された場合, THE Test_Script SHALL dotenvを使用して.envファイルから環境変数を読み込む
2. WHEN Test_Script が実行された場合, THE Test_Script SHALL DI_Containerを初期化し、設定を読み込む
3. WHEN Curator_Agent にReflectionResultとデータセット名を渡した場合, THE Test_Script SHALL Curator_Agent.run()を呼び出しCurationResultを取得する
4. WHEN CurationResult が取得された場合, THE Test_Script SHALL 各DeltaContextItemのtype、section、content、reasoningを表示する
5. WHEN CurationResult が取得された場合, THE Test_Script SHALL bullets_before、bullets_after、summaryを表示する
6. IF Curator_Agent の実行中にエラーが発生した場合, THEN THE Test_Script SHALL エラー内容をログに出力し、異常終了する

### Requirement 4: 共通パターンの準拠

**User Story:** 開発者として、既存スクリプトと一貫したパターンでスクリプトを利用したい. 既存のsrc/scripts/配下のスクリプトと同じ構成パターンに従うようにする.

#### Acceptance Criteria

1. THE Test_Script SHALL sys.path.insert(0, str(Path(__file__).parent.parent))でルートパスを追加する
2. THE Test_Script SHALL src.common.lib.logging.getLogger()を使用してロガーを取得する
3. THE Test_Script SHALL main()関数をエントリポイントとして定義する
4. THE Test_Script SHALL if __name__ == "__main__": main() パターンで実行する
5. THE Test_Script SHALL appworldデータセットを使用する
