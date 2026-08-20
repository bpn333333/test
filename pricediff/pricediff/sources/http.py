"""HTTPクライアント。リトライ・レート制限・ディスクキャッシュを共通化する。"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from pathlib import Path
from typing import Any, Optional

import requests

log = logging.getLogger(__name__)


class FetchError(RuntimeError):
    """外部APIの呼び出しに失敗した(呼び出し側で1商品ぶんの警告として扱う)。"""


class DiskCache:
    def __init__(self, directory: str, ttl_seconds: int, enabled: bool = True):
        self.enabled = enabled
        self.ttl = ttl_seconds
        self.dir = Path(directory).expanduser()
        if self.enabled:
            self.dir.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        digest = hashlib.sha256(key.encode("utf-8")).hexdigest()[:32]
        return self.dir / f"{digest}.json"

    def get(self, key: str) -> Optional[Any]:
        if not self.enabled:
            return None
        path = self._path(key)
        if not path.is_file():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None
        if time.time() - payload.get("stored_at", 0) > self.ttl:
            return None
        return payload.get("value")

    def set(self, key: str, value: Any) -> None:
        if not self.enabled:
            return
        try:
            self._path(key).write_text(
                json.dumps({"stored_at": time.time(), "value": value}, ensure_ascii=False),
                encoding="utf-8",
            )
        except OSError as exc:  # pragma: no cover - ディスク不調時のみ
            log.debug("キャッシュ書き込み失敗: %s", exc)


class HttpClient:
    """JSON APIを叩くための薄いラッパ。"""

    def __init__(
        self,
        *,
        timeout: int = 20,
        retries: int = 3,
        backoff: float = 2.0,
        interval: float = 1.0,
        user_agent: str = "pricediff/1.0",
        cache: Optional[DiskCache] = None,
    ):
        self.timeout = timeout
        self.retries = max(1, retries)
        self.backoff = backoff
        self.interval = interval
        self.cache = cache
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": user_agent, "Accept": "application/json"})
        self._last_request_at = 0.0
        self.stats = {"requests": 0, "cache_hits": 0, "errors": 0}

    def _throttle(self) -> None:
        if self.interval <= 0:
            return
        elapsed = time.monotonic() - self._last_request_at
        if elapsed < self.interval:
            time.sleep(self.interval - elapsed)
        self._last_request_at = time.monotonic()

    def get_json(
        self,
        url: str,
        params: Optional[dict[str, Any]] = None,
        *,
        cache_key: Optional[str] = None,
        headers: Optional[dict[str, str]] = None,
    ) -> Any:
        return self._request_json("GET", url, params=params, cache_key=cache_key, headers=headers)

    def post_json(
        self,
        url: str,
        *,
        data: Optional[bytes | str] = None,
        params: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None,
        cache_key: Optional[str] = None,
    ) -> Any:
        return self._request_json(
            "POST", url, params=params, data=data, headers=headers, cache_key=cache_key
        )

    def _request_json(
        self,
        method: str,
        url: str,
        *,
        params: Optional[dict[str, Any]] = None,
        data: Optional[bytes | str] = None,
        headers: Optional[dict[str, str]] = None,
        cache_key: Optional[str] = None,
    ) -> Any:
        body_key = data.decode("utf-8", "ignore") if isinstance(data, bytes) else (data or "")
        key = cache_key or f"{method}:{url}:{json.dumps(params, sort_keys=True, default=str)}:{body_key}"
        if self.cache:
            cached = self.cache.get(key)
            if cached is not None:
                self.stats["cache_hits"] += 1
                return cached

        last_error: Optional[Exception] = None
        for attempt in range(self.retries):
            self._throttle()
            try:
                self.stats["requests"] += 1
                response = self.session.request(
                    method, url, params=params, data=data, headers=headers, timeout=self.timeout
                )
                # 429/5xx はリトライ対象、それ以外の4xxは即座に諦める
                if response.status_code == 429 or response.status_code >= 500:
                    raise FetchError(f"HTTP {response.status_code}: {response.text[:200]}")
                if response.status_code >= 400:
                    raise FetchError(
                        f"HTTP {response.status_code}: {response.text[:300]}", 
                    )
                payload = response.json()
                if self.cache:
                    self.cache.set(key, payload)
                return payload
            except FetchError as exc:
                last_error = exc
                if "HTTP 4" in str(exc) and "HTTP 429" not in str(exc):
                    break
            except (requests.RequestException, ValueError) as exc:
                last_error = exc
            if attempt < self.retries - 1:
                time.sleep(self.backoff * (2**attempt))

        self.stats["errors"] += 1
        raise FetchError(f"{url} の取得に失敗しました: {last_error}")


def build_client(config) -> HttpClient:
    cache = DiskCache(
        config.get("cache", "dir", default="~/.cache/pricediff"),
        int(config.get("cache", "ttl_seconds", default=21600)),
        enabled=bool(config.get("cache", "enabled", default=True)),
    )
    return HttpClient(
        timeout=int(config.get("request", "timeout", default=20)),
        retries=int(config.get("request", "retries", default=3)),
        backoff=float(config.get("request", "backoff", default=2.0)),
        interval=float(config.get("request", "interval", default=1.0)),
        user_agent=str(config.get("request", "user_agent", default="pricediff/1.0")),
        cache=cache,
    )
