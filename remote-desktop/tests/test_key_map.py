"""キーマップの検証。pynput 本体は使わず、同じ形の偽モジュールで確かめる。"""

import types

import pytest

from rdcontrol.input_control import build_key_map


class FakeKey:
    """pynput.keyboard.Key と同じ属性名を持つスタブ。"""

    def __init__(self, name: str) -> None:
        self.name = name

    def __repr__(self) -> str:  # pragma: no cover - 失敗時の表示用
        return f"Key.{self.name}"


def fake_keyboard_module() -> types.SimpleNamespace:
    names = [
        "enter", "backspace", "tab", "esc", "delete", "insert", "home", "end",
        "page_up", "page_down", "up", "down", "left", "right", "space",
        "shift", "ctrl", "alt", "cmd", "caps_lock",
        "shift_l", "shift_r", "ctrl_l", "ctrl_r", "alt_l", "alt_r", "cmd_l", "cmd_r",
        "menu", "print_screen",
    ] + [f"f{i}" for i in range(1, 13)]
    key = types.SimpleNamespace(**{name: FakeKey(name) for name in names})
    return types.SimpleNamespace(Key=key)


@pytest.fixture
def key_map():
    return build_key_map(fake_keyboard_module())


@pytest.mark.parametrize(
    "browser_key, expected",
    [
        ("Enter", "enter"),
        ("Backspace", "backspace"),
        ("Escape", "esc"),
        ("ArrowLeft", "left"),
        ("PageDown", "page_down"),
        (" ", "space"),
        ("F5", "f5"),
        ("ContextMenu", "menu"),
    ],
)
def test_named_keys_map_to_pynput_keys(key_map, browser_key, expected):
    assert key_map[browser_key].name == expected


def test_left_and_right_modifiers_are_distinguished(key_map):
    assert key_map["ShiftLeft"].name == "shift_l"
    assert key_map["ShiftRight"].name == "shift_r"
    assert key_map["ControlRight"].name == "ctrl_r"


def test_missing_optional_keys_are_skipped():
    module = fake_keyboard_module()
    del module.Key.menu
    mapping = build_key_map(module)
    assert "ContextMenu" not in mapping
    assert "Enter" in mapping


def test_function_keys_beyond_the_stub_are_not_invented(key_map):
    assert "F20" not in key_map  # スタブは f12 までしか持たない
    assert "F12" in key_map
