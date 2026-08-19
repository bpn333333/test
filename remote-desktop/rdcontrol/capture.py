"""画面キャプチャと JPEG エンコード。

mss + Pillow を使う。GUI セッションのない環境(ヘッドレスサーバー、
コンテナ、SSH のみの接続)では初期化時に CaptureUnavailable を投げ、
利用者に原因が分かるメッセージを返す。
"""

from __future__ import annotations

import hashlib
import io
import logging
import threading
import time
from dataclasses import dataclass

logger = logging.getLogger("rdcontrol.capture")

DEFAULT_QUALITY = 60
DEFAULT_SCALE = 1.0
MIN_DIMENSION = 16

# ディスプレイ構成(数・解像度・配置)を調べ直す間隔
LAYOUT_CHECK_INTERVAL = 3.0


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

    def __init__(self, monitor: int = 1, *, factory=None) -> None:
        self._local = threading.local()
        self._monitor_index = monitor
        self._lock = threading.Lock()
        self._factory = factory
        # ディスプレイ構成が変わったときに、各スレッドの取得口を作り直すための世代番号
        self._generation = 0
        self._layout_checked = 0.0
        # 起動時に一度だけ検証し、環境不備は即座に知らせる
        monitors = self.monitors()
        self._layout = self._signature(monitors)
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
        # 構成が変わっていたら、このスレッドの取得口も作り直す
        if sct is not None and getattr(self._local, "generation", -1) != self._generation:
            try:
                sct.close()
            except Exception:
                pass
            sct = None
        if sct is None:
            if self._factory is not None:
                self._local.sct = sct = self._factory()
                self._local.generation = self._generation
                return sct
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
            self._local.generation = self._generation
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

    @staticmethod
    def _signature(monitors: list[MonitorInfo]) -> tuple:
        return tuple((m.index, m.left, m.top, m.width, m.height) for m in monitors)

    def refresh(self) -> list[MonitorInfo]:
        """ディスプレイ構成を読み直す。

        mss はモニタ一覧を最初に一度だけ読んで覚え込むため、モニタの電源を
        入れ切りしたり解像度を変えたりしても古い値のままになる。取得口を
        作り直すことで読み直させる。
        """
        self._generation += 1
        return self.monitors()

    def poll_layout(self, *, now: float | None = None) -> list[MonitorInfo] | None:
        """一定間隔で構成を調べ、変わっていれば新しい一覧を返す。

        変化が無ければ None。表示中のモニタが無くなった場合は、残っている
        モニタへ自動的に切り替える(切断せずに使い続けられるようにする)。
        """
        now = time.monotonic() if now is None else now
        if now - self._layout_checked < LAYOUT_CHECK_INTERVAL:
            return None
        self._layout_checked = now

        monitors = self.refresh()
        signature = self._signature(monitors)
        if signature == self._layout:
            return None

        logger.info("ディスプレイ構成が変わりました: %s", [m.label for m in monitors])
        self._layout = signature
        if not any(m.index == self._monitor_index for m in monitors):
            fallback = monitors[1].index if len(monitors) > 1 else monitors[0].index
            logger.info("表示中のモニタが無くなったため %s へ切り替えます", fallback)
            with self._lock:
                self._monitor_index = fallback
        return monitors

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

        with self._lock:
            index = self._monitor_index
        try:
            shot = self._grab_monitor(index)
        except Exception:
            # ディスプレイ構成が変わった直後は失敗しうる。読み直して一度だけやり直す。
            self.refresh()
            monitors = self.monitors()
            if not any(m.index == index for m in monitors):
                index = monitors[1].index if len(monitors) > 1 else monitors[0].index
                with self._lock:
                    self._monitor_index = index
                logger.info("表示中のモニタが無くなったため %s へ切り替えます", index)
            try:
                shot = self._grab_monitor(index)
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

    def _grab_monitor(self, index: int):
        sct = self._sct()
        monitors = sct.monitors
        if index >= len(monitors):
            raise IndexError(f"モニタ {index} は存在しません")
        return sct.grab(monitors[index])

    def close(self) -> None:
        sct = getattr(self._local, "sct", None)
        if sct is not None:
            sct.close()
            self._local.sct = None
