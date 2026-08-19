"""テクニカル指標。MQL5 側と同じ値を出すことが唯一の目的。

MetaTrader の組み込み指標には実装上のクセがある(特に ATR と ADX の平滑化)。
ここでは MT5 の挙動に寄せた実装を既定にしつつ、古典的な Wilder 版も残している。
どちらが正しいかは環境依存なので、必ず mt5/Scripts/TradeToolsExport.mq5 の
出力と tests/test_parity.py で照合してから本番に使うこと。
"""

from __future__ import annotations

from typing import List, Optional, Sequence

Series = List[Optional[float]]


def ema(values: Sequence[float], period: int) -> Series:
    """指数移動平均。MT5 の iMA(MODE_EMA) と同じく最初の値は SMA で種を作る。"""
    if period <= 0:
        raise ValueError("period は1以上にしてください")

    out: Series = [None] * len(values)
    if len(values) < period:
        return out

    alpha = 2.0 / (period + 1.0)
    seed = sum(values[:period]) / period
    out[period - 1] = seed

    prev = seed
    for i in range(period, len(values)):
        prev = values[i] * alpha + prev * (1.0 - alpha)
        out[i] = prev
    return out


def true_range(highs: Sequence[float], lows: Sequence[float], closes: Sequence[float]) -> Series:
    """真の値幅。先頭バーは前足が無いので None。"""
    out: Series = [None] * len(highs)
    for i in range(1, len(highs)):
        prev_close = closes[i - 1]
        out[i] = max(
            highs[i] - lows[i],
            abs(highs[i] - prev_close),
            abs(lows[i] - prev_close),
        )
    return out


def atr(highs: Sequence[float], lows: Sequence[float], closes: Sequence[float],
        period: int, mode: str = "mt5") -> Series:
    """ATR。

    mode="mt5"    : True Range の単純移動平均。MT5 組み込み iATR の挙動。
    mode="wilder" : 古典的な Wilder 平滑化。TradingView など他ツールはこちらが多い。
    """
    if mode not in ("mt5", "wilder"):
        raise ValueError("mode は 'mt5' か 'wilder' です")

    tr = true_range(highs, lows, closes)
    out: Series = [None] * len(highs)
    if len(highs) < period + 1:
        return out

    first = period  # index 1..period の TR が揃う位置
    seed = sum(tr[1:period + 1]) / period
    out[first] = seed

    prev = seed
    for i in range(first + 1, len(highs)):
        if mode == "mt5":
            # SMA を差分更新する。MT5 の ATR.mq5 と同じ形
            prev = prev + (tr[i] - tr[i - period]) / period
        else:
            prev = (prev * (period - 1) + tr[i]) / period
        out[i] = prev
    return out


def adx(highs: Sequence[float], lows: Sequence[float], closes: Sequence[float],
        period: int) -> Series:
    """ADX(Wilder 平滑化)。+DI/-DI の差の平滑値。

    トレンドの有無だけを見るフィルタなので、多少の実装差は判定を大きく変えない。
    それでも本番前にパリティ検証はすること。
    """
    n = len(highs)
    out: Series = [None] * n
    if n < period * 2 + 1:
        return out

    plus_dm = [0.0] * n
    minus_dm = [0.0] * n
    tr = [0.0] * n

    for i in range(1, n):
        up_move = highs[i] - highs[i - 1]
        down_move = lows[i - 1] - lows[i]

        plus_dm[i] = up_move if (up_move > down_move and up_move > 0) else 0.0
        minus_dm[i] = down_move if (down_move > up_move and down_move > 0) else 0.0

        prev_close = closes[i - 1]
        tr[i] = max(
            highs[i] - lows[i],
            abs(highs[i] - prev_close),
            abs(lows[i] - prev_close),
        )

    # Wilder の初期値は単純合計、以降は「前回値 - 前回値/period + 今回値」
    sm_plus = sum(plus_dm[1:period + 1])
    sm_minus = sum(minus_dm[1:period + 1])
    sm_tr = sum(tr[1:period + 1])

    dx: Series = [None] * n

    def _dx(p: float, m: float, t: float) -> Optional[float]:
        if t <= 0:
            return None
        plus_di = 100.0 * p / t
        minus_di = 100.0 * m / t
        denominator = plus_di + minus_di
        if denominator == 0:
            return 0.0
        return 100.0 * abs(plus_di - minus_di) / denominator

    dx[period] = _dx(sm_plus, sm_minus, sm_tr)

    for i in range(period + 1, n):
        sm_plus = sm_plus - sm_plus / period + plus_dm[i]
        sm_minus = sm_minus - sm_minus / period + minus_dm[i]
        sm_tr = sm_tr - sm_tr / period + tr[i]
        dx[i] = _dx(sm_plus, sm_minus, sm_tr)

    # ADX は DX をもう一段平滑化したもの
    first_adx = period * 2 - 1
    window = [v for v in dx[period:first_adx + 1] if v is not None]
    if len(window) < period:
        return out

    prev = sum(window) / len(window)
    out[first_adx] = prev

    for i in range(first_adx + 1, n):
        if dx[i] is None:
            continue
        prev = (prev * (period - 1) + dx[i]) / period
        out[i] = prev
    return out
