"""ブラウザから操作する文字起こしアプリ（このPC専用）。

    python webapp.py
    → http://127.0.0.1:8765

音声の取り込みはサーバ側、つまりこの PC の WASAPI ループバックで行う。
ブラウザは操作と表示だけを担当する。ブラウザ自身の getDisplayMedia では
タブの音しか取れず、デバイス選択やアプリ横断の取り込みができないため。
"""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import json
import os
import queue
import subprocess
import sys
import tempfile
import threading
import time
import wave
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from fastapi import (
    FastAPI,
    Form,
    HTTPException,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

from live import SegmentBuffer
from loopback import (
    LoopbackError,
    LoopbackRecorder,
    find_loopback_device,
    list_loopback_devices,
    require_pyaudio,
    resample_to_16k,
    to_mono_float,
)
from process_loopback import ProcessLoopbackError, ProcessLoopbackRecorder, list_audio_windows
from transcribe import WRITERS, format_timestamp
from whisper_model import load_model

HERE = Path(__file__).parent
STATIC = HERE / "static"
SAVE_DIR = HERE / "transcripts"   # 結果の自動保存先
LEVEL_INTERVAL = 0.1  # 音量メーターの送信間隔（秒）


# --------------------------------------------------------------------------
# 設定
# --------------------------------------------------------------------------


@dataclass
class Settings:
    """ブラウザから渡される設定。欠けている項目は既定値で補う。"""

    device: str | None = None
    process_id: str | None = None   # 指定するとそのプロセスの音だけを取り込む
    window_title: str | None = None
    model: str = "large-v3"
    language: str = "ja"
    compute_device: str = "auto"
    compute_type: str = "default"
    prompt: str | None = None
    threshold: float = 0.005
    silence: float = 0.7
    min_seconds: float = 2.0
    max_seconds: float = 15.0
    noise_factor: float = 2.0

    @classmethod
    def from_request(cls, body: dict) -> "Settings":
        fields = {f.name: f.type for f in cls.__dataclass_fields__.values()}
        kwargs: dict = {}
        for key, value in body.items():
            if key not in fields or value is None or value == "":
                continue
            kwargs[key] = float(value) if fields[key] == "float" else value
        return cls(**kwargs)

    @property
    def model_key(self) -> tuple:
        return (self.model, self.compute_device, self.compute_type)


# --------------------------------------------------------------------------
# セッション
# --------------------------------------------------------------------------


def explain(exc: Exception, settings: Settings) -> str:
    """例外を、次に何をすればよいか分かる文にする。"""
    text = str(exc)
    lowered = text.lower()

    memory = ("mkl_malloc", "failed to allocate", "bad_alloc", "out of memory", "cannot allocate")
    if any(word in lowered for word in memory):
        where = "GPU" if "cuda" in lowered or settings.compute_device == "cuda" else "CPU"
        advice = (
            "モデルを medium か small に下げてください"
            if settings.model.startswith("large")
            else "他のアプリを閉じてメモリを空けてください"
        )
        if where == "CPU" and settings.compute_device != "cpu":
            advice += "（推論を GPU に切り替えるのも有効です）"
        return f"{where} のメモリが足りません。{advice}。［{text}］"

    return text


@dataclass
class Segment:
    start: float
    end: float
    text: str

    def as_dict(self) -> dict:
        return {
            "start": self.start,
            "end": self.end,
            "text": self.text,
            "stamp": format_timestamp(self.start),
        }


@dataclass
class Session:
    """取り込みと推論をまとめて 1 つだけ走らせる。"""

    mode: str = "idle"  # idle | live | record | file
    detail: str = ""
    segments: list[Segment] = field(default_factory=list)
    source: str = ""

    _loop: asyncio.AbstractEventLoop | None = None
    _subscribers: set[asyncio.Queue] = field(default_factory=set)
    _thread: threading.Thread | None = None
    _stop: threading.Event = field(default_factory=threading.Event)
    _lock: threading.Lock = field(default_factory=threading.Lock)
    _model = None
    _model_key: tuple | None = None
    wav_path: Path | None = None

    # ---- イベント配信 -----------------------------------------------------

    def bind(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop

    def subscribe(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue()
        self._subscribers.add(q)
        return q

    def unsubscribe(self, q: asyncio.Queue) -> None:
        self._subscribers.discard(q)

    def emit(self, event: dict) -> None:
        """ワーカースレッドからイベントループへ橋渡しする。"""
        if self._loop is None:
            return
        self._loop.call_soon_threadsafe(self._fanout, event)

    def _fanout(self, event: dict) -> None:
        for q in list(self._subscribers):
            q.put_nowait(event)

    def set_state(self, mode: str, detail: str = "") -> None:
        self.mode = mode
        self.detail = detail
        self.emit({"type": "state", **self.state()})

    def state(self) -> dict:
        return {
            "mode": self.mode,
            "detail": self.detail,
            "source": self.source,
            "segments": len(self.segments),
        }

    # ---- モデル -----------------------------------------------------------

    def model_for(self, settings: Settings):
        """同じ設定なら読み込み済みのモデルを使い回す。"""
        if self._model is not None and self._model_key == settings.model_key:
            return self._model

        def on_status(kind: str, message: str) -> None:
            # どこで動いているのかを隠さない。GPU のつもりが CPU に
            # 落ちていた、という状況が画面から分かるようにする
            if kind == "loading":
                self.set_state(self.mode, f"読み込み中 {message}")
            elif kind == "fallback":
                self.emit({"type": "warning", "message": message})
            else:
                self.set_state(self.mode, message)

        self._model = load_model(
            settings.model,
            settings.compute_device,
            settings.compute_type,
            on_status=on_status,
        )
        self._model_key = settings.model_key
        return self._model

    # ---- 開始・停止 -------------------------------------------------------

    def start(self, target, settings: Settings, mode: str, source: str) -> None:
        with self._lock:
            if self.mode != "idle":
                raise HTTPException(409, f"すでに実行中です（{self.mode}）")
            self.segments = []
            self.source = source
            self._stop.clear()
            self.set_state(mode, "準備中")
            self._thread = threading.Thread(
                target=self._guard, args=(target, settings), daemon=True
            )
            self._thread.start()

    def _guard(self, target, settings: Settings) -> None:
        try:
            target(settings)
        except Exception as exc:  # noqa: BLE001 - 画面に出して知らせる
            self.emit({"type": "error", "message": explain(exc, settings)})
        finally:
            # 途中で失敗しても、そこまでの結果は残す
            saved = self.save_transcript()
            if saved:
                self.emit({
                    "type": "saved",
                    "folder": str(SAVE_DIR),
                    "names": [p.name for p in saved],
                })
            self.set_state("idle", "")

    def stop(self) -> None:
        self._stop.set()

    def wait(self, timeout: float = 60.0) -> None:
        if self._thread is not None:
            self._thread.join(timeout)

    # ---- 文字起こしワーカー -----------------------------------------------

    def _transcribe_worker(self, model, jobs: queue.Queue, settings: Settings) -> None:
        """区切られた音声を順番に文字起こしして配信する。"""
        while True:
            job = jobs.get()
            if job is None:
                break
            audio, rate, offset = job
            segments, _ = model.transcribe(
                resample_to_16k(audio, rate),
                language=settings.language,
                vad_filter=True,
                initial_prompt=settings.prompt,
                beam_size=1,  # 遅延を抑えるため貪欲デコード
            )
            text = " ".join(seg.text.strip() for seg in segments).strip()
            if not text:
                continue
            segment = Segment(offset, offset + len(audio) / rate, text)
            self.segments.append(segment)
            self.emit({"type": "segment", **segment.as_dict()})

    # ---- 保存 -------------------------------------------------------------

    def save_transcript(self) -> list[Path]:
        """結果を transcripts/ に書き出す。

        ダウンロードを押し忘れても消えないよう、終わった時点で必ず残す。
        """
        if not self.segments:
            return []
        SAVE_DIR.mkdir(exist_ok=True)
        stem = time.strftime("%Y-%m-%d_%H%M%S")
        rows = [s.as_dict() for s in self.segments]
        paths = []
        for fmt in ("txt", "srt"):
            path = SAVE_DIR / f"{stem}.{fmt}"
            WRITERS[fmt](path, rows)
            paths.append(path)
        return paths

    # ---- 録音元 -----------------------------------------------------------

    def open_recorder(self, settings: Settings):
        """録音元を開いて返す。呼び出し側が __exit__ する責任を持つ。

        ウィンドウ（プロセス）指定が使えない環境は珍しくないので、
        失敗しても止めずにデバイス録音へ退避し、理由を画面に出す。
        """
        if settings.process_id:
            recorder = ProcessLoopbackRecorder(
                int(settings.process_id), settings.window_title or ""
            )
            try:
                recorder.__enter__()
                return recorder
            except (ProcessLoopbackError, OSError) as exc:
                self.emit({
                    "type": "warning",
                    "message": f"ウィンドウ単位の取り込みに失敗しました（{exc}）。"
                               "デバイス全体の録音に切り替えます。",
                })

        recorder = LoopbackRecorder(settings.device)
        recorder.__enter__()
        return recorder

    # ---- リアルタイム -----------------------------------------------------

    def run_live(self, settings: Settings) -> None:
        model = self.model_for(settings)
        jobs: queue.Queue = queue.Queue()
        worker = threading.Thread(
            target=self._transcribe_worker, args=(model, jobs, settings), daemon=True
        )
        worker.start()

        rec = self.open_recorder(settings)
        try:
            self.source = rec.device["name"]
            self.set_state("live", "取り込み中")
            buffer = SegmentBuffer(
                rate=rec.rate,
                threshold=settings.threshold,
                silence=settings.silence,
                min_seconds=settings.min_seconds,
                max_seconds=settings.max_seconds,
                noise_factor=settings.noise_factor,
            )
            # 無音だけのバッファは捨てられるので、区切りの先頭位置は
            # 取り込んだ総量から逆算する。捨てられた分もここには含まれる
            total = 0.0
            last_level = 0.0

            for frame in rec.frames():
                if self._stop.is_set():
                    break
                mono = to_mono_float(frame)
                total += len(mono) / rec.rate

                now = time.monotonic()
                if now - last_level >= LEVEL_INTERVAL:
                    last_level = now
                    rms = float(np.sqrt(np.mean(np.square(mono))))
                    self.emit({"type": "level", "rms": rms, "elapsed": total})

                segment = buffer.push(mono)
                if segment is not None:
                    jobs.put((segment, rec.rate, total - len(segment) / rec.rate))

            tail = buffer.flush()
            if tail is not None:
                jobs.put((tail, rec.rate, total - len(tail) / rec.rate))
        finally:
            rec.__exit__(None, None, None)

        self.set_state("live", "残りを処理中")
        jobs.put(None)
        worker.join()

    # ---- 録音してから文字起こし -------------------------------------------

    def run_record(self, settings: Settings) -> None:
        path = Path(tempfile.gettempdir()) / f"loopback-{int(time.time())}.wav"
        rec = self.open_recorder(settings)
        try:
            self.source = rec.device["name"]
            self.set_state("record", "録音中")
            with wave.open(str(path), "wb") as wav:
                wav.setnchannels(rec.channels)
                wav.setsampwidth(2)
                wav.setframerate(rec.rate)
                written = 0
                last_level = 0.0
                for frame in rec.frames():
                    if self._stop.is_set():
                        break
                    wav.writeframes(frame.tobytes())
                    written += len(frame)
                    now = time.monotonic()
                    if now - last_level >= LEVEL_INTERVAL:
                        last_level = now
                        rms = float(np.sqrt(np.mean(np.square(to_mono_float(frame)))))
                        self.emit(
                            {"type": "level", "rms": rms, "elapsed": written / rec.rate}
                        )
        finally:
            rec.__exit__(None, None, None)

        self.wav_path = path
        self.emit({"type": "recorded", "path": str(path), "name": path.name})
        self.transcribe_file(path, settings, keep_state="record")

    # ---- ファイルを文字起こし ---------------------------------------------

    def run_file(self, settings: Settings) -> None:
        if self.wav_path is None:
            raise LoopbackError("文字起こしする音声がありません")
        self.transcribe_file(self.wav_path, settings, keep_state="file")

    def transcribe_file(self, path: Path, settings: Settings, keep_state: str) -> None:
        model = self.model_for(settings)
        self.set_state(keep_state, "文字起こし中")
        segments, info = model.transcribe(
            str(path),
            language=settings.language,
            vad_filter=True,
            initial_prompt=settings.prompt,
            beam_size=5,
        )
        self.emit({"type": "info", "language": info.language, "duration": info.duration})
        for seg in segments:
            if self._stop.is_set():
                break
            text = seg.text.strip()
            if not text:
                continue
            segment = Segment(seg.start, seg.end, text)
            self.segments.append(segment)
            self.emit(
                {
                    "type": "segment",
                    **segment.as_dict(),
                    "progress": seg.end / info.duration if info.duration else None,
                }
            )


session = Session()


# --------------------------------------------------------------------------
# API
# --------------------------------------------------------------------------

@contextlib.asynccontextmanager
async def lifespan(_: FastAPI):
    session.bind(asyncio.get_running_loop())
    yield


app = FastAPI(title="windows-transcribe", lifespan=lifespan)


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(STATIC / "index.html")


@app.get("/api/devices")
async def devices() -> JSONResponse:
    """ループバックデバイスの一覧。取り込めない環境では理由を返す。"""
    try:
        pa_mod = require_pyaudio()
        pa = pa_mod.PyAudio()
    except LoopbackError as exc:
        return JSONResponse({"devices": [], "error": str(exc)})

    try:
        try:
            default_index = find_loopback_device(pa)["index"]
        except LoopbackError:
            default_index = None
        found = [
            {
                "index": int(d["index"]),
                "name": d["name"],
                "rate": int(d["defaultSampleRate"]),
                "channels": int(d["maxInputChannels"]),
                "default": int(d["index"]) == default_index,
            }
            for d in list_loopback_devices(pa)
        ]
    finally:
        pa.terminate()
    return JSONResponse({"devices": found, "error": None})


@app.get("/api/windows")
async def windows() -> JSONResponse:
    """音を出しうるウィンドウの一覧。取り込めない環境では理由を返す。"""
    try:
        return JSONResponse({"windows": list_audio_windows(), "error": None})
    except (ProcessLoopbackError, OSError) as exc:
        return JSONResponse({"windows": [], "error": str(exc)})


@app.get("/api/state")
async def state() -> JSONResponse:
    return JSONResponse(
        {**session.state(), "segments_detail": [s.as_dict() for s in session.segments]}
    )


@app.post("/api/live/start")
async def live_start(body: dict) -> JSONResponse:
    settings = Settings.from_request(body)
    session.start(session.run_live, settings, "live", "ループバック")
    return JSONResponse(session.state())


@app.post("/api/record/start")
async def record_start(body: dict) -> JSONResponse:
    settings = Settings.from_request(body)
    session.start(session.run_record, settings, "record", "ループバック")
    return JSONResponse(session.state())


@app.post("/api/stop")
async def stop() -> JSONResponse:
    session.stop()
    return JSONResponse(session.state())


@app.post("/api/upload")
async def upload(file: UploadFile, body: str = Form("{}")) -> JSONResponse:
    """音声ファイルを受け取って文字起こしする。"""
    settings = Settings.from_request(json.loads(body))
    suffix = Path(file.filename or "audio.wav").suffix or ".wav"
    path = Path(tempfile.gettempdir()) / f"upload-{int(time.time())}{suffix}"
    path.write_bytes(await file.read())
    session.wav_path = path
    session.start(session.run_file, settings, "file", file.filename or path.name)
    return JSONResponse(session.state())


@app.get("/api/download.{fmt}")
async def download(fmt: str) -> FileResponse:
    if fmt not in WRITERS:
        raise HTTPException(404, f"未対応の形式: {fmt}")
    if not session.segments:
        raise HTTPException(404, "書き出す内容がありません")
    stem = Path(session.source or "transcript").stem or "transcript"
    path = Path(tempfile.gettempdir()) / f"{stem}.{fmt}"
    WRITERS[fmt](path, [s.as_dict() for s in session.segments])
    return FileResponse(path, filename=path.name, media_type="text/plain")


@app.post("/api/reveal")
async def reveal() -> JSONResponse:
    """保存先のフォルダをエクスプローラーで開く。"""
    SAVE_DIR.mkdir(exist_ok=True)
    if sys.platform == "win32":
        os.startfile(SAVE_DIR)  # noqa: S606 - ローカル専用アプリ
    elif sys.platform == "darwin":
        subprocess.Popen(["open", str(SAVE_DIR)])
    else:
        raise HTTPException(400, f"この環境では開けません: {SAVE_DIR}")
    return JSONResponse({"folder": str(SAVE_DIR)})


@app.get("/healthz")
async def healthz() -> PlainTextResponse:
    return PlainTextResponse("ok")


@app.websocket("/ws")
async def ws(socket: WebSocket) -> None:
    await socket.accept()
    q = session.subscribe()
    try:
        await socket.send_json(
            {
                "type": "state",
                **session.state(),
                "history": [s.as_dict() for s in session.segments],
            }
        )
        while True:
            await socket.send_json(await q.get())
    except WebSocketDisconnect:
        pass
    finally:
        session.unsubscribe(q)


app.mount("/static", StaticFiles(directory=STATIC), name="static")


# --------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description="ブラウザから使う文字起こしアプリ")
    parser.add_argument("--host", default="127.0.0.1", help="待ち受けアドレス")
    parser.add_argument("--port", type=int, default=8765, help="待ち受けポート")
    parser.add_argument("--open", action="store_true", help="ブラウザを自動で開く")
    args = parser.parse_args()

    import uvicorn

    url = f"http://{args.host}:{args.port}"
    print(f"起動しました: {url}")
    print("停止するには Ctrl+C")
    if args.open:
        import webbrowser

        threading.Timer(1.0, lambda: webbrowser.open(url)).start()

    with contextlib.suppress(KeyboardInterrupt):
        uvicorn.run(app, host=args.host, port=args.port, log_level="warning")


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as exc:
        raise SystemExit(str(exc))
