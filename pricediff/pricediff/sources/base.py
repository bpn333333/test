"""各モール取得元の共通インターフェース。"""

from __future__ import annotations

import datetime as dt
from typing import Optional, Protocol

from ..models import Offer, WatchItem


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")


class Source(Protocol):
    market: str

    def available(self) -> bool:
        """このソースが実際に取得できる状態か(APIキーが揃っているか等)。"""

    def fetch(self, item: WatchItem) -> Optional[Offer]:
        """1商品ぶんのオファーを返す。見つからなければ None。"""


def first_number(*values) -> Optional[float]:
    for value in values:
        if value in (None, "", "-"):
            continue
        try:
            return float(str(value).replace(",", "").replace("¥", "").replace("￥", ""))
        except (TypeError, ValueError):
            continue
    return None
