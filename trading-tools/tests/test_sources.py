from datetime import datetime

import pytest

from tradetools_monitor.config import MonitorConfig, SignalParams
from tradetools_monitor.sources import (
    collect,
    parse_mt5_time,
    read_ohlc_csv,
    read_signal_file,
    signals_from_csv_dir,
)

HEADER = (
    "signal_id,emitted_at,bar_time,symbol,timeframe,direction,price,sl,tp,"
    "atr,adx,source,reason\n"
)
ROW = (
    'USDJPY-PERIOD_H1-2026.02.11 18:00-BUY,2026.02.11 19:00:02,'
    '2026.02.11 18:00:00,USDJPY,PERIOD_H1,BUY,157.533,156.900,158.700,'
    '0.422,48.4,indicator,"EMA12/48 上抜け・終値がEMA200の上・ADX 48.4"\n'
)


def test_parse_mt5_time_handles_both_formats():
    assert parse_mt5_time("2026.02.11 18:00:00") == datetime(2026, 2, 11, 18, 0)
    assert parse_mt5_time("2026.02.11 18:00") == datetime(2026, 2, 11, 18, 0)


def test_read_signal_file_parses_a_row(tmp_path):
    path = tmp_path / "signals.csv"
    path.write_text(HEADER + ROW, encoding="utf-8")

    signals = read_signal_file(path)
    assert len(signals) == 1

    signal = signals[0]
    assert signal.symbol == "USDJPY"
    assert signal.direction == "BUY"
    assert signal.price == pytest.approx(157.533)
    assert signal.time == datetime(2026, 2, 11, 18, 0)
    # reason にカンマが含まれていても列がずれないこと
    assert "EMA12/48" in signal.reason


def test_signal_id_round_trips_through_the_file(tmp_path):
    path = tmp_path / "signals.csv"
    path.write_text(HEADER + ROW, encoding="utf-8")

    signal = read_signal_file(path)[0]
    assert signal.signal_id == "USDJPY-PERIOD_H1-2026.02.11 18:00-BUY"


def test_missing_file_returns_empty_list(tmp_path):
    assert read_signal_file(tmp_path / "nope.csv") == []


def test_broken_and_partial_rows_are_skipped(tmp_path):
    path = tmp_path / "signals.csv"
    path.write_text(HEADER + ROW + "壊れた行,途中まで\n" + ROW.replace("BUY", "SELL"),
                    encoding="utf-8")

    signals = read_signal_file(path)
    assert [s.direction for s in signals] == ["BUY", "SELL"]


def test_rows_without_direction_are_ignored(tmp_path):
    path = tmp_path / "signals.csv"
    path.write_text(HEADER + ROW.replace(",BUY,", ",NONE,"), encoding="utf-8")
    assert read_signal_file(path) == []


def test_read_ohlc_csv_sorts_by_time(tmp_path):
    path = tmp_path / "ohlc.csv"
    path.write_text(
        "time,open,high,low,close\n"
        "2026.02.11 19:00:00,2,2,2,2\n"
        "2026.02.11 18:00:00,1,1,1,1\n",
        encoding="utf-8",
    )
    bars = read_ohlc_csv(path)
    assert [b.close for b in bars] == [1.0, 2.0]


def test_csv_dir_source_needs_enough_history(tmp_path):
    path = tmp_path / "USDJPY_PERIOD_H1.csv"
    path.write_text("time,open,high,low,close\n2026.02.11 18:00:00,1,1,1,1\n",
                    encoding="utf-8")

    result = signals_from_csv_dir(tmp_path, ["USDJPY"], "PERIOD_H1", SignalParams())
    assert result == []


def test_collect_rejects_unknown_source(tmp_path):
    config = MonitorConfig(source="mystery")
    with pytest.raises(ValueError, match="未知の source"):
        collect(config)
