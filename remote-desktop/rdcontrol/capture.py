"""画面キャプチャと JPEG エンコード。

mss + Pillow を使う。GUI セッションのない環境(ヘッドレスサーバー、
コンテナ、SSH のみの接続)では初期化時に CaptureUnavailable を投げ、
利用者に原因が分かるメッセージを返す。
"""

from __future__ import annotations

import hashlib
import io
import threading
from dataclasses import dataclass

DEFAULT_QUALITY = 60
DEFAULT_SCALE = 1.0
MIN_DIMENSION = 16


class CaptureUnavailable(RuntimeError):
    """画面キャプチャができない環境であることを示す。"""


@dataclass(frozen=True)
class Frame:
    """1 枚のキャプチャ結果。"""

    jpeg: bytes
    width: int
    height: int
    screen_width: int
    screen_height: int
    digest: str


@dataclass(frozen=True)
class MonitorInfo:
    index: int
    left: int
    top: int
    width: int
    height: int

    @property
    def label(self) -> str:
        return f"#{self.index} ({self.width}x{self.height})"


def scaled_size(width: int, height: int, scale: float) -> tuple[int, int]:
    """縮小後のサイズを求める。極端に小さくならないよう下限を設ける。"""
    scale = min(1.0, max(0.05, scale))
    return (
        max(MIN_DIMENSION, int(round(width * scale))),
        max(MIN_DIMENSION, int(round(height * scale))),
    )


class ScreenCapture:
    """スレッドローカルな mss インスタンスを介して画面を取得する。

    mss のインスタンスはスレッド間で共有できないため、キャプチャを
    実行するスレッドごとに生成する(asyncio.to_thread から呼ばれる
    ワーカースレッドが複数になっても安全にするため)。
    """

    def __init__(self, monitor: int = 1) -> None:
        self._local = threading.local()
        self._monitor_index = monitor
        self._lock = threading.Lock()
        # 起動時に一度だけ検証し、環境不備は即座に知らせる
        monitors = self.monitors()
        if not monitors:
            raise CaptureUnavailable("キャプチャ可能なモニタが見つかりませんでした。")
        if not any(m.index == monitor for m in monitors):
            raise CaptureUnavailable(
                f"モニタ {monitor} は存在しません。利用可能: "
                + ", ".join(m.label for m in monitors)
            )

    @property
    def monitor_index(self) -> int:
        return self._monitor_index

    def select_monitor(self, index: int) -> bool:
        """表示対象のモニタを切り替える。存在しない番号なら False。"""
        if not any(m.index == index for m in self.monitors()):
            return False
        with self._lock:
            self._monitor_index = index
        return True

    def _sct(self):
        sct = getattr(self._local, "sct", None)
        if sct is None:
            try:
                import mss  # 遅延 import: テストや import 時に GUI を要求しない
            except ImportError as exc:  # pragma: no cover - 依存の有無は環境依存
                raise CaptureUnavailable(
                    "mss がインストールされていません。`pip install -r requirements.txt` を実行してください。"
                ) from exc
            try:
                sct = mss.mss()
            except Exception as exc:  # mss.ScreenShotError など環境依存の例外
                raise CaptureUnavailable(
                    "画面に接続できませんでした。デスクトップにログインした状態で "
                    "実行しているか確認してください(Linux では DISPLAY / WAYLAND_DISPLAY が必要です)。"
                ) from exc
            self._local.sct = sct
        return sct

    def monitors(self) -> list[MonitorInfo]:
        """利用可能なモニタ一覧。index 0 は全画面を結合した仮想モニタ。"""
        sct = self._sct()
        result = []
        for i, mon in enumerate(sct.monitors):
            result.append(
                MonitorInfo(
                    index=i,
                    left=int(mon["left"]),
                    top=int(mon["top"]),
                    width=int(mon["width"]),
                    height=int(mon["height"]),
                )
            )
        return result

    def current_monitor(self) -> MonitorInfo:
        index = self._monitor_index
        for mon in self.monitors():
            if mon.index == index:
                return mon
        raise CaptureUnavailable(f"モニタ {index} が利用できなくなりました。")

    def grab(self, *, quality: int = DEFAULT_QUALITY, scale: float = DEFAULT_SCALE) -> Frame:
        """現在のモニタを 1 枚キャプチャして JPEG に変換する。"""
        try:
            from PIL import Image
        except ImportError as exc:  # pragma: no cover - 依存の有無は環境依存
            raise CaptureUnavailable(
                "Pillow がインストールされていません。`pip install -r requirements.txt` を実行してください。"
            ) from exc

        sct = self._sct()
        with self._lock:
            index = self._monitor_index
        try:
            shot = sct.grab(sct.monitors[index])
        except Exception as exc:
            raise CaptureUnavailable(f"画面のキャプチャに失敗しました: {exc}") from exc

        image = Image.frombytes("RGB", shot.size, shot.rgb)
        target = scaled_size(image.width, image.height, scale)
        if target != (image.width, image.height):
            image = image.resize(target, Image.BILINEAR)

        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=int(quality), optimize=False)
        jpeg = buffer.getvalue()
        return Frame(
            jpeg=jpeg,
            width=image.width,
            height=image.height,
            screen_width=int(shot.size[0]),
            screen_height=int(shot.size[1]),
            digest=hashlib.blake2b(jpeg, digest_size=16).hexdigest(),
        )

    def close(self) -> None:
        sct = getattr(self._local, "sct", None)
        if sct is not None:
            sct.close()
            self._local.sct = None
