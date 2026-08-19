# 導入手順

## 1. MT5 側(サインツール・EA)

1. MT5 で **ファイル → データフォルダを開く**
2. 次のようにコピーする

   | このリポジトリ | コピー先 |
   |---|---|
   | `mt5/Include/TradeTools/` | `MQL5/Include/TradeTools/` |
   | `mt5/Indicators/TradeToolsSignal.mq5` | `MQL5/Indicators/` |
   | `mt5/Experts/TradeToolsEA.mq5` | `MQL5/Experts/` |
   | `mt5/Scripts/TradeToolsExport.mq5` | `MQL5/Scripts/` |

3. MetaEditor で3つの `.mq5` をコンパイル(F7)。エラー0を確認
4. MT5 を再起動 → ナビゲータからチャートにドラッグ

### サインツールの設定

- 通知はポップアップ・スマホ通知・CSV書き出しを個別に切り替えられる
- スマホ通知を使う場合は MT5 の **ツール → オプション → 通知** で
  MetaQuotes ID を設定しておく

### EA の設定(いきなり実弾を入れない)

順番を飛ばさないこと。

1. **ストラテジーテスター**でバックテスト。期間は最低2年、複数通貨ペア
2. **デモ口座**で最低1ヶ月フォワード。バックテストと乖離がないか見る
3. 実口座は最小ロットから。`InpRiskPercent` は 1.0 のまま触らない
4. チャート右上の 😐 が 🙂 になっていること(自動売買が有効)を毎回確認

## 2. Python 側(モニタリング・X配信)

```bash
cd trading-tools
python -m pip install -r monitor/requirements.txt

# 設定ファイルを作る
python -c "import sys; sys.path.insert(0,'monitor'); \
  from tradetools_monitor.config import MonitorConfig; \
  MonitorConfig().dump('config.json')"
```

`config.json` の `signal_file` を、MT5 の**共有データフォルダ**の
`Files/TradeTools/signals.csv` に合わせる。パスは MT5 の
**ファイル → データフォルダを開く** から辿れる(`Terminal/Common/Files/`)。

### 実行

```bash
cd trading-tools

# 1回だけ実行して確認
PYTHONPATH=monitor python -m tradetools_monitor --config config.json --once

# 常時監視
PYTHONPATH=monitor python -m tradetools_monitor --config config.json
```

### X配信を有効にする

1. X Developer Portal でアプリを作り、**Read and write** 権限にする
2. API Key / Secret と Access Token / Secret を発行
3. 環境変数に入れる(コードには絶対に書かない)

```bash
export X_API_KEY=...
export X_API_SECRET=...
export X_ACCESS_TOKEN=...
export X_ACCESS_TOKEN_SECRET=...
python -m pip install -r distribution/requirements.txt
```

4. `config.json` の `publish_to_x` を `true` にする
5. **まずドライランで文面を確認する**(`--live` を付けない)

```bash
PYTHONPATH=monitor python -m tradetools_monitor --config config.json --once
cat data/x_dryrun.log
```

6. 文面に問題がなければ `--live` を付けて本番投稿

料金プランと投稿上限は変動が激しいため、運用開始前に開発者ダッシュボードで
現時点の上限を確認すること。

## 3. パリティ検証(本番前に必ず1回)

MQL5 と Python が同じ判定をしているかを確認する。

1. MT5 の対象チャートで `TradeToolsExport` スクリプトを実行
2. 共有フォルダ `Files/TradeTools/parity_ohlc.csv` と `parity_signals.csv` を
   このリポジトリの `data/` にコピー
3. 検証

```bash
cd trading-tools
python -m pytest tests/test_parity.py -v
```

ここが一致していないと、チャートの矢印・EAの発注・Xの投稿がずれる。
不一致が出たら `config.json` の `params.atr_mode` を `wilder` に変えて再実行し、
それでも合わなければ `docs/ARCHITECTURE.md` の手順で両実装を突き合わせる。

## 4. バックテスト(手法の検証)

### データの用意

1. MT5 の **ツール → オプション → チャート** で
   「ヒストリー内の最大バー数」を無制限にする
2. 対象銘柄・対象時間軸のチャートを開き、**過去まで十分にスクロール**して
   ヒストリーをダウンロードする(スクロールしないと過去足が入らない)
3. そのチャートで `TradeToolsExportData` スクリプトを実行
   - 既定で `USDJPY,EURUSD,GBPUSD` を書き出す
   - 時間軸はチャートの時間軸を使う(入力で変更可)
4. 共有フォルダ `MQL5/Files/TradeTools/<SYMBOL>_<TIMEFRAME>.csv` を
   このリポジトリの `data/` にコピー

### 実行

```bash
cd trading-tools

# 全期間
PYTHONPATH=monitor python -m tradetools_monitor.backtest   --symbols USDJPY EURUSD GBPUSD --timeframe PERIOD_H1

# アウトオブサンプル検証(前7割で見て、残り3割で確認)
PYTHONPATH=monitor python -m tradetools_monitor.backtest   --symbols USDJPY EURUSD GBPUSD --timeframe PERIOD_H1 --oos 0.7

# 結果をJSONで保存
PYTHONPATH=monitor python -m tradetools_monitor.backtest --json data/report.json
```

### 取引条件の設定

既定値は仮のものなので、**ブローカーの実際の条件に合わせること。**
設定JSONに `backtest` を書いて `--config` で渡す。

```json
{
  "params": { "ema_fast": 12, "ema_slow": 48 },
  "backtest": {
    "initial_balance": 1000000,
    "risk_percent": 1.0,
    "spread_points": 10,
    "slippage_points": 2,
    "commission_per_lot": 0,
    "swap_long_points": 0,
    "swap_short_points": 0,
    "quote_to_account_rate": 1.0
  }
}
```

- `spread_points` は**平均ではなく、実際に約定する時間帯のスプレッド**を入れる
- `quote_to_account_rate` は決済通貨→口座通貨の換算レート。
  口座が円で USDJPY を検証するなら 1.0。EURUSD/GBPUSD は決済通貨が USD なので
  **USDJPY のレート(例: 150)** を入れる。固定レート近似である点に注意

### エンジンの前提(結果を読むときに知っておくこと)

- **先読みをしない。** 確定足の終値で判定し、エントリーは次の足の始値
- **同一足で損切りと利確の両方に触れた場合は損切りを優先**(最悪ケース)。
  `worst_case_intrabar: false` で反転できるが、既定は悲観側
- 日足を跨いだ分だけスワップを差し引く
- **ティックデータではなく OHLC ベース。** 足の中の値動きは再現されない。
  短期の手法ほど実運用との乖離が大きくなる

## 5. 常時稼働

- **EA**: MT5 を落とすと止まる。FX業者提供のVPSか、Windows VPS を使う
- **モニタリング/配信**: Linux VPS で `systemd` か `nohup`。
  MT5 と別サーバーにする場合は `signals.csv` を同期する
