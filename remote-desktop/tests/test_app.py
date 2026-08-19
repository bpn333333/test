"""HTTP / WebSocket の統合テスト。実画面と実デバイスは偽物に差し替える。"""

import contextlib
import json
import threading
import time

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from rdcontrol.app import WS_TOO_MANY_CLIENTS, WS_UNAUTHORIZED, create_app
from rdcontrol.capture import Frame, MonitorInfo
from rdcontrol.config import Settings

TOKEN = "test-token"


class FakeCapture:
    """1x1 の JPEG を返すだけのキャプチャ。フレームは呼ぶたびに変化する。"""

    def __init__(self) -> None:
        self.monitor_index = 1
        self._counter = 0
        self._monitors = [
            MonitorInfo(0, 0, 0, 3200, 1080),
            MonitorInfo(1, 0, 0, 1920, 1080),
            MonitorInfo(2, 1920, 0, 1280, 1024),
        ]

    def monitors(self):
        return list(self._monitors)

    def current_monitor(self):
        return next(m for m in self._monitors if m.index == self.monitor_index)

    def select_monitor(self, index: int) -> bool:
        if not any(m.index == index for m in self._monitors):
            return False
        self.monitor_index = index
        return True

    def grab(self, *, quality: int = 60, scale: float = 1.0) -> Frame:
        self._counter += 1
        payload = b"\xff\xd8\xff" + bytes([self._counter % 251])
        return Frame(
            jpeg=payload,
            width=16,
            height=9,
            screen_width=1920,
            screen_height=1080,
            digest=str(self._counter),
        )

    def close(self) -> None:
        pass


class FakeController:
    """呼び出しを記録するだけの入力コントローラ。"""

    def __init__(self) -> None:
        self.calls: list[tuple] = []
        self._position = (100, 100)
        self._lock = threading.Lock()

    def _record(self, *call) -> None:
        with self._lock:
            self.calls.append(call)

    def get_position(self) -> tuple[int, int]:
        return self._position

    def move_to(self, x, y):
        self._position = (x, y)
        self._record("move", x, y)

    def mouse_down(self, x, y, button):
        self._position = (x, y)
        self._record("down", x, y, button)

    def mouse_up(self, x, y, button):
        self._position = (x, y)
        self._record("up", x, y, button)

    def scroll(self, x, y, dx, dy):
        self._record("scroll", x, y, dx, dy)

    def key_down(self, key, code=""):
        self._record("key_down", key, code)

    def key_up(self, key, code=""):
        self._record("key_up", key, code)

    def type_text(self, text):
        self._record("text", text)

    def release_all(self):
        self._record("release_all")

    def snapshot(self) -> list[tuple]:
        with self._lock:
            return list(self.calls)


@pytest.fixture
def controller() -> FakeController:
    return FakeController()


def make_client(controller: FakeController | None, **settings_kwargs) -> TestClient:
    settings = Settings(token=TOKEN, **settings_kwargs)
    app = create_app(settings, capture=FakeCapture(), controller=controller)
    return TestClient(app)


def receive_text(websocket) -> dict:
    """フレーム(バイナリ)を読み飛ばして次の JSON メッセージを返す。"""
    for _ in range(200):
        message = websocket.receive()
        if "text" in message and message["text"] is not None:
            return json.loads(message["text"])
    raise AssertionError("JSON メッセージが届きませんでした")


def wait_for_clients(client: TestClient, expected: int) -> None:
    """サーバー側のセッション数が期待値になるまで待つ。"""
    for _ in range(300):
        if client.get("/healthz").json()["clients"] == expected:
            return
        time.sleep(0.01)
    raise AssertionError(f"接続数が {expected} になりませんでした")


@contextlib.contextmanager
def open_session(client: TestClient, remaining: int = 0):
    """WebSocket を開き、抜けるときにサーバー側の後始末完了まで待つ。

    TestClient は切断を送った直後にアプリのタスクをキャンセルするため、
    待たずに抜けるとサーバーの終了処理と競合してテストが不安定になる。
    """
    with client.websocket_connect(f"/ws?token={TOKEN}") as websocket:
        yield websocket
        websocket.close(1000)
        wait_for_clients(client, remaining)


def sync(websocket) -> None:
    """ping/pong で、直前に送った入力の処理完了を待ち合わせる。"""
    websocket.send_json({"t": "ping"})
    while True:
        message = receive_text(websocket)
        if message["t"] == "pong":
            return


def test_page_requires_a_valid_token(controller):
    with make_client(controller) as client:
        assert client.get("/").status_code == 401
        assert client.get("/", params={"token": "nope"}).status_code == 401
        response = client.get("/", params={"token": TOKEN})
        assert response.status_code == 200
        assert "rdcontrol" in response.text


def test_unauthorized_page_explains_the_common_causes_without_leaking_the_token(controller):
    with make_client(controller) as client:
        body = client.get("/", params={"token": "..."}).text
        # 実際に多い原因(プレースホルダのまま / 途中で切れた / 再起動でトークンが変わった)
        assert "プレースホルダ" in body
        assert "切れて" in body
        assert "起動のたびに変わります" in body
        # 未認証の相手にトークンそのものを見せない
        assert TOKEN not in body


def test_healthz_is_open_and_reports_client_count(controller):
    with make_client(controller) as client:
        response = client.get("/healthz")
        assert response.status_code == 200
        assert response.json() == {"status": "ok", "clients": 0}


