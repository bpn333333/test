"""MQL5 実装と Python 実装の一致検証。

この環境には MetaTrader が無いため、照合には本人の MT5 での書き出しが要る。

  1. MT5 で mt5/Scripts/TradeToolsExport.mq5 を対象チャートで実行
  2. 共有フォルダ MQL5/Files/TradeTools/ の parity_ohlc.csv と
     parity_signals.csv を trading-tools/data/ にコピー
  3. python -m pytest tests/test_parity.py -v

データが無い間はスキップされる。**本番運用の前に必ず一度は通すこと。**
ここが一致していないと、チャートの矢印・EAの発注・X配信の内容がずれる。
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tradetools_monitor.config import SignalParams
from tradetools_monitor.signals import scan
from tradetools_monitor.sources import read_ohlc_csv, read_signal_file

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
OHLC_FILE = DATA_DIR / "parity_ohlc.csv"
SIGNAL_FILE = DATA_DIR / "parity_signals.csv"

pytestmark = pytest.mark.skipif(
    not (OHLC_FILE.exists() and SIGNAL_FILE.exists()),
    reason="MT5 の書き出しがまだありません(TradeToolsExport.mq5 を実行してください)",
)


def _mt5_signals():
    """parity_signals.csv は signals.csv と列が違うので個別に読む。"""
    import csv

    from tradetools_monitor.sources import parse_mt5_time

    rows = []
    with SIGNAL_FILE.open(encoding="utf-8", errors="replace") as handle:
        for row in csv.DictReader(handle):
            rows.append(
                {
                    "time": parse_mt5_time(row["bar_time"]),
                    "direction": row["direction"].strip(),
                    "price": float(row["price"]),
                    "sl": float(row["sl"]),
                    "tp": float(row["tp"]),
                }
            )
    return rows


def test_signal_times_and_directions_match():
    bars = read_ohlc_csv(OHLC_FILE)
    symbol = OHLC_FILE.stem.split("_")[0].upper() or "UNKNOWN"

    python_signals = scan(bars, SignalParams(), symbol, "PERIOD_H1")
    mt5_signals = _mt5_signals()

    python_keys = {(s.time, s.direction) for s in python_signals}
    mt5_keys = {(s["time"], s["direction"]) for s in mt5_signals}

    only_python = sorted(python_keys - mt5_keys)
    only_mt5 = sorted(mt5_keys - python_keys)

    assert not only_python and not only_mt5, (
        f"Python 側だけ: {only_python[:5]} / MT5 側だけ: {only_mt5[:5]}\n"
        "指標の平滑化方式(SignalParams.atr_mode)を見直してください"
    )


def test_stop_and_target_levels_match():
    bars = read_ohlc_csv(OHLC_FILE)
    symbol = OHLC_FILE.stem.split("_")[0].upper() or "UNKNOWN"

    python_by_time = {s.time: s for s in scan(bars, SignalParams(), symbol, "PERIOD_H1")}
    tolerance = 1e-3  # 表示桁の丸め分だけ許容する

    for row in _mt5_signals():
        signal = python_by_time.get(row["time"])
        assert signal is not None, f"{row['time']} のシグナルが Python 側にありません"
        assert signal.price == pytest.approx(row["price"], abs=tolerance)
        assert signal.sl == pytest.approx(row["sl"], abs=tolerance)
        assert signal.tp == pytest.approx(row["tp"], abs=tolerance)
