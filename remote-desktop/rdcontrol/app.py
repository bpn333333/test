"""FastAPI アプリケーション本体。

HTTP で操作用ページを配信し、WebSocket で
「サーバー → クライアント: JPEG フレーム」「クライアント → サーバー: 入力イベント」
を双方向にやり取りする。
"""

from __future__ import annotations

import asyncio
import logging
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Query, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .auth import AuthGuard
from .capture import CaptureUnavailable, ScreenCapture
from .config import Settings
from .input_control import InputController, InputUnavailable, normalized_to_screen
from .protocol import ProtocolError, parse_client_message
from .session import ClientSession, SessionManager

logger = logging.getLogger("rdcontrol")

STATIC_DIR = Path(__file__).parent / "static"

# WebSocket のクローズコード(4000 番台はアプリ定義)
WS_UNAUTHORIZED = 4401
WS_TOO_MANY_CLIENTS = 4429
WS_SERVER_ERROR = 4500


_UNSET = object()


def create_app(
    settings: Settings,
    *,
    capture: Any = None,
    controller: Any = _UNSET,
) -> FastAPI:
    """アプリを組み立てる。

    capture / controller はテスト時に差し替えられるようにしてある。
    省略した場合は実際の画面とデバイスに接続する。
    """
    if capture is None:
        capture = ScreenCapture(monitor=settings.monitor)
    guard = AuthGuard(settings.token)
    manager = SessionManager(settings)

    input_error: str | None = None
    if settings.view_only:
        controller = None
        input_error = "サーバーが --view-only で起動しているため操作は無効です。"
    elif controller is _UNSET:
        controller = None
        try:
            controller = InputController()
        except InputUnavailable as exc:
            input_error = str(exc)
            logger.warning("入力制御を無効化します: %s", exc)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        yield
        if controller is not None:
            controller.release_all()
        capture.close()

    app = FastAPI(
        title="rdcontrol",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
        lifespan=lifespan,
    )

    app.state.settings = settings
    app.state.capture = capture
    app.state.manager = manager
    app.state.controller = controller
    app.state.input_error = input_error

    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.get("/healthz")
    async def healthz() -> JSONResponse:
        return JSONResponse({"status": "ok", "clients": len(manager.sessions)})

    @app.get("/", response_class=HTMLResponse)
    async def index(request: Request, token: str = Query(default="")) -> Any:
        client_ip = request.client.host if request.client else "unknown"
        if not guard.check(client_ip, token):
            logger.warning("認証失敗: %s (失敗 %d 回)", client_ip, guard.failures(client_ip))
            return HTMLResponse(
                "<h1>401 Unauthorized</h1><p>トークンが正しくありません。"
                "サーバー起動時に表示された URL をそのまま開いてください。</p>",
                status_code=401,
            )
        return FileResponse(STATIC_DIR / "index.html")

    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket) -> None:
        client_ip = websocket.client.host if websocket.client else "unknown"
        token = websocket.query_params.get("token", "")
        if not guard.check(client_ip, token):
            logger.warning("WebSocket 認証失敗: %s", client_ip)
            await websocket.close(code=WS_UNAUTHORIZED, reason="unauthorized")
            return
        if manager.is_full():
            await websocket.close(code=WS_TOO_MANY_CLIENTS, reason="too many clients")
            return

        await websocket.accept()
        session = manager.add(client_ip)
        logger.info(
            "接続: client=%d from=%s 操作権=%s", session.id, client_ip, session.has_control
        )
        try:
            await _serve_session(websocket, session, app)
        except WebSocketDisconnect:
            pass
        except Exception:  # 予期しない例外でもクリーンアップは必ず通す
            logger.exception("セッション %d で例外が発生しました", session.id)
        finally:
            had_control = session.has_control
            successor = manager.remove(session)
            if had_control and controller is not None:
                # 操作していたクライアントが切れた場合、押しっぱなしの
                # キー・ボタンを必ず解放する
                controller.release_all()
            logger.info("切断: client=%d", session.id)
            if successor is not None:
                logger.info("操作権を client=%d へ引き継ぎました", successor.id)

    return app


