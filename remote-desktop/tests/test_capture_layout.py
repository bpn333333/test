"""ディスプレイ構成が変わったときの挙動のテスト。

画面取得ライブラリ(mss)はモニタ一覧を最初に一度読んで覚え込むため、
モニタの電源を入れ切りしても古い値のままになる。その追従を確認する。
実画面は使わず、同じ振る舞いの偽物を差し込んで検証する。
"""

import pytest

from rdcontrol.capture import CaptureUnavailable, ScreenCapture

ONE_DISPLAY = [
    {"left": 0, "top": 0, "width": 1920, "height": 1080},     # 0 = 全体
    {"left": 0, "top": 0, "width": 1920, "height": 1080},     # 1
]
TWO_DISPLAYS = [
    {"left": 0, "top": 0, "width": 3200, "height": 1080},
    {"left": 0, "top": 0, "width": 1920, "height": 1080},
    {"left": 1920, "top": 0, "width": 1280, "height": 1024},
]


class FakeShot:
    def __init__(self, width: int, height: int) -> None:
        self.size = (width, height)
        self.rgb = b"\x00" * (width * height * 3)


class FakeSct:
    """mss と同じく、作られた時点の構成を覚え込む取得口。"""

    def __init__(self, displays: "FakeDisplays") -> None:
        self._displays = displays
        self.monitors = list(displays.layout)   # 作成時のスナップショット
        self.closed = False

    def grab(self, region):
        # 今は存在しないモニタを撮ろうとすると失敗する(実機と同じ)
        if region not in self._displays.layout:
            raise RuntimeError("そのモニタは存在しません")
        return FakeShot(region["width"], region["height"])

    def close(self) -> None:
        self.closed = True


class FakeDisplays:
    def __init__(self, layout) -> None:
        self.layout = [dict(entry) for entry in layout]
        self.created = 0

    def factory(self) -> FakeSct:
        self.created += 1
        return FakeSct(self)

    def set(self, layout) -> None:
        self.layout = [dict(entry) for entry in layout]


@pytest.fixture
def displays() -> FakeDisplays:
    return FakeDisplays(TWO_DISPLAYS)


def make_capture(displays: FakeDisplays, monitor: int = 1) -> ScreenCapture:
    return ScreenCapture(monitor=monitor, factory=displays.factory)


def test_a_stale_monitor_list_is_re_read_on_refresh(displays):
    capture = make_capture(displays)
    assert len(capture.monitors()) == 3

    displays.set(ONE_DISPLAY)
    assert len(capture.monitors()) == 3     # 覚え込んだままなので変わらない
    assert len(capture.refresh()) == 2      # 読み直すと反映される


def test_layout_changes_are_reported_once(displays):
    capture = make_capture(displays)
    displays.set(ONE_DISPLAY)

    changed = capture.poll_layout(now=100.0)
    assert changed is not None
    assert len(changed) == 2
    # 同じ構成のままなら、次からは知らせない
    assert capture.poll_layout(now=200.0) is None


def test_the_layout_is_not_checked_on_every_frame(displays):
    capture = make_capture(displays)
    capture.poll_layout(now=100.0)
    displays.set(ONE_DISPLAY)
    # 間隔を空けずに呼んでも調べ直さない(毎フレーム調べると無駄が大きい)
    assert capture.poll_layout(now=100.5) is None
    assert capture.poll_layout(now=105.0) is not None


def test_losing_the_displayed_monitor_falls_back_instead_of_failing(displays):
    capture = make_capture(displays, monitor=2)     # サブモニタを表示中
    displays.set(ONE_DISPLAY)                       # そのモニタの電源を切った

    changed = capture.poll_layout(now=100.0)
    assert changed is not None
    assert capture.monitor_index == 1               # 残っているモニタへ切り替わる
    assert capture.grab().screen_width == 1920      # そのまま使い続けられる


def test_capture_recovers_when_a_monitor_disappears_between_frames(displays):
    capture = make_capture(displays, monitor=2)
    assert capture.grab().screen_width == 1280

    # 構成が変わったことをまだ知らない状態で撮ろうとする
    displays.set(ONE_DISPLAY)
    frame = capture.grab()
    assert frame.screen_width == 1920
    assert capture.monitor_index == 1


def test_a_resized_monitor_is_captured_at_its_new_size(displays):
    capture = make_capture(displays)
    assert capture.grab().screen_width == 1920

    displays.set([
        {"left": 0, "top": 0, "width": 1280, "height": 720},
        {"left": 0, "top": 0, "width": 1280, "height": 720},
    ])
    capture.poll_layout(now=100.0)
    assert capture.grab().screen_width == 1280


def test_input_coordinates_follow_the_new_layout(displays):
    capture = make_capture(displays, monitor=2)
    assert (capture.current_monitor().left, capture.current_monitor().width) == (1920, 1280)

    displays.set(ONE_DISPLAY)
    capture.poll_layout(now=100.0)
    monitor = capture.current_monitor()
    assert (monitor.left, monitor.width) == (0, 1920)


def test_a_missing_monitor_at_startup_is_reported(displays):
    with pytest.raises(CaptureUnavailable):
        make_capture(displays, monitor=9)
