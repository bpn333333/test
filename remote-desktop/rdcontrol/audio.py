"""PC が再生している音を取り込む。

「今スピーカーから出ている音」を録る仕組み(ループバック録音)は OS ごとに
違うため、環境に応じて実装を切り替える。取り込めない環境でも、画面共有は
そのまま使えるようにする(音声だけ無効になる)。

送信量を抑えるため、モノラル 24kHz 16bit に変換してから送る。
"""

from __future__ import annotations

import logging

logger = logging.getLogger("rdcontrol.audio")

TARGET_RATE = 24_000      # 音声としては十分で、帯域は 384kbps に収まる
CHUNK_MS = 40             # 1 回に送る長さ。短いと途切れにくいが通信回数が増える


class AudioUnavailable(RuntimeError):
    """このマシンの音を取り込めないことを示す。"""


def _numpy():
    try:
        import numpy
    except ImportError as exc:  # pragma: no cover - 依存の有無は環境依存
        raise AudioUnavailable(
            "numpy がインストールされていません。`pip install -r requirements.txt` を実行してください。"
        ) from exc
    return numpy


def to_mono(samples, channels: int):
    """複数チャンネルの並びをモノラルにまとめる。"""
    if channels <= 1:
        return samples
    return samples.reshape(-1, channels).mean(axis=1)


def resample(samples, source_rate: int, target_rate: int = TARGET_RATE):
    """線形補間で標本化周波数を変換する。"""
    numpy = _numpy()
    if source_rate == target_rate or samples.size == 0:
        return samples
    duration = samples.size / source_rate
    target_size = max(1, int(duration * target_rate))
    source_positions = numpy.linspace(0, samples.size - 1, num=samples.size)
    target_positions = numpy.linspace(0, samples.size - 1, num=target_size)
    return numpy.interp(target_positions, source_positions, samples)


def to_pcm16(samples) -> bytes:
    """-1.0〜1.0 の値を 16bit PCM のバイト列にする。"""
    numpy = _numpy()
    clipped = numpy.clip(samples, -1.0, 1.0)
    return (clipped * 32767.0).astype(numpy.int16).tobytes()


def convert(raw, channels: int, source_rate: int) -> bytes:
    """取り込んだ生データを、送信する形式(モノラル 24kHz 16bit)へ変換する。"""
    return to_pcm16(resample(to_mono(raw, channels), source_rate))


class LoopbackCapture:
    """スピーカー出力の取り込み。バックエンドは環境に応じて選ぶ。"""

    def __init__(self) -> None:
        self._backend = None
        self._open()

    # ---- バックエンドの選択 -------------------------------------------

    def _open(self) -> None:
        errors: list[str] = []
        for factory in (_open_wasapi, _open_sounddevice):
            try:
                self._backend = factory()
                logger.info("音声の取り込みを開始しました: %s", self._backend.name)
                return
            except AudioUnavailable as exc:
                errors.append(str(exc))
        raise AudioUnavailable(
            "このマシンの音を取り込めませんでした。\n  " + "\n  ".join(errors)
        )

    @property
    def name(self) -> str:
        return self._backend.name

    def read(self) -> bytes:
        """次のひとかたまりを、変換済みのバイト列で返す。"""
        raw, channels, rate = self._backend.read()
        return convert(raw, channels, rate)

    def close(self) -> None:
        if self._backend is not None:
            self._backend.close()
            self._backend = None


class _WasapiBackend:
    """Windows: WASAPI のループバック録音(pyaudiowpatch)。"""

    name = "WASAPI loopback (Windows)"

    def __init__(self, audio, stream, channels: int, rate: int, frames: int) -> None:
        self._audio = audio
        self._stream = stream
        self._channels = channels
        self._rate = rate
        self._frames = frames

    def read(self):
        numpy = _numpy()
        data = self._stream.read(self._frames, exception_on_overflow=False)
        samples = numpy.frombuffer(data, dtype=numpy.int16).astype(numpy.float32) / 32768.0
        return samples, self._channels, self._rate

    def close(self) -> None:
        try:
            self._stream.stop_stream()
            self._stream.close()
        finally:
            self._audio.terminate()


def _open_wasapi() -> _WasapiBackend:
    try:
        import pyaudiowpatch as pyaudio
    except ImportError as exc:
        raise AudioUnavailable("pyaudiowpatch が無い(Windows 用)") from exc

    try:
        audio = pyaudio.PyAudio()
        device = audio.get_default_wasapi_loopback()
        rate = int(device["defaultSampleRate"])
        channels = int(device["maxInputChannels"])
        frames = max(1, int(rate * CHUNK_MS / 1000))
        stream = audio.open(
            format=pyaudio.paInt16,
            channels=channels,
            rate=rate,
            input=True,
            input_device_index=int(device["index"]),
            frames_per_buffer=frames,
        )
    except Exception as exc:
        raise AudioUnavailable(f"WASAPI ループバックを開けませんでした: {exc}") from exc
    return _WasapiBackend(audio, stream, channels, rate, frames)


class _SoundDeviceBackend:
    """macOS / Linux: 既定の入力デバイス(モニタ用の仮想デバイスを想定)。"""

    name = "sounddevice"

    def __init__(self, stream, channels: int, rate: int, frames: int) -> None:
        self._stream = stream
        self._channels = channels
        self._rate = rate
        self._frames = frames

    def read(self):
        data, _overflowed = self._stream.read(self._frames)
        return data.reshape(-1), self._channels, self._rate

    def close(self) -> None:
        self._stream.stop()
        self._stream.close()


def _open_sounddevice() -> _SoundDeviceBackend:
    try:
        import sounddevice
    except ImportError as exc:
        raise AudioUnavailable("sounddevice が無い") from exc

    try:
        device = sounddevice.query_devices(kind="input")
        rate = int(device["default_samplerate"])
        channels = min(2, int(device["max_input_channels"]))
        frames = max(1, int(rate * CHUNK_MS / 1000))
        stream = sounddevice.InputStream(
            samplerate=rate, channels=channels, dtype="float32", blocksize=frames
        )
        stream.start()
    except Exception as exc:
        raise AudioUnavailable(
            f"入力デバイスを開けませんでした: {exc}"
            "(macOS は BlackHole、Linux は PulseAudio の monitor を既定の入力にしてください)"
        ) from exc
    return _SoundDeviceBackend(stream, channels, rate, frames)
