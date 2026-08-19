"""マウス・キーボードの操作。pynput をラップする。

ブラウザの KeyboardEvent / MouseEvent を pynput のキー・ボタンへ変換し、
押しっぱなしのキーを追跡する。切断時に release_all() を呼ぶことで
「Ctrl が押されたまま操作不能になる」といった事故を防ぐ。
"""

from __future__ import annotations

import logging
import sys
import threading
from typing import Any

logger = logging.getLogger("rdcontrol.input")

# SendInput の絶対座標は、仮想デスクトップ全体を 0〜65535 に写像したもの
ABSOLUTE_RANGE = 65535


class InputUnavailable(RuntimeError):
    """入力デバイスを操作できない環境であることを示す。"""


def _load_pynput():
    try:
        from pynput import keyboard, mouse
    except ImportError as exc:  # pragma: no cover - 依存の有無は環境依存
        raise InputUnavailable(
            "pynput がインストールされていません。`pip install -r requirements.txt` を実行してください。"
        ) from exc
    return keyboard, mouse


def build_key_map(keyboard_module: Any) -> dict[str, Any]:
    """KeyboardEvent.key / .code から pynput の Key への対応表を作る。"""
    key = keyboard_module.Key
    mapping: dict[str, Any] = {
        # 編集・移動
        "Enter": key.enter,
        "NumpadEnter": key.enter,
        "Backspace": key.backspace,
        "Tab": key.tab,
        "Escape": key.esc,
        "Delete": key.delete,
        "Insert": key.insert,
        "Home": key.home,
        "End": key.end,
        "PageUp": key.page_up,
        "PageDown": key.page_down,
        "ArrowUp": key.up,
        "ArrowDown": key.down,
        "ArrowLeft": key.left,
        "ArrowRight": key.right,
        " ": key.space,
        "Space": key.space,
        # 修飾キー(左右の区別がつかない場合の既定値)
        "Shift": key.shift,
        "Control": key.ctrl,
        "Alt": key.alt,
        "Meta": key.cmd,
        "CapsLock": key.caps_lock,
        # 左右を区別する code 側
        "ShiftLeft": key.shift_l,
        "ShiftRight": key.shift_r,
        "ControlLeft": key.ctrl_l,
        "ControlRight": key.ctrl_r,
        "AltLeft": key.alt_l,
        "AltRight": key.alt_r,
        "MetaLeft": key.cmd_l,
        "MetaRight": key.cmd_r,
    }
    for name in ("menu", "print_screen", "scroll_lock", "pause", "num_lock"):
        special = getattr(key, name, None)
        if special is not None:
            mapping[{"menu": "ContextMenu", "print_screen": "PrintScreen",
                     "scroll_lock": "ScrollLock", "pause": "Pause",
                     "num_lock": "NumLock"}[name]] = special
    for i in range(1, 21):
        f_key = getattr(key, f"f{i}", None)
        if f_key is not None:
            mapping[f"F{i}"] = f_key
    return mapping


def absolute_mouse_coordinates(
    x: int, y: int, left: int, top: int, width: int, height: int
) -> tuple[int, int]:
    """画面座標を SendInput 用の絶対座標(0〜65535)へ変換する。

    left/top/width/height は仮想デスクトップ全体(全モニタを含む矩形)。
    """
    nx = round((x - left) * ABSOLUTE_RANGE / max(1, width - 1))
    ny = round((y - top) * ABSOLUTE_RANGE / max(1, height - 1))
    return (
        min(ABSOLUTE_RANGE, max(0, nx)),
        min(ABSOLUTE_RANGE, max(0, ny)),
    )


