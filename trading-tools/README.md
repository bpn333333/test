# TradeTools — FX(MT5)向けトレードツール一式

4つのツールを**1つの判定ロジックの上に**構築したもの。

| # | ツール | 実体 | 状態 |
|---|---|---|---|
| ① | サインツール | `mt5/Indicators/TradeToolsSignal.mq5` | 実装済み・**MT5未検証** |
| ② | EA | `mt5/Experts/TradeToolsEA.mq5` | 実装済み・**MT5未検証** |
| ③ | 市場モニタリング | `monitor/tradetools_monitor/` | 実装済み・テスト通過 |
| ④ | X配信 | `distribution/tradetools_x/` | 実装済み・テスト通過(ドライラン) |

## この時点で「できていること」と「できていないこと」

**できていること**

- 4ツールが同じ判定ロジック(`SignalCore.mqh`)を共有する構造
- Python 側 60 件のテストが通る(指標・判定・取り込み・文面生成・配信制御)
- 免責の自動付与、断定表現の検出、文字数超過の検出、重複配信の防止

**できていないこと(ここを飛ばさないこと)**

- **MQL5 のコンパイルと動作確認は未実施。** この開発環境に MetaTrader が無い。
  MetaEditor でのコンパイル確認は本人の PC で必要
- **MQL5 と Python の判定一致は未検証。** `tests/test_parity.py` を
  MT5 の書き出しデータで通すまで、両者がずれている可能性がある
- **バックテストは未実施。** 現在のロジックに優位性がある根拠はまだ何も無い
- **X API への実接続は未確認。** この環境から外部ネットワークに出られないため

## 使い方

導入手順は [`docs/SETUP.md`](docs/SETUP.md)。設計の考え方は
[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)。

```bash
cd trading-tools
python -m pytest            # テスト
PYTHONPATH=monitor python -m tradetools_monitor --once   # 監視を1回実行

# バックテスト(data/ に <SYMBOL>_<TIMEFRAME>.csv が必要)
PYTHONPATH=monitor python -m tradetools_monitor.backtest \
  --symbols USDJPY EURUSD GBPUSD --timeframe PERIOD_H1 --oos 0.7
```

## 事業として進めるなら

| ドキュメント | 内容 |
|---|---|
| [`docs/BUSINESS_MODEL.md`](docs/BUSINESS_MODEL.md) | 事業構造・収益源・ユニットエコノミクス・ロードマップ・未決事項 |
| [`docs/MARKET_RESEARCH.md`](docs/MARKET_RESEARCH.md) | 販売プラットフォーム・ブローカー・Kindle・配信チャネルの調査 |
| [`docs/COMPLIANCE.md`](docs/COMPLIANCE.md) | 日本・米国の規制論点と、配信表現のチェックリスト |

有償でシグナルを配信すると、日本では金商法の投資助言・代理業、
米国では CTA 登録が論点になる。**何を有償にするのか(ツールか、シグナルか)を
先に決めないと、作るものも売り方も変わる。**

## 次にやること(順番に意味がある)

1. MetaEditor で3つの `.mq5` をコンパイルし、エラーを潰す
2. `TradeToolsExport.mq5` を実行 → `data/` にコピー → `pytest tests/test_parity.py`
3. ストラテジーテスターで複数通貨ペア・2年以上のバックテスト
4. 結果を見てロジックを見直す(**ここで初めて優位性の議論ができる**)
5. デモ口座で1ヶ月フォワード
6. 有償化の範囲を決める(`docs/COMPLIANCE.md`)
7. X配信をドライランで文面確認 → 本番

## ディレクトリ

```
trading-tools/
├── mt5/
│   ├── Include/TradeTools/
│   │   ├── SignalCore.mqh      判定ロジック(唯一の定義)
│   │   ├── RiskManager.mqh     ロット計算・発注前ガード
│   │   └── SignalFile.mqh      Python への受け渡し
│   ├── Indicators/TradeToolsSignal.mq5   ① サインツール
│   ├── Experts/TradeToolsEA.mq5          ② EA
│   └── Scripts/
│       ├── TradeToolsExport.mq5          パリティ検証用の書き出し
│       └── TradeToolsExportData.mq5      バックテスト用OHLCの書き出し
├── monitor/tradetools_monitor/            ③ 市場モニタリング
│   ├── indicators.py   EMA / ATR / ADX
│   ├── signals.py      SignalCore.mqh の鏡像
│   ├── sources.py      signals.csv / OHLC CSV の取り込み
│   ├── backtest.py     バックテストエンジンと CLI
│   ├── notifier.py     コンソール・ファイル・Webhook
│   └── runner.py       監視ループと CLI
├── distribution/tradetools_x/             ④ X配信
│   ├── composer.py     本文生成 + 免責・禁止表現・文字数の検査
│   ├── client.py       X API v2 / ドライラン
│   └── publisher.py    重複排除・投稿間隔・1日上限
├── tests/
└── docs/
```

## 免責

このリポジトリのコードは投資助言ではない。使用によって生じた損失について
作者は責任を負わない。実口座で動かす前に、必ずデモ口座で検証すること。
