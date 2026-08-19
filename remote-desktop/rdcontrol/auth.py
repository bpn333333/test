"""アクセストークンの発行と検証、および総当たり攻撃への簡易防御。"""

from __future__ import annotations

import secrets
import time
from dataclasses import dataclass, field

TOKEN_BYTES = 24
DEFAULT_MAX_FAILURES = 8
DEFAULT_LOCKOUT_SECONDS = 300.0


def generate_token() -> str:
    """URL に埋め込める安全なランダムトークンを生成する。"""
    return secrets.token_urlsafe(TOKEN_BYTES)


def token_matches(expected: str, provided: str | None) -> bool:
    """タイミング攻撃に強い比較でトークンを照合する。"""
    if not provided:
        return False
    return secrets.compare_digest(expected, provided)


@dataclass
class _Attempts:
    failures: int = 0
    locked_until: float = 0.0


@dataclass
class AuthGuard:
    """接続元 IP ごとに認証失敗を数え、一定回数でロックアウトする。

    自宅 LAN やトンネル越しの利用を想定した軽量な防御であり、
    公開インターネットに直接晒す運用は README で非推奨としている。
    """

    token: str
    max_failures: int = DEFAULT_MAX_FAILURES
    lockout_seconds: float = DEFAULT_LOCKOUT_SECONDS
    _attempts: dict[str, _Attempts] = field(default_factory=dict, repr=False)

    def is_locked(self, client_ip: str, *, now: float | None = None) -> bool:
        now = time.monotonic() if now is None else now
        record = self._attempts.get(client_ip)
        if record is None:
            return False
        if record.locked_until and record.locked_until <= now:
            # ロックアウト期間が明けたのでカウンタを捨てる
            del self._attempts[client_ip]
            return False
        return bool(record.locked_until)

    def check(self, client_ip: str, provided: str | None, *, now: float | None = None) -> bool:
        """トークンを検証する。ロックアウト中や不一致なら False。"""
        now = time.monotonic() if now is None else now
        if self.is_locked(client_ip, now=now):
            return False

        if token_matches(self.token, provided):
            self._attempts.pop(client_ip, None)
            return True

        record = self._attempts.setdefault(client_ip, _Attempts())
        record.failures += 1
        if record.failures >= self.max_failures:
            record.locked_until = now + self.lockout_seconds
        return False

    def failures(self, client_ip: str) -> int:
        record = self._attempts.get(client_ip)
        return record.failures if record else 0