class WindowsPointer:
    """Windows でカーソル移動を SendInput として送るための補助。

    pynput は Windows でのカーソル移動に SetCursorPos を使う。これは
    ポインタの座標を書き換えるだけで、マウス移動イベントを入力ストリームに
    流さないため、多くのアプリでホバー(マウスオーバー)が反応しない。
    移動も SendInput で送ることで、実際にマウスを動かしたときと同じ扱いになる。
    """

    # GetSystemMetrics のインデックス(仮想デスクトップ全体の位置とサイズ)
    SM_XVIRTUALSCREEN = 76
    SM_YVIRTUALSCREEN = 77
    SM_CXVIRTUALSCREEN = 78
    SM_CYVIRTUALSCREEN = 79

    MOUSEEVENTF_MOVE = 0x0001
    MOUSEEVENTF_ABSOLUTE = 0x8000
    MOUSEEVENTF_VIRTUALDESK = 0x4000

    def __init__(self) -> None:
        import ctypes
        from ctypes import wintypes

        self._ctypes = ctypes
        self._user32 = ctypes.WinDLL("user32", use_last_error=True)

        class MOUSEINPUT(ctypes.Structure):
            _fields_ = [
                ("dx", wintypes.LONG),
                ("dy", wintypes.LONG),
                ("mouseData", wintypes.DWORD),
                ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD),
                ("dwExtraInfo", wintypes.WPARAM),  # ULONG_PTR 相当
            ]

        class INPUT(ctypes.Structure):
            _fields_ = [("type", wintypes.DWORD), ("mi", MOUSEINPUT)]

        self._INPUT = INPUT
        self._MOUSEINPUT = MOUSEINPUT
        self._user32.SendInput.argtypes = (
            wintypes.UINT,
            ctypes.POINTER(INPUT),
            ctypes.c_int,
        )
        self._user32.SendInput.restype = wintypes.UINT

    def virtual_screen(self) -> tuple[int, int, int, int]:
        metrics = self._user32.GetSystemMetrics
        return (
            metrics(self.SM_XVIRTUALSCREEN),
            metrics(self.SM_YVIRTUALSCREEN),
            metrics(self.SM_CXVIRTUALSCREEN),
            metrics(self.SM_CYVIRTUALSCREEN),
        )

    def move_to(self, x: int, y: int) -> bool:
        """カーソルを動かす。送信できたら True。"""
        left, top, width, height = self.virtual_screen()
        if width <= 0 or height <= 0:
            return False
        nx, ny = absolute_mouse_coordinates(x, y, left, top, width, height)
        event = self._INPUT(
            type=0,  # INPUT_MOUSE
            mi=self._MOUSEINPUT(
                dx=nx,
                dy=ny,
                mouseData=0,
                dwFlags=self.MOUSEEVENTF_MOVE
                | self.MOUSEEVENTF_ABSOLUTE
                | self.MOUSEEVENTF_VIRTUALDESK,
                time=0,
                dwExtraInfo=0,
            ),
        )
        sent = self._user32.SendInput(1, self._ctypes.byref(event), self._ctypes.sizeof(event))
        return sent == 1


def _make_windows_pointer() -> WindowsPointer | None:
    """Windows なら SendInput 版のポインタを用意する。失敗したら None。"""
    if sys.platform != "win32":
        return None
    try:
        return WindowsPointer()
    except Exception as exc:  # ctypes まわりは環境依存で落ちうる
        logger.warning("SendInput を使えないため SetCursorPos を使います: %s", exc)
        return None


