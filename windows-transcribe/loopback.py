"""WASAPI ループバック入力（Windows 専用）。

Windows の WASAPI は「再生中の音をそのまま入力として読む」ループバック機能を
OS 標準で持っているため、VB-CABLE などの仮想オーディオデバイスを
インストールしなくてもデスクトップ音声を録音できる。
"""

from __future__ import annotations

import numpy as np

try:  # Windows 専用。他 OS では import に失敗する
    import pyaudiowpatch as pyaudio
except ImportError:  # pragma: no cover - 実行環境依存
    pyaudio = None

CHUNK = 2048


class LoopbackError(RuntimeError):
    """取り込みを開始できない。CLI は終了、サーバは 400 として扱う。"""


def require_pyaudio():
    if pyaudio is None:
        raise LoopbackError(
            "PyAudioWPatch が見つかりません（Windows 専用）。"
            "  pip install PyAudioWPatch"
        )
    return pyaudio


def list_loopback_devices(pa) -> list[dict]:
    """利用可能なループバックデバイスを列挙する。"""
    return list(pa.get_loopback_device_info_generator())


def find_loopback_device(pa, hint: str | None = None) -> dict:
    """録音対象のループバックデバイスを決める。

    hint があれば名前の部分一致で選び、無ければ既定の再生デバイスに
    対応するループバックを選ぶ。
    """
    devices = list_loopback_devices(pa)
    if not devices:
        raise LoopbackError(
            "ループバックデバイスが見つかりません。"
            "サウンド設定で有効な再生デバイスがあるか確認してください。"
        )

    if hint:
        needle = hint.lower()
        for dev in devices:
            if needle in dev["name"].lower():
                return dev
        names = "\n".join(f"  [{d['index']}] {d['name']}" for d in devices)
        raise LoopbackError(f"'{hint}' に一致するデバイスがありません。候補:\n{names}")

    wasapi = pa.get_host_api_info_by_type(pyaudio.paWASAPI)
    speakers = pa.get_device_info_by_index(wasapi["defaultOutputDevice"])
    for dev in devices:
        if speakers["name"] in dev["name"]:
            return dev
    return devices[0]


class LoopbackRecorder:
    """ループバックデバイスから int16 フレームを読み出すコンテキストマネージャ。"""

    def __init__(self, hint: str | None = None, chunk: int = CHUNK):
        self._hint = hint
        self._chunk = chunk
        self._pa = None
        self._stream = None
        self.device: dict | None = None
        self.rate: int = 0
        self.channels: int = 0

    def __enter__(self) -> "LoopbackRecorder":
        pa_mod = require_pyaudio()
        self._pa = pa_mod.PyAudio()
        self.device = find_loopback_device(self._pa, self._hint)
        self.rate = int(self.device["defaultSampleRate"])
        self.channels = int(self.device["maxInputChannels"])
        self._stream = self._pa.open(
            format=pa_mod.paInt16,
            channels=self.channels,
            rate=self.rate,
            input=True,
            input_device_index=int(self.device["index"]),
            frames_per_buffer=self._chunk,
        )
        return self

    def __exit__(self, *exc) -> None:
        if self._stream is not None:
            self._stream.stop_stream()
            self._stream.close()
        if self._pa is not None:
            self._pa.terminate()

    def frames(self):
        """(chunk, channels) の int16 配列を yield し続ける。"""
        while True:
            raw = self._stream.read(self._chunk, exception_on_overflow=False)
            yield np.frombuffer(raw, dtype=np.int16).reshape(-1, self.channels)


def to_mono_float(frame: np.ndarray) -> np.ndarray:
    """int16 の多チャンネルフレームを float32 モノラル（-1.0〜1.0）にする。"""
    return (frame.astype(np.float32) / 32768.0).mean(axis=1)


def resample_to_16k(audio: np.ndarray, rate: int) -> np.ndarray:
    """Whisper が要求する 16 kHz へリサンプルする。"""
    if rate == 16000:
        return audio.astype(np.float32, copy=False)
    try:
        import soxr
    except ImportError:  # pragma: no cover - 実行環境依存
        raise LoopbackError("リサンプルに soxr が必要です: pip install soxr") from None
    return soxr.resample(audio, rate, 16000, quality="HQ").astype(np.float32)
