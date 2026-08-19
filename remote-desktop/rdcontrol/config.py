"""起動設定。"""

from __future__ import annotations

from dataclasses import dataclass, field

from .auth import generate_token

DEFAULT_PORT = 8765
DEFAULT_FPS = 10
DEFAULT_QUALITY = 60
DEFAULT_SCALE = 1.0


@dataclass
class Settings:
    """サーバーの起動設定。

    既定では 127.0.0.1 のみを listen する。外部から接続する場合は
    SSH トンネルなどで転送する運用を README で推奨している。
    """

    host: str = "127.0.0.1"
    port: int = DEFAULT_PORT
    token: str = field(default_factory=generate_token)
    monitor: int = 1
    fps: int = DEFAULT_FPS
    quality: int = DEFAULT_QUALITY
    scale: float = DEFAULT_SCALE
    view_only: bool = False
    max_clients: int = 4
    idle_timeout: float = 0.0  # 0 なら無効

    @property
    def is_public(self) -> bool:
        """ループバック以外を listen しているか(警告表示の判定に使う)。"""
        return self.host not in ("127.0.0.1", "localhost", "::1")

    def url(self) -> str:
        host = self.host
        if host in ("0.0.0.0", "::", ""):
            host = "127.0.0.1"
        if ":" in host and not host.startswith("["):
            host = f"[{host}]"
        return f"http://{host}:{self.port}/?token={self.token}"
