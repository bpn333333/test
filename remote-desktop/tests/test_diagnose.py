"""座標診断のテスト。実デバイスの代わりに、ずれ方を模した偽物を使う。"""

import pytest

from rdcontrol.capture import MonitorInfo
from rdcontrol.diagnose import diagnose


class StubCapture:
    def __init__(self, monitor: MonitorInfo) -> None:
        self._monitor = monitor

    def current_monitor(self) -> MonitorInfo:
        return self._monitor


class StubController:
    """指示した座標に対して、係数 factor 倍の位置にしか動かないコントローラ。

    factor=1.0 が正常。0.667 は Windows の表示スケーリング 150% 相当。
    """

    def __init__(self, factor: float = 1.0, offset: int = 0) -> None:
        self.factor = factor
        self.offset = offset
        self._position = (0, 0)
        self.moves: list[tuple[int, int]] = []

    def get_position(self) -> tuple[int, int]:
        return self._position

    def move_to(self, x: int, y: int) -> None:
        self.moves.append((x, y))
        self._position = (int(x * self.factor) + self.offset, int(y * self.factor) + self.offset)


@pytest.fixture
def monitor() -> MonitorInfo:
    return MonitorInfo(1, 0, 0, 1920, 1080)


def report(capture, controller) -> str:
    return "\n".join(diagnose(capture, controller, settle=0))


def test_reports_success_when_the_cursor_lands_where_asked(monitor):
    text = report(StubCapture(monitor), StubController(factor=1.0))
    assert "✓ ずれはありません" in text
    assert "✗" not in text


def test_detects_display_scaling_and_names_the_percentage(monitor):
    # 150% スケーリング: 指示した座標の 1/1.5 の位置にしか動かない
    text = report(StubCapture(monitor), StubController(factor=1 / 1.5))
    assert "✗" in text
    assert "150% 相当" in text
    assert "拡大縮小" in text


def test_inconsistent_offsets_are_not_reported_as_scaling(monitor):
    text = report(StubCapture(monitor), StubController(factor=1.0, offset=40))
    assert "✗" in text
    assert "スケーリング" not in text
    assert "--list-monitors" in text


def test_small_rounding_differences_are_tolerated(monitor):
    text = report(StubCapture(monitor), StubController(factor=1.0, offset=1))
    assert "✓ ずれはありません" in text


def test_the_original_cursor_position_is_restored(monitor):
    controller = StubController(factor=1.0)
    controller._position = (777, 333)
    diagnose(StubCapture(monitor), controller, settle=0)
    assert controller.moves[-1] == (777, 333)


def test_monitor_offsets_are_included_in_the_measured_targets(monitor):
    controller = StubController(factor=1.0)
    diagnose(StubCapture(MonitorInfo(2, 1920, 0, 1280, 1024)), controller, settle=0)
    # 左上に指定した測定点が、そのモニタの原点になっている
    assert controller.moves[0] == (1920, 0)
