"""シグナルの取り込み口。

signal_file : MT5(インジケータ/EA)が書いた CSV を追跡する。本番はこれ。
csv         : ローカルの OHLC から Python 側で判定する。検証・バックテスト用。

MT5 端末が動いている PC 以外(VPS 上の配信サーバなど)では、共有フォルダを
同期するか、この CSV を転送する運用にする。
"""

from __future__ import annotations

import csv
import io
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Optional, Sequence

from .config import MonitorConfig, SignalParams
from .signals import Bar, Signal, evaluate

MT5_TIME_FORMATS = ("%Y.%m.%d %H:%M:%S", "%Y.%m.%d %H:%M")


def parse_mt5_time(text: str) -> datetime:
    """MT5 の TimeToString 出力を読む。"""
    value = text.strip()
    for fmt in MT5_TIME_FORMATS:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    # ISO 形式で書かれていた場合の保険
    return datetime.fromisoformat(value)


def read_signal_file(path: Path) -> List[Signal]:
    """MT5 が追記した signals.csv を全件読む。

    書き込み途中の行に当たることがあるため、壊れた行は落として続行する
    (次のポーリングで完全な行として読み直せる)。
    """
    if not path.exists():
        return []

    text = path.read_text(encoding="utf-8", errors="replace")
    rows = csv.DictReader(io.StringIO(text))

    out: List[Signal] = []
    for row in rows:
        try:
            direction = (row["direction"] or "").strip()
            if direction not in ("BUY", "SELL"):
                continue
            out.append(
                Signal(
                    direction=direction,
                    time=parse_mt5_time(row["bar_time"]),
                    symbol=(row["symbol"] or "").strip(),
                    timeframe=(row["timeframe"] or "").strip(),
                    price=float(row["price"]),
                    sl=float(row["sl"]),
                    tp=float(row["tp"]),
                    atr=float(row["atr"]),
                    adx=float(row["adx"]),
                    reason=(row.get("reason") or "").strip(),
                )
            )
        except (KeyError, TypeError, ValueError):
            continue
    return out


def read_ohlc_csv(path: Path) -> List[Bar]:
    """time,open,high,low,close 形式の CSV を読む(MT5 のエクスポートと同形式)。"""
    bars: List[Bar] = []
    with path.open(encoding="utf-8", errors="replace") as handle:
        for row in csv.DictReader(handle):
            try:
                bars.append(
                    Bar(
                        time=parse_mt5_time(row["time"]),
                        open=float(row["open"]),
                        high=float(row["high"]),
                        low=float(row["low"]),
                        close=float(row["close"]),
                    )
                )
            except (KeyError, TypeError, ValueError):
                continue
    bars.sort(key=lambda b: b.time)
    return bars


def signals_from_csv_dir(directory: Path, symbols: Sequence[str], timeframe: str,
                         params: SignalParams) -> List[Signal]:
    """<csv_dir>/<SYMBOL>_<TIMEFRAME>.csv を読み、最新の確定足だけ判定する。"""
    out: List[Signal] = []
    for symbol in symbols:
        path = directory / f"{symbol}_{timeframe}.csv"
        if not path.exists():
            continue
        bars = read_ohlc_csv(path)
        if len(bars) < params.warmup_bars:
            continue
        signal = evaluate(bars, params, symbol, timeframe, len(bars) - 1)
        if signal is not None and signal.direction != "NONE":
            out.append(signal)
    return out


def collect(config: MonitorConfig) -> List[Signal]:
    """設定に従ってシグナルを集める。"""
    if config.source == "signal_file":
        return read_signal_file(config.resolved_signal_file())
    if config.source == "csv":
        return signals_from_csv_dir(
            Path(config.csv_dir).expanduser(), config.symbols, config.timeframe, config.params
        )
    raise ValueError(f"未知の source: {config.source}")
