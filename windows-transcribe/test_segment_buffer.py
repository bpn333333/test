"""SegmentBuffer の区切り判定を検証する（Windows 以外でも実行できる）。"""

import numpy as np

from live import SegmentBuffer

RATE = 48000
FRAME = 4800  # 0.1 秒


def silent() -> np.ndarray:
    return np.zeros(FRAME, dtype=np.float32)


def loud() -> np.ndarray:
    return np.full(FRAME, 0.2, dtype=np.float32)


def new_buffer(**kw) -> SegmentBuffer:
    params = dict(
        rate=RATE, threshold=0.005, silence=0.7, min_seconds=2.0, max_seconds=25.0
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


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn()
            print(f"ok  {name}")
    print("\nすべて通過")
