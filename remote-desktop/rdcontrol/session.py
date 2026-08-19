"""接続クライアントの管理と操作権の調停。"""

from __future__ import annotations

import itertools
from dataclasses import dataclass, field
from typing import Any

from .config import Settings


@dataclass
class ClientSession:
    """1 本の WebSocket 接続に対応する状態。"""

    id: int
    remote: str
    quality: int
    fps: int
    scale: float
    has_control: bool = False

    def apply_config(self, message: dict[str, Any]) -> None:
        if "quality" in message:
            self.quality = int(message["quality"])
        if "fps" in message:
            self.fps = int(message["fps"])
        if "scale" in message:
            self.scale = float(message["scale"])

    @property
    def frame_interval(self) -> float:
        return 1.0 / max(1, self.fps)


class SessionManager:
    """同時接続数の制限と、操作権を 1 クライアントに限定する調停を行う。

    2 人が同時にマウスを動かすと操作不能になるため、操作できるのは
    常に 1 クライアントだけとし、他は閲覧のみになる。操作権を持つ
    クライアントが切断したら次のクライアントへ自動的に引き継ぐ。
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._ids = itertools.count(1)
        self._sessions: dict[int, ClientSession] = {}

    @property
    def sessions(self) -> list[ClientSession]:
        return list(self._sessions.values())

    def is_full(self) -> bool:
        return len(self._sessions) >= self._settings.max_clients

    def add(self, remote: str) -> ClientSession:
        session = ClientSession(
            id=next(self._ids),
            remote=remote,
            quality=self._settings.quality,
            fps=self._settings.fps,
            scale=self._settings.scale,
        )
        # 操作権はサーバーが view-only でなく、まだ誰も持っていない場合のみ付与
        if not self._settings.view_only and not any(s.has_control for s in self._sessions.values()):
            session.has_control = True
        self._sessions[session.id] = session
        return session

    def remove(self, session: ClientSession) -> ClientSession | None:
        """セッションを取り除き、操作権を引き継いだ相手を返す。"""
        self._sessions.pop(session.id, None)
        if not session.has_control:
            return None
        session.has_control = False
        if self._settings.view_only:
            return None
        successor = next(iter(self._sessions.values()), None)
        if successor is not None:
            successor.has_control = True
        return successor