async def _serve_session(websocket: WebSocket, session: ClientSession, app: FastAPI) -> None:
    settings: Settings = app.state.settings
    capture: ScreenCapture = app.state.capture

    monitors = [
        {"index": m.index, "label": m.label, "width": m.width, "height": m.height}
        for m in capture.monitors()
    ]
    await websocket.send_json(
        {
            "t": "hello",
            "client_id": session.id,
            "has_control": session.has_control,
            "view_only": settings.view_only or app.state.controller is None,
            "input_error": app.state.input_error,
            "monitor": capture.monitor_index,
            "monitors": monitors,
            "quality": session.quality,
            "fps": session.fps,
            "scale": session.scale,
        }
    )

    receiver = asyncio.create_task(_receive_loop(websocket, session, app))
    streamer = asyncio.create_task(_stream_loop(websocket, session, app))
    done, pending = await asyncio.wait(
        {receiver, streamer}, return_when=asyncio.FIRST_COMPLETED
    )
    for task in pending:
        task.cancel()
    await asyncio.gather(*pending, return_exceptions=True)

    # 片方が落ちたときも、両方の例外を必ず回収してから再送出する
    # (回収し損ねると "Task exception was never retrieved" になる)
    failure: BaseException | None = None
    for task in done:
        exc = task.exception()
        if exc is None or isinstance(exc, (WebSocketDisconnect, asyncio.CancelledError)):
            continue
        if failure is None:
            failure = exc
    if failure is not None:
        raise failure


async def _stream_loop(websocket: WebSocket, session: ClientSession, app: FastAPI) -> None:
    """一定間隔で画面をキャプチャし、変化があったときだけ送信する。"""
    capture: ScreenCapture = app.state.capture
    last_digest = ""
    last_sent = 0.0
    while True:
        started = time.monotonic()
        try:
            frame = await asyncio.to_thread(
                capture.grab, quality=session.quality, scale=session.scale
            )
        except CaptureUnavailable as exc:
            await websocket.send_json({"t": "error", "message": str(exc)})
            await websocket.close(code=WS_SERVER_ERROR, reason="capture failed")
            return

        # 画面が静止しているときは無駄な送信を避ける。ただし 2 秒に 1 回は
        # 送って、接続が生きていることをクライアントに伝える。
        now = time.monotonic()
        if frame.digest != last_digest or now - last_sent > 2.0:
            try:
                await websocket.send_bytes(frame.jpeg)
            except (WebSocketDisconnect, RuntimeError):
                # 相手が切断した直後の送信。配信ループを静かに終える。
                return
            last_digest = frame.digest
            last_sent = now

        elapsed = time.monotonic() - started
        await asyncio.sleep(max(0.0, session.frame_interval - elapsed))


async def _receive_loop(websocket: WebSocket, session: ClientSession, app: FastAPI) -> None:
    """クライアントからの入力イベントを処理する。"""
    settings: Settings = app.state.settings
    capture: ScreenCapture = app.state.capture
    controller: InputController | None = app.state.controller

    while True:
        packet = await websocket.receive()
        if packet["type"] == "websocket.disconnect":
            return
        # 通常はテキストだが、バイナリで送ってくるクライアントも受け付ける
        raw = packet.get("text")
        if raw is None:
            raw = (packet.get("bytes") or b"").decode("utf-8", errors="replace")
        try:
            message = parse_client_message(raw)
        except ProtocolError as exc:
            logger.warning("client=%d 不正なメッセージ: %s", session.id, exc)
            await websocket.send_json({"t": "error", "message": f"invalid message: {exc}"})
            continue

        kind = message["t"]

        if kind == "ping":
            await websocket.send_json({"t": "pong"})
            continue

        if kind == "config":
            session.apply_config(message)
            if "monitor" in message and capture.select_monitor(int(message["monitor"])):
                logger.info("client=%d モニタを %s に切り替え", session.id, message["monitor"])
            await websocket.send_json(
                {
                    "t": "config",
                    "quality": session.quality,
                    "fps": session.fps,
                    "scale": session.scale,
                    "monitor": capture.monitor_index,
                }
            )
            continue

        # ここから先は操作系。権限がなければ黙って捨てる(通知はまとめて 1 回)。
        if controller is None or settings.view_only or not session.has_control:
            continue

        await asyncio.to_thread(_dispatch_input, message, controller, capture)


def _dispatch_input(
    message: dict[str, Any], controller: InputController, capture: ScreenCapture
) -> None:
    """入力イベントを実際のデバイス操作へ変換する(ワーカースレッドで実行)。"""
    kind = message["t"]
    if kind in ("mouse_move", "mouse_down", "mouse_up", "scroll"):
        monitor = capture.current_monitor()
        x, y = normalized_to_screen(
            message["x"], message["y"], monitor.left, monitor.top, monitor.width, monitor.height
        )
        if kind == "mouse_move":
            controller.move_to(x, y)
        elif kind == "mouse_down":
            controller.mouse_down(x, y, message["button"])
        elif kind == "mouse_up":
            controller.mouse_up(x, y, message["button"])
        else:
            controller.scroll(x, y, message["dx"], message["dy"])
        return

    if kind == "key_down":
        controller.key_down(message["key"], message["code"])
    elif kind == "key_up":
        controller.key_up(message["key"], message["code"])
    elif kind == "text":
        controller.type_text(message["text"])
