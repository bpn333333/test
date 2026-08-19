"""テスト用の合成バー生成。"""

from __future__ import annotations

import math
from datetime import datetime, timedelta
from typing import List

from tradetools_monitor.signals import Bar


def make_bars(count: int, start: datetime | None = None,
              base: float = 140.0, amplitude: float = 3.0,
              wavelength: float = 11.0, drift: float = 0.02,
              spread: float = 0.3) -> List[Bar]:
    """再現性のある合成データ。乱数を使わないのでテストが揺れない。"""
    start = start or datetime(2026, 1, 5, 9, 0)  # 月曜9時
    bars: List[Bar] = []
    for i in range(count):
        close = base + amplitude * math.sin(i / wavelength) + i * drift
        bars.append(
            Bar(
                time=start + timedelta(hours=i),
                open=close,
                high=close + spread,
                low=close - spread,
                close=close,
            )
        )
    return bars


def make_flat_bars(count: int, start: datetime | None = None,
                   price: float = 150.0) -> List[Bar]:
    """完全に横ばい。ATR=0、クロス無しの境界を突くため。"""
    start = start or datetime(2026, 1, 5, 9, 0)
    return [
        Bar(time=start + timedelta(hours=i), open=price, high=price,
            low=price, close=price)
        for i in range(count)
    ]
