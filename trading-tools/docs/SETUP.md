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

## 4. 常時稼働

- **EA**: MT5 を落とすと止まる。FX業者提供のVPSか、Windows VPS を使う
- **モニタリング/配信**: Linux VPS で `systemd` か `nohup`。
  MT5 と別サーバーにする場合は `signals.csv` を同期する