def test_websocket_rejects_a_wrong_token(controller):
    with make_client(controller) as client:
        with pytest.raises(WebSocketDisconnect) as excinfo:
            with client.websocket_connect("/ws?token=wrong") as websocket:
                websocket.receive()
        assert excinfo.value.code == WS_UNAUTHORIZED


def test_hello_describes_the_session_and_frames_start_flowing(controller):
    with make_client(controller) as client:
        with open_session(client) as websocket:
            hello = receive_text(websocket)
            assert hello["t"] == "hello"
            assert hello["has_control"] is True
            assert hello["view_only"] is False
            assert [m["index"] for m in hello["monitors"]] == [0, 1, 2]

            message = websocket.receive()
            assert message.get("bytes", b"").startswith(b"\xff\xd8\xff")


def test_cursor_position_is_streamed_so_the_client_can_draw_it(controller):
    # キャプチャ画像にポインタは写らないため、位置だけ別に送っている
    with make_client(controller) as client:
        with open_session(client) as websocket:
            receive_text(websocket)
            while True:
                message = receive_text(websocket)
                if message["t"] == "cursor":
                    break
            assert message["visible"] is True
            assert message["x"] == pytest.approx(100 / 1920)
            assert message["y"] == pytest.approx(100 / 1080)


def test_cursor_on_another_monitor_is_reported_as_hidden(controller):
    controller._position = (5000, 5000)  # モニタ 1 の外
    with make_client(controller) as client:
        with open_session(client) as websocket:
            receive_text(websocket)
            while True:
                message = receive_text(websocket)
                if message["t"] == "cursor":
                    break
            assert message["visible"] is False
            assert "x" not in message


def test_mouse_events_reach_the_controller_in_screen_coordinates(controller):
    with make_client(controller) as client:
        with open_session(client) as websocket:
            receive_text(websocket)
            websocket.send_json({"t": "mouse_down", "x": 0.5, "y": 0.5, "button": "right"})
            websocket.send_json({"t": "mouse_up", "x": 0.5, "y": 0.5, "button": "right"})
            sync(websocket)

    calls = controller.snapshot()
    assert ("down", 960, 540, "right") in calls
    assert ("up", 960, 540, "right") in calls


def test_events_are_mapped_onto_the_selected_monitor(controller):
    with make_client(controller) as client:
        with open_session(client) as websocket:
            receive_text(websocket)
            websocket.send_json({"t": "config", "monitor": 2})
            sync(websocket)
            websocket.send_json({"t": "mouse_move", "x": 0.0, "y": 0.0})
            sync(websocket)

    assert ("move", 1920, 0) in controller.snapshot()


def test_config_changes_are_echoed_back(controller):
    with make_client(controller) as client:
        with open_session(client) as websocket:
            receive_text(websocket)
            websocket.send_json({"t": "config", "quality": 25, "fps": 3, "scale": 0.5})
            while True:
                message = receive_text(websocket)
                if message["t"] == "config":
                    break
            assert message["quality"] == 25
            assert message["fps"] == 3
            assert message["scale"] == 0.5


def test_invalid_messages_get_an_error_and_the_session_survives(controller):
    with make_client(controller) as client:
        with open_session(client) as websocket:
            receive_text(websocket)
            websocket.send_text('{"t": "rm -rf"}')
            while True:
                message = receive_text(websocket)
                if message["t"] == "error":
                    break
            assert "invalid message" in message["message"]
            sync(websocket)  # まだ生きていることを確認


def test_typed_text_is_sent_to_the_keyboard(controller):
    # スマホのソフトキーボードは、1 文字ずつのキーイベントではなく文字列で届く
    with make_client(controller) as client:
        with open_session(client) as websocket:
            receive_text(websocket)
            websocket.send_json({"t": "text", "text": "こんにちは"})
            sync(websocket)

    assert ("text", "こんにちは") in controller.snapshot()


def test_view_only_server_ignores_input(controller):
    with make_client(controller, view_only=True) as client:
        with open_session(client) as websocket:
            hello = receive_text(websocket)
            assert hello["view_only"] is True
            assert hello["has_control"] is False
            websocket.send_json({"t": "mouse_down", "x": 0.5, "y": 0.5, "button": "left"})
            sync(websocket)

    assert not [call for call in controller.snapshot() if call[0] == "down"]


def test_second_client_can_watch_but_not_control(controller):
    with make_client(controller) as client:
        with open_session(client) as first:
            receive_text(first)
            with open_session(client, remaining=1) as second:
                hello = receive_text(second)
                assert hello["has_control"] is False
                second.send_json({"t": "key_down", "key": "a", "code": "KeyA"})
                sync(second)

    assert not [call for call in controller.snapshot() if call[0] == "key_down"]


def test_client_limit_closes_extra_connections(controller):
    with make_client(controller, max_clients=1) as client:
        with open_session(client) as first:
            receive_text(first)
            with pytest.raises(WebSocketDisconnect) as excinfo:
                with client.websocket_connect(f"/ws?token={TOKEN}") as second:
                    second.receive()
            assert excinfo.value.code == WS_TOO_MANY_CLIENTS


def test_held_keys_are_released_when_the_controller_disconnects(controller):
    with make_client(controller) as client:
        with open_session(client) as websocket:
            receive_text(websocket)
            websocket.send_json({"t": "key_down", "key": "Control", "code": "ControlLeft"})
            sync(websocket)

    assert ("release_all",) in controller.snapshot()