class InputController:
    """1 セッション分の入力状態を保持するコントローラ。"""

    def __init__(self) -> None:
        keyboard, mouse = _load_pynput()
        self._keyboard_module = keyboard
        self._mouse_module = mouse
        try:
            self._keyboard = keyboard.Controller()
            self._mouse = mouse.Controller()
        except Exception as exc:  # X11 未接続などで失敗しうる
            raise InputUnavailable(
                "入力デバイスに接続できませんでした。デスクトップにログインした状態で "
                "実行しているか確認してください。"
            ) from exc
        self._key_map = build_key_map(keyboard)
        self._buttons = {
            "left": mouse.Button.left,
            "right": mouse.Button.right,
            "middle": mouse.Button.middle,
        }
        self._lock = threading.Lock()
        self._pressed_keys: set[Any] = set()
        self._pressed_buttons: set[Any] = set()
        self._windows_pointer = _make_windows_pointer()

    # ---- 変換 -------------------------------------------------------

    def resolve_key(self, key: str, code: str = "") -> Any | None:
        """ブラウザのキー情報を pynput のキーに変換する。未対応なら None。"""
        # 左右が区別できる code を優先する
        if code and code in self._key_map:
            return self._key_map[code]
        if key in self._key_map:
            return self._key_map[key]
        if len(key) == 1:
            return key
        return None

    # ---- マウス -----------------------------------------------------

    def get_position(self) -> tuple[int, int]:
        """OS が持っている現在のカーソル位置(画面全体の絶対座標)。"""
        x, y = self._mouse.position
        return int(x), int(y)

    def move_to(self, x: int, y: int) -> None:
        # Windows では SendInput を優先する(SetCursorPos ではホバーが反応しない)
        pointer = self._windows_pointer
        if pointer is not None:
            try:
                if pointer.move_to(int(x), int(y)):
                    return
            except Exception as exc:
                logger.warning("SendInput での移動に失敗しました。以後は従来の方法を使います: %s", exc)
                self._windows_pointer = None
        self._mouse.position = (int(x), int(y))

    def mouse_down(self, x: int, y: int, button: str) -> None:
        target = self._buttons.get(button)
        if target is None:
            return
        self.move_to(x, y)
        with self._lock:
            self._pressed_buttons.add(target)
        self._mouse.press(target)

    def mouse_up(self, x: int, y: int, button: str) -> None:
        target = self._buttons.get(button)
        if target is None:
            return
        self.move_to(x, y)
        self._mouse.release(target)
        with self._lock:
            self._pressed_buttons.discard(target)

    def scroll(self, x: int, y: int, dx: int, dy: int) -> None:
        if dx == 0 and dy == 0:
            return
        self.move_to(x, y)
        self._mouse.scroll(int(dx), int(dy))

    # ---- キーボード -------------------------------------------------

    def key_down(self, key: str, code: str = "") -> bool:
        target = self.resolve_key(key, code)
        if target is None:
            return False
        self._keyboard.press(target)
        with self._lock:
            self._pressed_keys.add(target)
        return True

    def key_up(self, key: str, code: str = "") -> bool:
        target = self.resolve_key(key, code)
        if target is None:
            return False
        self._keyboard.release(target)
        with self._lock:
            self._pressed_keys.discard(target)
        return True

    def type_text(self, text: str) -> None:
        self._keyboard.type(text)

    # ---- 後始末 -----------------------------------------------------

    def release_all(self) -> None:
        """押されたままのキー・ボタンをすべて解放する。

        切断時やセッション終了時に必ず呼ぶこと。呼ばないと修飾キーが
        押しっぱなしになり、ローカルの操作が壊れる。
        """
        with self._lock:
            keys = list(self._pressed_keys)
            buttons = list(self._pressed_buttons)
            self._pressed_keys.clear()
            self._pressed_buttons.clear()
        for button in buttons:
            try:
                self._mouse.release(button)
            except Exception:
                pass
        for key in keys:
            try:
                self._keyboard.release(key)
            except Exception:
                pass


def normalized_to_screen(
    x: float, y: float, left: int, top: int, width: int, height: int
) -> tuple[int, int]:
    """0.0〜1.0 の正規化座標を、モニタ上の絶対座標に変換する。"""
    x = min(1.0, max(0.0, x))
    y = min(1.0, max(0.0, y))
    # 右端・下端で 1 ピクセルはみ出さないように最大値を width-1 に丸める
    screen_x = left + min(width - 1, int(round(x * width)))
    screen_y = top + min(height - 1, int(round(y * height)))
    return screen_x, screen_y


def screen_to_normalized(
    x: int, y: int, left: int, top: int, width: int, height: int
) -> tuple[float, float] | None:
    """画面の絶対座標を 0.0〜1.0 に戻す。対象モニタの外なら None。

    カーソル位置をクライアントに知らせるために使う。別モニタにカーソルが
    ある間は送っても意味がないので None を返す。
    """
    if width <= 0 or height <= 0:
        return None
    nx = (x - left) / width
    ny = (y - top) / height
    if not (0.0 <= nx <= 1.0 and 0.0 <= ny <= 1.0):
        return None
    return nx, ny
