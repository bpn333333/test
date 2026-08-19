import json

import pytest

from rdcontrol.protocol import MAX_MESSAGE_BYTES, ProtocolError, parse_client_message


def dumps(**kwargs) -> str:
    return json.dumps(kwargs)


def test_mouse_move_is_normalized_and_clamped():
    assert parse_client_message(dumps(t="mouse_move", x=1.4, y=-0.2)) == {
        "t": "mouse_move",
        "x": 1.0,
        "y": 0.0,
    }


def test_mouse_down_defaults_to_left_button():
    message = parse_client_message(dumps(t="mouse_down", x=0.1, y=0.2))
    assert message["button"] == "left"


def test_unknown_button_is_rejected():
    with pytest.raises(ProtocolError):
        parse_client_message(dumps(t="mouse_down", x=0.1, y=0.2, button="thumb"))


def test_scroll_delta_is_truncated_to_notches_and_capped():
    message = parse_client_message(dumps(t="scroll", x=0.5, y=0.5, dx=0, dy=999))
    assert message["dy"] == 30
    assert message["dx"] == 0


def test_config_values_are_clamped_to_supported_range():
    message = parse_client_message(dumps(t="config", quality=500, fps=0, scale=9))
    assert message == {"t": "config", "quality": 95, "fps": 1, "scale": 1.0}


def test_config_omits_fields_that_were_not_sent():
    assert parse_client_message(dumps(t="config", fps=5)) == {"t": "config", "fps": 5}


def test_monitor_must_be_a_small_integer():
    assert parse_client_message(dumps(t="config", monitor=2))["monitor"] == 2
    with pytest.raises(ProtocolError):
        parse_client_message(dumps(t="config", monitor=99))
    with pytest.raises(ProtocolError):
        parse_client_message(dumps(t="config", monitor=1.5))


def test_key_events_keep_key_and_code():
    message = parse_client_message(dumps(t="key_down", key="a", code="KeyA"))
    assert message == {"t": "key_down", "key": "a", "code": "KeyA"}


def test_oversized_message_is_rejected():
    with pytest.raises(ProtocolError):
        parse_client_message(dumps(t="text", text="x" * (MAX_MESSAGE_BYTES + 10)))


def test_long_text_field_is_rejected():
    with pytest.raises(ProtocolError):
        parse_client_message(dumps(t="text", text="x" * 5000))


@pytest.mark.parametrize(
    "raw",
    [
        "not json",
        "[1, 2, 3]",
        '"just a string"',
        json.dumps({"t": "shutdown"}),
        json.dumps({"t": "mouse_move", "x": "0.5", "y": 0.5}),
        json.dumps({"t": "mouse_move", "x": float("inf"), "y": 0.5}),
        json.dumps({"t": "key_down", "key": ["a"], "code": "KeyA"}),
    ],
)
def test_malformed_messages_raise(raw):
    with pytest.raises(ProtocolError):
        parse_client_message(raw)


def test_booleans_are_not_accepted_as_numbers():
    with pytest.raises(ProtocolError):
        parse_client_message(dumps(t="mouse_move", x=True, y=0.5))
