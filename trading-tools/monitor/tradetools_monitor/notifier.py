"""通知。標準出力・ファイル・Webhook。

Webhook は Discord / Slack の受信URLをそのまま入れられる形にしてある。
外部送信は失敗しても監視ループを止めない(通知の失敗で監視が死ぬ方が困る)。
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Protocol

from .signals import Signal


def decimals_for(symbol: str) -> int:
    """円絡みは3桁、それ以外は5桁。composer._decimals と同じ規則。"""
    return 3 if "JPY" in symbol.upper() else 5


def format_signal(signal: Signal, decimals: Optional[int] = None) -> str:
    """人が読む1行。X配信の本文とは別物(あちらは composer が作る)。"""
    if decimals is None:
        decimals = decimals_for(signal.symbol)
    return (
        f"[{signal.symbol} {signal.timeframe}] {signal.direction}  "
        f"{signal.time:%Y-%m-%d %H:%M}  "
        f"価格 {signal.price:.{decimals}f} / 損切 {signal.sl:.{decimals}f} / "
        f"利確 {signal.tp:.{decimals}f} (RR {signal.risk_reward:.1f})  — {signal.reason}"
    )


class Notifier(Protocol):
    def send(self, signal: Signal) -> bool:
        ...


class ConsoleNotifier:
    def send(self, signal: Signal) -> bool:
        print(format_signal(signal), flush=True)
        return True


class FileNotifier:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path).expanduser()

    def send(self, signal: Signal) -> bool:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(f"{stamp}\t{format_signal(signal)}\n")
        return True


class WebhookNotifier:
    """Discord / Slack 互換。どちらも content / text のどちらかを見る。"""

    def __init__(self, url: str, timeout: int = 10) -> None:
        self.url = url
        self.timeout = timeout

    def send(self, signal: Signal) -> bool:
        if not self.url:
            return False

        body = format_signal(signal)
        payload = json.dumps({"content": body, "text": body}).encode("utf-8")
        request = urllib.request.Request(
            self.url, data=payload, headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return 200 <= response.status < 300
        except (urllib.error.URLError, OSError) as error:
            print(f"Webhook 送信失敗: {error}", flush=True)
            return False


def build_notifiers(config) -> List[Notifier]:
    notifiers: List[Notifier] = []
    if config.notify_console:
        notifiers.append(ConsoleNotifier())
    if config.notify_file:
        notifiers.append(FileNotifier(config.notify_file))
    if config.notify_webhook_url:
        notifiers.append(WebhookNotifier(config.notify_webhook_url))
    return notifiers
