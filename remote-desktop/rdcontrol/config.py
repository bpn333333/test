"""起動設定。"""

from __future__ import annotations

import getpass
import socket
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
    ssh_target: str = ""  # 案内に表示する SSH 接続先。空なら自動推定

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

    def tunnel_url(self) -> str:
        """SSH トンネル経由で開く URL(手元の 127.0.0.1 を指す)。"""
        return f"http://127.0.0.1:{self.port}/?token={self.token}"

    def tunnel_command(self) -> str:
        """操作する側の端末で実行する SSH トンネルのコマンド。"""
        return ssh_tunnel_command(self.port, self.ssh_target or local_ssh_target())


def ssh_tunnel_command(port: int, target: str) -> str:
    """ローカルポート転送で rdcontrol につなぐ ssh コマンドを組み立てる。

    ExitOnForwardFailure は、手元のポートが既に使われていたときに
    「つながったように見えて実は転送されていない」状態を防ぐために付ける。
    ServerAlive* は、NAT やモバイル回線で無言のまま切られた接続を検知するため。
    """
    return (
        "ssh -N "
        "-o ExitOnForwardFailure=yes "
        "-o ServerAliveInterval=30 -o ServerAliveCountMax=3 "
        f"-L {port}:127.0.0.1:{port} {target}"
    )


def local_ssh_target() -> str:
    """このマシンへの SSH 接続先(user@host)を推定する。

    あくまで案内表示用。名前解決できない環境もあるため、失敗しても
    それらしい文字列を返して処理は止めない。
    """
    try:
        user = getpass.getuser()
    except Exception:
        user = "ユーザー名"
    try:
        host = socket.gethostname() or "このマシン"
    except Exception:
        host = "このマシン"
    return f"{user}@{host}"
