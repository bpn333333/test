"""為替レート(CNY -> JPY)の取得。

source: fixed      -> config の値をそのまま使う(オフラインでも動く)
        frankfurter -> https://api.frankfurter.app から当日レートを取得
buffer_pct を上乗せして、円安方向にぶれても計算が甘くならないようにする。
"""

from __future__ import annotations

import logging
from typing import Optional

log = logging.getLogger(__name__)

FRANKFURTER_URL = "https://api.frankfurter.app/latest"


class FxRate:
    def __init__(self, rate: float, source: str, buffer_pct: float = 0.0):
        self.base_rate = rate
        self.source = source
        self.buffer_pct = buffer_pct

    @property
    def rate(self) -> float:
        """安全マージンを乗せた実効レート。"""
        return self.base_rate * (1 + self.buffer_pct / 100)

    def to_jpy(self, cny: Optional[float]) -> Optional[float]:
        return None if cny is None else cny * self.rate

    def describe(self) -> str:
        if self.buffer_pct:
            return (
                f"1 CNY = {self.base_rate:.3f} JPY ({self.source}"
                f" / +{self.buffer_pct:g}%バッファ後 {self.rate:.3f})"
            )
        return f"1 CNY = {self.base_rate:.3f} JPY ({self.source})"


def get_fx_rate(config, client=None, *, override: Optional[float] = None) -> FxRate:
    buffer_pct = float(config.get("fx", "buffer_pct", default=0.0))
    fixed = float(config.get("fx", "cny_jpy", default=21.0))

    if override:
        # 明示指定されたレートは、そのまま使う(安全マージンを勝手に足さない)
        return FxRate(override, "指定値", 0.0)

    source = str(config.get("fx", "source", default="fixed")).lower()
    if source == "frankfurter" and client is not None:
        try:
            payload = client.get_json(FRANKFURTER_URL, {"from": "CNY", "to": "JPY"})
            rate = float(payload["rates"]["JPY"])
            return FxRate(rate, f"frankfurter {payload.get('date', '')}".strip(), buffer_pct)
        except Exception as exc:  # noqa: BLE001 - レート取得失敗は致命的ではない
            log.warning("為替レートの取得に失敗したため設定値を使います: %s", exc)

    return FxRate(fixed, "設定値", buffer_pct)
