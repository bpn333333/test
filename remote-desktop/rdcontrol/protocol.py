"""クライアント → サーバー間で流れる JSON メッセージの検証。

ネットワーク越しに届く値は一切信用せず、この層で型・範囲・列挙値を
すべて検証してから上位層に渡す。
"""

from __future__ import annotations

import json
from typing import Any

MOUSE_BUTTONS = frozenset({"left", "right", "middle"})

# 座標を伴うポインタ系イベント
_POINTER_TYPES = frozenset({"mouse_move", "mouse_down", "mouse_up", "scroll"})
# キーボード系イベント
_KEY_TYPES = frozenset({"key_down", "key_up"})

MESSAGE_TYPES = _POINTER_TYPES | _KEY_TYPES | frozenset({"text", "config", "ping"})

MAX_MESSAGE_BYTES = 8 * 1024
MAX_TEXT_LENGTH = 4096

# config で受け付ける範囲
QUALITY_RANGE = (10, 95)
FPS_RANGE = (1, 30)
SCALE_RANGE = (0.2, 1.0)


class ProtocolError(ValueError):
    """クライアントから不正なメッセージが届いたことを示す。"""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ProtocolError(message)


def _number(value: Any, name: str) -> float:
    _require(isinstance(value, (int, float)) and not isinstance(value, bool), f"{name} must be a number")
    value = float(value)
    _require(value == value and abs(value) != float("inf"), f"{name} must be finite")
    return value


def _unit(value: Any, name: str) -> float:
    """0.0〜1.0 に正規化された座標。範囲外はクランプする。"""
    return min(1.0, max(0.0, _number(value, name)))


def _string(value: Any, name: str, max_length: int) -> str:
    _require(isinstance(value, str), f"{name} must be a string")
    _require(len(value) <= max_length, f"{name} is too long")
    return value


def parse_client_message(raw: str | bytes) -> dict[str, Any]:
    """WebSocket で受信した生データを検証済みの dict に変換する。

    戻り値は必ず ``t`` キーを持ち、型ごとに必要なフィールドが
    正規化された状態で入っている。
    """
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8", errors="replace")
    _require(len(raw) <= MAX_MESSAGE_BYTES, "message too large")

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:  # pragma: no cover - メッセージ本文は環境依存
        raise ProtocolError(f"invalid JSON: {exc.msg}") from exc

    _require(isinstance(payload, dict), "message must be a JSON object")

    msg_type = payload.get("t")
    _require(msg_type in MESSAGE_TYPES, f"unknown message type: {msg_type!r}")

    if msg_type in _POINTER_TYPES:
        message: dict[str, Any] = {
            "t": msg_type,
            "x": _unit(payload.get("x"), "x"),
            "y": _unit(payload.get("y"), "y"),
        }
        if msg_type in ("mouse_down", "mouse_up"):
            button = payload.get("button", "left")
            _require(button in MOUSE_BUTTONS, f"unknown button: {button!r}")
            message["button"] = button
        if msg_type == "scroll":
            # ブラウザの deltaY はピクセル単位なのでノッチ数に丸める
            message["dx"] = _clamp_scroll(_number(payload.get("dx", 0), "dx"))
            message["dy"] = _clamp_scroll(_number(payload.get("dy", 0), "dy"))
        return message

    if msg_type in _KEY_TYPES:
        return {
            "t": msg_type,
            "key": _string(payload.get("key", ""), "key", 32),
            "code": _string(payload.get("code", ""), "code", 32),
        }

    if msg_type == "text":
        return {"t": "text", "text": _string(payload.get("text", ""), "text", MAX_TEXT_LENGTH)}

    if msg_type == "config":
        message = {"t": "config"}
        if "quality" in payload:
            message["quality"] = int(_clamp(_number(payload["quality"], "quality"), *QUALITY_RANGE))
        if "fps" in payload:
            message["fps"] = int(_clamp(_number(payload["fps"], "fps"), *FPS_RANGE))
        if "scale" in payload:
            message["scale"] = _clamp(_number(payload["scale"], "scale"), *SCALE_RANGE)
        if "monitor" in payload:
            monitor = _number(payload["monitor"], "monitor")
            _require(monitor == int(monitor) and 0 <= monitor < 16, "monitor out of range")
            message["monitor"] = int(monitor)
        return message

    return {"t": "ping"}


def _clamp(value: float, low: float, high: float) -> float:
    return min(high, max(low, value))


def _clamp_scroll(value: float) -> int:
    """スクロール量をノッチ数(整数)に変換し、暴走を防ぐため上限をかける。"""
    notches = int(_clamp(value, -30.0, 30.0))
    return notches
