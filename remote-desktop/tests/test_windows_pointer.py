"""Windows でのカーソル移動(SendInput)まわりのテスト。

pynput は Windows での移動に SetCursorPos を使うが、それではマウス移動
イベントが流れずホバーが反応しない。SendInput 用の座標変換と、
Windows 以外での無効化を確認する。
"""

import pytest

from rdcontrol import input_control
from rdcontrol.input_control import ABSOLUTE_RANGE, absolute_mouse_coordinates


def test_corners_map_to_the_ends_of_the_absolute_range():
    assert absolute_mouse_coordinates(0, 0, 0, 0, 1920, 1080) == (0, 0)
    assert absolute_mouse_coordinates(1919, 1079, 0, 0, 1920, 1080) == (
        ABSOLUTE_RANGE,
        ABSOLUTE_RANGE,
    )


def test_centre_maps_to_the_middle_of_the_range():
    x, y = absolute_mouse_coordinates(960, 540, 0, 0, 1920, 1080)
    assert x == pytest.approx(ABSOLUTE_RANGE / 2, abs=40)
    assert y == pytest.approx(ABSOLUTE_RANGE / 2, abs=40)


def test_virtual_desktop_origin_is_subtracted():
    # 左側にサブモニタがある構成では仮想画面の原点が負になる
    assert absolute_mouse_coordinates(-1920, 0, -1920, 0, 3840, 1080)[0] == 0
    assert absolute_mouse_coordinates(0, 0, -1920, 0, 3840, 1080)[0] == pytest.approx(
        ABSOLUTE_RANGE / 2, abs=40
    )


def test_values_outside_the_virtual_desktop_are_clamped():
    assert absolute_mouse_coordinates(-500, -500, 0, 0, 1920, 1080) == (0, 0)
    assert absolute_mouse_coordinates(9999, 9999, 0, 0, 1920, 1080) == (
        ABSOLUTE_RANGE,
        ABSOLUTE_RANGE,
    )


def test_a_degenerate_screen_size_does_not_divide_by_zero():
    assert absolute_mouse_coordinates(0, 0, 0, 0, 1, 1) == (0, 0)


def test_the_windows_path_is_disabled_on_other_platforms(monkeypatch):
    monkeypatch.setattr(input_control.sys, "platform", "linux")
    assert input_control._make_windows_pointer() is None


def test_a_failure_to_initialise_falls_back_instead_of_raising(monkeypatch):
    # Windows を名乗っても ctypes.WinDLL が無ければ静かに諦める
    monkeypatch.setattr(input_control.sys, "platform", "win32")
    assert input_control._make_windows_pointer() is None
