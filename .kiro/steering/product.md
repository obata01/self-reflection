---
inclusion: always
---

# プロダクト概要

ACE（Agentic Context Engineering）フレームワークに基づく、LLMエージェントの自己内省システム.

## コンセプト

エージェントが推論中に得た経験から学び、Playbook（知識ベース）として蓄積・改善する自己内省アーキテクチャ.

## 3つのエージェント

- Generator: タスク実行・推論を行う. Query + Playbookを入力とし、Trajectory（推論過程）を出力する.
- Reflector: 成功/失敗を分析し、教訓（Insights）を抽出する.
- Curator: 洞察をPlaybookに統合・整理し、Delta Context Items（更新差分）を生成する.

## 主要データモデル

- Playbook: 知識ベース全体. Bulletのコンテナ. データセットごとにJSONファイルで管理.
- Bullet: 個別の知識単位. helpful/harmfulカウンターによる信頼度スコアを持つ.
- Section: Bulletの分類. データセットごとに設定ファイルで定義可能.

## 検索方式

Playbook全体注入ではなく、ハイブリッド検索（Numpyベクトル近傍探索 + BM25全文検索）で関連Bulletのみ注入する方針.
