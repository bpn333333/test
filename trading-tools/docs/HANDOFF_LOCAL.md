# ローカル環境への引き継ぎプロンプト

クラウドセッション（claude.ai/code）からローカルの Claude Code へ移るときに使う。
以下のコードブロックの内容を、ローカルセッションの最初のメッセージに貼り付ける。

**更新のルール:** 状況が変わったらこのファイルを更新する。
特に「まだできていないこと」と「次にやること」は、作業のたびに現状と合わせる。

---

```
FX/MT5向けトレードツールの開発を、クラウドセッションから引き継ぎます。
このセッションでは会話の文脈が引き継がれていないため、まず状況を把握してください。

## 最初にやること

以下を読んでから作業を始めてください。

1. trading-tools/README.md
2. trading-tools/docs/ARCHITECTURE.md
3. trading-tools/docs/BUSINESS_MODEL.md
4. PLAN.md（第6章がトレードツールの位置づけ）

リポジトリ: https://github.com/bpn333333/test
作業ブランチ: claude/trading-tools-four-types-7hcpuu
PR: https://github.com/bpn333333/test/pull/2 （ドラフト）

## これまでに作ったもの

trading-tools/ 配下に、MT5向けツール4種と検証環境が実装済みです。

- mt5/Include/TradeTools/SignalCore.mqh … 判定ロジックの唯一の定義
- mt5/Include/TradeTools/RiskManager.mqh … ロット計算・発注前ガード
- mt5/Indicators/TradeToolsSignal.mq5 … サインツール
- mt5/Experts/TradeToolsEA.mq5 … EA
- mt5/Scripts/TradeToolsExportData.mq5 … バックテスト用OHLC書き出し
- monitor/tradetools_monitor/ … 市場モニタリング + バックテストエンジン
- distribution/tradetools_x/ … X配信
- docs/INDICATORS.md … 主要インジケーター50種と売買サインの一覧

設計上の約束:
- 判定ロジックは SignalCore.mqh の1箇所だけに置く。インジケータもEAもそこを呼ぶ
- monitor/tradetools_monitor/signals.py はその Python 鏡像。
  両者の一致を tests/test_parity.py で検証する（データがあれば）
- バックテストは先読みしない（確定足で判定、次の足の始値でエントリー）
- 同一足で損切りと利確の両方に触れたら損切りを優先（悲観側）

Python側テストは66件が通ります（python -m pytest）。
Python標準ライブラリのみで動きます。

## まだできていないこと

- MQL5のコンパイル・動作確認（クラウド環境にMT5が無かったため未実施）
- MQL5とPythonの判定一致の検証（tests/test_parity.py がデータ待ちでスキップ状態）
- バックテストの実行（data/ が空。相場データが無い）
- パラメータ探索（グリッドサーチ）の機能
- Python側の指標は EMA / ATR / ADX のみ実装。
  RSI・ボリンジャーバンド・ストキャス・MACD・一目均衡表などは未実装

## このローカル環境で新しくできること

Windows + MT5端末が起動していれば、以下が可能になります。

- MetaTrader5 Pythonパッケージで相場データを直接取得（CSV受け渡しが不要）
- terminal64.exe /config:～.ini でストラテジーテスターをコマンドラインから実行
- パラメータ探索の全自動化

まず接続確認をしてください:
  pip install MetaTrader5
  python -c "import MetaTrader5 as mt5; mt5.initialize(); print(mt5.terminal_info())"

## 作業ルール（重要）

- 意見や提案は不要。聞かれたことにファクトで答えること
- 指示されていない作業を勝手に進めないこと。指示されたことだけを実行する
- 作業の追加や次の一手の提案はしない

## 決まっていること

- 対象通貨ペア: USDJPY / EURUSD / GBPUSD
- 戦略は3種類（本人がロジックを考案し、Claudeが過去データで検証する）
  ① スキャルピング: 15分足
  ② デイトレード: マルチタイムフレーム分析で1日20-40pips
  ③ スイング: 介入警戒レート付近や日足で100-500pips
  将来的に①②③を統合したEAも作る
- 用途は商品化・配信前提（金商法の論点は docs/COMPLIANCE.md）

## 次にやること

過去チャートで、インジケーター毎の有効性を検証する。
docs/INDICATORS.md の一覧にある各インジケーターの売買サインに従って
過去データでトレードした場合の成績を出す。

具体的な対象インジケーター・時間軸・期間は、こちらから指示します。
まずは上記の読み込みとMT5接続の確認まで行い、そこで止まってください。
```

---

## 環境の違い（参考）

| | クラウド（claude.ai/code） | ローカル（Windows） |
|---|---|---|
| MT5端末へのアクセス | 不可 | 可 |
| 相場データの取得 | CSVを手で受け渡し | `copy_rates_from()` で直接 |
| ストラテジーテスター | 不可 | `terminal64.exe /config:～.ini` |
| 外部ネットワーク | 遮断（検索のみ可） | 制限なし |
| 稼働時間 | 常時 | PCの起動中のみ |
| 環境の永続性 | コンテナは一定時間で破棄 | 永続 |

`MetaTrader5` Pythonパッケージの公式対応は **Windows のみ**。
Mac の場合、MT5本体は CrossOver 等で動くが、このパッケージは動かない。

## 引き継がれないもの

- 会話の文脈（このファイルを読ませることで補う）
- Google ドライブ / Gmail 等のコネクタ接続（ローカル側で個別に設定が必要）

## 関連ファイル

| ファイル | 内容 |
|---|---|
| `README.md` | プロジェクト全体と現状 |
| `docs/ARCHITECTURE.md` | 4ツールの構成と設計判断 |
| `docs/SETUP.md` | 導入手順・バックテストの実行方法 |
| `docs/INDICATORS.md` | インジケーター50種と売買サイン |
| `docs/BUSINESS_MODEL.md` | 事業構造・ロードマップ・未決事項 |
| `docs/MARKET_RESEARCH.md` | 販売・配信チャネルの調査 |
| `docs/COMPLIANCE.md` | 規制論点のチェックリスト |
| `../PLAN.md` | 案件獲得プロジェクトとの優先順位（第6章） |
