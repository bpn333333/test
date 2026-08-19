"""SignalCore.mqh の Python 鏡像。

MQL5 側とこのファイルは同じ入力に対して同じ出力を返さなければならない。
判定ロジックを変えるときは、必ず両方を同時に変更すること。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Sequence

from .config import SignalParams
from .indicators import adx as calc_adx
from .indicators import atr as calc_atr
from .indicators import ema as calc_ema

BUY = "BUY"
SELL = "SELL"
NONE = "NONE"


@dataclass
class Bar:
    time: datetime
    open: float
    high: float
    low: float
    close: float


@dataclass
class Signal:
    """TTSignal と同じ内容。"""

    direction: str
    time: datetime
    symbol: str
    timeframe: str
    price: float
    sl: float
    tp: float
    atr: float
    adx: float
    reason: str

    @property
    def signal_id(self) -> str:
        """SignalFile.mqh の TTSignalId と同じ形式。重複排除のキー。"""
        stamp = self.time.strftime("%Y.%m.%d %H:%M")
        return f"{self.symbol}-{self.timeframe}-{stamp}-{self.direction}"

    @property
    def risk_reward(self) -> float:
        risk = abs(self.price - self.sl)
        if risk == 0:
            return 0.0
        return abs(self.tp - self.price) / risk


def in_session(when: datetime, params: SignalParams) -> tuple[bool, str]:
    """CTTSignalCore::InSession と同じ判定。MT5 のサーバー時間を前提とする。"""
    weekday = when.weekday()  # 月=0 ... 日=6

    if weekday >= 5:
        return False, "週末のため見送り"
    if when.hour < params.session_start_hour or when.hour >= params.session_end_hour:
        return False, f"時間帯外({when.hour:02d}時)のため見送り"
    if params.block_friday_late and weekday == 4 and when.hour >= params.friday_cutoff_hour:
        return False, "金曜終盤のため新規見送り"
    return True, ""


@dataclass
class IndicatorSet:
    """1本ずつ再計算しないためのキャッシュ。全期間分をまとめて持つ。"""

    fast: List[Optional[float]]
    slow: List[Optional[float]]
    trend: List[Optional[float]]
    adx: List[Optional[float]]
    atr: List[Optional[float]]


def compute_indicators(bars: Sequence[Bar], params: SignalParams) -> IndicatorSet:
    closes = [b.close for b in bars]
    highs = [b.high for b in bars]
    lows = [b.low for b in bars]

    return IndicatorSet(
        fast=calc_ema(closes, params.ema_fast),
        slow=calc_ema(closes, params.ema_slow),
        trend=calc_ema(closes, params.ema_trend),
        adx=calc_adx(highs, lows, closes, params.adx_period),
        atr=calc_atr(highs, lows, closes, params.atr_period, params.atr_mode),
    )


def evaluate(bars: Sequence[Bar], params: SignalParams, symbol: str,
             timeframe: str, index: Optional[int] = None,
             indicators: Optional[IndicatorSet] = None) -> Optional[Signal]:
    """指定した足を判定する。index を省略すると最終足(=確定足として扱う)。

    方向が出なかった場合も Signal を返す(direction=NONE, reason に理由)。
    ヒストリー不足など判定そのものができない場合だけ None を返す。

    indicators を渡すと再計算を省ける(scan が全期間で1回だけ計算して使い回す)。
    """
    params.validate()

    if index is None:
        index = len(bars) - 1
    if index < 1 or index >= len(bars):
        return None
    if len(bars) < params.warmup_bars:
        return None

    ind = indicators or compute_indicators(bars, params)
    fast, slow, trend = ind.fast, ind.slow, ind.trend
    adx_values, atr_values = ind.adx, ind.atr

    required: List[Optional[float]] = [
        fast[index], fast[index - 1], slow[index], slow[index - 1],
        trend[index], atr_values[index],
    ]
    if any(v is None for v in required):
        return None

    bar = bars[index]
    atr_now = float(atr_values[index])
    # 値動きが完全に止まると ADX は定義できない。判定不能ではなく「見送り」として扱う
    adx_raw = adx_values[index]
    adx_now = float(adx_raw) if adx_raw is not None else 0.0

    def _flat(reason: str) -> Signal:
        return Signal(NONE, bar.time, symbol, timeframe, bar.close,
                      0.0, 0.0, atr_now, adx_now, reason)

    if atr_now <= 0:
        return _flat("ATRが0のため損切り幅を決められません")

    if adx_raw is None:
        return _flat("ADXを算出できません(値動きが不足)")

    ok, why = in_session(bar.time, params)
    if not ok:
        return _flat(why)

    if adx_now < params.adx_min:
        return _flat(f"ADX {adx_now:.1f} < {params.adx_min:.1f} のためレンジと判断")

    cross_up = fast[index - 1] <= slow[index - 1] and fast[index] > slow[index]
    cross_down = fast[index - 1] >= slow[index - 1] and fast[index] < slow[index]

    if not cross_up and not cross_down:
        return _flat("クロスなし")

    trend_now = float(trend[index])
    if cross_up and bar.close <= trend_now:
        return _flat("上抜けだが終値がトレンドEMAの下のため見送り")
    if cross_down and bar.close >= trend_now:
        return _flat("下抜けだが終値がトレンドEMAの上のため見送り")

    sl_distance = atr_now * params.sl_atr_mult
    tp_distance = sl_distance * params.rr_ratio

    if cross_up:
        direction, sl, tp = BUY, bar.close - sl_distance, bar.close + tp_distance
    else:
        direction, sl, tp = SELL, bar.close + sl_distance, bar.close - tp_distance

    reason = (
        f"EMA{params.ema_fast}/{params.ema_slow} "
        f"{'上抜け' if cross_up else '下抜け'}・"
        f"終値がEMA{params.ema_trend}の{'上' if cross_up else '下'}・"
        f"ADX {adx_now:.1f}"
    )
    return Signal(direction, bar.time, symbol, timeframe, bar.close,
                  sl, tp, atr_now, adx_now, reason)


def scan(bars: Sequence[Bar], params: SignalParams, symbol: str,
         timeframe: str) -> List[Signal]:
    """全期間を走査して成立したシグナルだけを返す(検証・バックテスト用)。"""
    indicators = compute_indicators(bars, params)

    found: List[Signal] = []
    for index in range(params.warmup_bars, len(bars)):
        signal = evaluate(bars, params, symbol, timeframe, index, indicators)
        if signal is not None and signal.direction != NONE:
            found.append(signal)
    return found
