"""SegmentBuffer の区切り判定を検証する（Windows 以外でも実行できる）。"""

import numpy as np

from live import SegmentBuffer

RATE = 48000
FRAME = 4800  # 0.1 秒


def level(rms: float) -> np.ndarray:
    """指定した RMS の 0.1 秒フレームを作る。"""
    return np.full(FRAME, rms, dtype=np.float32)


def silent() -> np.ndarray:
    return np.zeros(FRAME, dtype=np.float32)


def loud() -> np.ndarray:
    return level(0.2)


def new_buffer(**kw) -> SegmentBuffer:
    params = dict(
        rate=RATE, threshold=0.005, silence=0.7, min_seconds=2.0, max_seconds=25.0,
        noise_factor=0.0,  # 既定は絶対しきい値のみ。追従は専用のテストで見る
    )
    params.update(kw)
    return SegmentBuffer(**params)


def push_all(buf: SegmentBuffer, frames) -> list[np.ndarray]:
    return [seg for f in frames if (seg := buf.push(f)) is not None]


def test_pause_splits_after_min_seconds():
    buf = new_buffer()
    # 1.5 秒の有音では min_seconds に届かないので、無音が続いても切れない
    assert push_all(buf, [loud()] * 15 + [silent()] * 5) == []
    # 有音を足して 2 秒を超え、無音が 0.7 秒続いた時点で切れる
    segments = push_all(buf, [loud()] * 10 + [silent()] * 7)
    assert len(segments) == 1
    assert len(segments[0]) == (15 + 5 + 10 + 7) * FRAME


def test_silence_only_is_discarded():
    buf = new_buffer()
    # 無音だけなら max_seconds に達しても推論に回さない
    assert push_all(buf, [silent()] * 300) == []
    assert buf.flush() is None


def test_max_seconds_forces_split():
    buf = new_buffer(max_seconds=3.0)
    segments = push_all(buf, [loud()] * 30)
    assert len(segments) == 1
    assert len(segments[0]) == 30 * FRAME


def test_flush_returns_tail():
    buf = new_buffer()
    assert push_all(buf, [loud()] * 5) == []
    tail = buf.flush()
    assert tail is not None and len(tail) == 5 * FRAME
    assert buf.flush() is None  # 二度目は空


def test_silence_counter_resets_on_speech():
    buf = new_buffer()
    # 無音 0.5 秒 → 発話 → 無音 0.5 秒 では区切られない
    assert push_all(buf, [loud()] * 25 + [silent()] * 5 + [loud()] * 2 + [silent()] * 5) == []
    assert push_all(buf, [silent()] * 2)  # ここで累計 0.7 秒に達して区切られる


def test_adaptive_threshold_finds_pauses_under_constant_noise():
    """歓声や BGM が途切れない音声でも発話の切れ目を検出できる。"""
    noise, speech = level(0.05), level(0.5)

    # 絶対しきい値だけでは、暗騒音 0.05 が threshold 0.005 を常に上回るため
    # 「無音」が一度も成立せず、max_seconds まで区切られない
    absolute = new_buffer(max_seconds=100.0)
    assert push_all(absolute, [speech] * 30 + [noise] * 30) == []

    # 暗騒音に追従させると、発話が止んだ 0.7 秒後に区切られる
    adaptive = new_buffer(max_seconds=100.0, noise_factor=2.0)
    segments = push_all(adaptive, [speech] * 30 + [noise] * 30)
    assert len(segments) == 1


def test_adaptive_threshold_still_honors_the_absolute_floor():
    """静かな環境では暗騒音が 0 に近いので、絶対しきい値が下限として効く。"""
    buf = new_buffer(noise_factor=2.0)
    segments = push_all(buf, [loud()] * 30 + [silent()] * 10)
    assert len(segments) == 1


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn()
            print(f"ok  {name}")
    print("\nすべて通過")
