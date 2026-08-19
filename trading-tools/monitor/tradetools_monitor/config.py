"""設定。MQL5 の TTDefaultParams() と既定値を一致させること。

片方だけ変更すると、サインツールの矢印と配信内容がずれる。
値を変えるときは必ず両方を同時に変え、パリティテストを回す。
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List


@dataclass
class SignalParams:
    """SignalCore.mqh の TTSignalParams と1対1で対応する。"""

    ema_fast: int = 12
    ema_slow: int = 48
    ema_trend: int = 200
    adx_period: int = 14
    adx_min: float = 20.0
    atr_period: int = 14
    sl_atr_mult: float = 1.5
    rr_ratio: float = 1.8
    session_start_hour: int = 8
    session_end_hour: int = 22
    block_friday_late: bool = True
    friday_cutoff_hour: int = 20
    atr_mode: str = "mt5"  # indicators.atr の実装切替

    def validate(self) -> None:
        if self.ema_fast >= self.ema_slow:
            raise ValueError("ema_fast は ema_slow より小さくしてください")
        if self.adx_min < 0:
            raise ValueError("adx_min は0以上です")
        if self.sl_atr_mult <= 0 or self.rr_ratio <= 0:
            raise ValueError("sl_atr_mult と rr_ratio は0より大きい値です")
        if not 0 <= self.session_start_hour <= 23 or not 1 <= self.session_end_hour <= 24:
            raise ValueError("取引時間帯の指定が不正です")
        if self.session_start_hour >= self.session_end_hour:
            raise ValueError("session_start_hour は session_end_hour より前にしてください")

    @property
    def warmup_bars(self) -> int:
        """SignalCore::WarmupBars() と同じ式。ずらさないこと。"""
        longest = max(self.ema_trend, self.ema_slow, self.adx_period, self.atr_period)
        return longest * 3 + 10


@dataclass
class MonitorConfig:
    """監視対象と動作。"""

    symbols: List[str] = field(default_factory=lambda: ["USDJPY", "EURUSD", "GBPJPY"])
    timeframe: str = "PERIOD_H1"
    poll_seconds: int = 60
    params: SignalParams = field(default_factory=SignalParams)

    # 発生源。"signal_file" = MT5 が書いた CSV を読む / "csv" = ローカルOHLCで検証
    source: str = "signal_file"
    signal_file: str = "~/AppData/Roaming/MetaQuotes/Terminal/Common/Files/TradeTools/signals.csv"
    csv_dir: str = "data"

    # 通知先
    notify_console: bool = True
    notify_file: str = "data/alerts.log"
    notify_webhook_url: str = ""  # Discord/Slack など。空なら送らない

    # X配信へ引き渡すか
    publish_to_x: bool = False
    # この分数より古い足のシグナルは配信しない(0で無制限)。
    # 監視を止めていた間に溜まった古いシグナルが一斉に流れるのを防ぐ
    publish_max_age_minutes: int = 180

    # 状態の保存先。再起動しても同じシグナルを二重に流さないため
    state_file: str = "data/monitor_state.json"

    @classmethod
    def load(cls, path: str | os.PathLike[str] | None = None) -> "MonitorConfig":
        """JSON から読み込む。存在しなければ既定値。"""
        if path is None:
            return cls()

        raw: Dict[str, Any] = json.loads(Path(path).expanduser().read_text(encoding="utf-8"))
        params = SignalParams(**raw.pop("params", {}))
        config = cls(params=params, **raw)
        config.params.validate()
        return config

    def dump(self, path: str | os.PathLike[str]) -> None:
        Path(path).expanduser().write_text(
            json.dumps(asdict(self), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def resolved_signal_file(self) -> Path:
        return Path(self.signal_file).expanduser()
