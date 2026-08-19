"""音声の変換と配信のテスト。実際の録音デバイスは使わない。"""

import asyncio

import numpy as np
import pytest

from rdcontrol.audio import AudioUnavailable, TARGET_RATE, convert, resample, to_mono, to_pcm16
from rdcontrol.audio_stream import AudioHub


# --- 変換 -------------------------------------------------------------

def test_stereo_is_mixed_down_to_mono():
    stereo = np.array([1.0, 0.0, 0.5, 0.5], dtype=np.float32)  # L,R,L,R
    assert list(to_mono(stereo, 2)) == [0.5, 0.5]


def test_mono_input_is_left_alone():
    mono = np.array([0.1, 0.2], dtype=np.float32)
    assert list(to_mono(mono, 1)) == pytest.approx([0.1, 0.2])


def test_resampling_halves_the_sample_count():
    samples = np.linspace(-1.0, 1.0, num=480, dtype=np.float32)
    assert resample(samples, 48_000, 24_000).size == 240


def test_resampling_keeps_the_shape_of_the_signal():
    samples = np.linspace(0.0, 1.0, num=100, dtype=np.float32)
    resampled = resample(samples, 48_000, 24_000)
    assert resampled[0] == pytest.approx(0.0, abs=0.02)
    assert resampled[-1] == pytest.approx(1.0, abs=0.02)


def test_matching_rates_skip_resampling():
    samples = np.array([0.5, -0.5], dtype=np.float32)
    assert resample(samples, TARGET_RATE, TARGET_RATE) is samples


def test_samples_become_16bit_little_endian_bytes():
    assert to_pcm16(np.array([0.0, 1.0, -1.0], dtype=np.float32)) == (
        b"\x00\x00" + b"\xff\x7f" + b"\x01\x80"
    )


def test_values_beyond_the_range_are_clipped_instead_of_wrapping():
    # 丸めずに変換すると、大きすぎる値が反対の符号に化けて雑音になる
    assert to_pcm16(np.array([2.0, -2.0], dtype=np.float32)) == b"\xff\x7f" + b"\x01\x80"


def test_conversion_produces_one_sample_per_frame_at_the_target_rate():
    stereo = np.zeros(48_000 * 2, dtype=np.float32)   # 1 秒ぶんのステレオ
    assert len(convert(stereo, 2, 48_000)) == TARGET_RATE * 2   # 16bit なので 2 バイト/標本


# --- 配信 -------------------------------------------------------------

class FakeCapture:
    instances: list["FakeCapture"] = []

    def __init__(self) -> None:
        self.closed = False
        FakeCapture.instances.append(self)

    def read(self) -> bytes:
        return b"chunk"

    def close(self) -> None:
        self.closed = True


@pytest.fixture(autouse=True)
def reset_instances():
    FakeCapture.instances.clear()
    yield


@pytest.mark.asyncio
async def test_every_listener_receives_the_same_audio():
    hub = AudioHub(factory=FakeCapture)
    first = await hub.subscribe()
    second = await hub.subscribe()
    try:
        assert await asyncio.wait_for(first.get(), 2) == b"chunk"
        assert await asyncio.wait_for(second.get(), 2) == b"chunk"
        assert len(FakeCapture.instances) == 1   # 取り込みは 1 本にまとめる
    finally:
        await hub.aclose()


@pytest.mark.asyncio
async def test_capture_stops_when_the_last_listener_leaves():
    hub = AudioHub(factory=FakeCapture)
    first = await hub.subscribe()
    second = await hub.subscribe()
    await hub.unsubscribe(first)
    assert not FakeCapture.instances[0].closed     # まだ聞いている人がいる
    await hub.unsubscribe(second)
    assert FakeCapture.instances[0].closed
    assert hub.listeners == 0


@pytest.mark.asyncio
async def test_an_unavailable_device_is_reported_to_the_caller():
    def broken():
        raise AudioUnavailable("デバイスがありません")

    hub = AudioHub(factory=broken)
    with pytest.raises(AudioUnavailable):
        await hub.subscribe()
    assert hub.listeners == 0


@pytest.mark.asyncio
async def test_a_slow_listener_drops_old_audio_instead_of_stalling():
    hub = AudioHub(factory=FakeCapture)
    queue = await hub.subscribe()
    try:
        # 受け取らずに放置しても、待ち行列は上限で頭打ちになる
        await asyncio.sleep(0.2)
        assert queue.qsize() <= 8
    finally:
        await hub.aclose()
