"""Tailscale 経由で使うためのアドレス検出のテスト。"""

import pytest

from rdcontrol import tailscale
from rdcontrol.__main__ import resolve_tailscale_host
from rdcontrol.config import Settings
from rdcontrol.tailscale import detect_tailscale_ip, is_tailscale_address, parse_tailscale_ip


@pytest.mark.parametrize(
    "address, expected",
    [
        ("100.64.0.1", True),
        ("100.101.102.103", True),
        ("100.127.255.255", True),
        ("100.63.255.255", False),   # CGNAT 帯の 1 つ手前
        ("100.128.0.0", False),      # CGNAT 帯の 1 つ後ろ
        ("192.168.1.20", False),
        ("127.0.0.1", False),
        ("not-an-address", False),
    ],
)
def test_only_the_tailscale_range_is_recognised(address, expected):
    assert is_tailscale_address(address) is expected


def test_the_tailscale_address_is_picked_out_of_the_command_output():
    assert parse_tailscale_ip("100.101.102.103\nfd7a:115c:a1e0::1\n") == "100.101.102.103"


def test_output_without_a_tailscale_address_yields_nothing():
    assert parse_tailscale_ip("fd7a:115c:a1e0::1\n") is None
    assert parse_tailscale_ip("") is None


def test_detection_uses_the_first_command_that_answers():
    calls = []

    def fake_run(command):
        calls.append(command)
        return "100.90.80.70\n" if command[0] == "tailscale" else None

    assert detect_tailscale_ip(run=fake_run) == "100.90.80.70"
    assert calls == [["tailscale", "ip", "-4"]]


def test_detection_falls_through_to_later_commands(monkeypatch):
    monkeypatch.setattr(tailscale, "_commands", lambda: [["missing"], ["tailscale", "ip", "-4"]])
    outputs = {"missing": None, "tailscale": "100.90.80.70\n"}
    assert detect_tailscale_ip(run=lambda c: outputs[c[0]]) == "100.90.80.70"


def test_detection_returns_none_when_tailscale_is_not_running(monkeypatch):
    monkeypatch.setattr(tailscale, "_address_from_interfaces", lambda: None)
    assert detect_tailscale_ip(run=lambda _: None) is None


def test_a_tailscale_host_is_not_treated_as_an_unencrypted_exposure():
    settings = Settings(token="t", host="100.101.102.103")
    assert settings.is_tailscale
    assert not settings.is_public       # 警告は出さない(Tailscale が暗号化する)
    assert not settings.is_loopback


def test_a_plain_lan_host_is_still_treated_as_an_exposure():
    settings = Settings(token="t", host="0.0.0.0")
    assert not settings.is_tailscale
    assert settings.is_public


def test_missing_tailscale_prints_the_setup_hint(capsys):
    assert resolve_tailscale_host(detect=lambda: None) is None
    assert "Tailscale をインストール" in capsys.readouterr().err


def test_a_found_address_is_returned_without_noise(capsys):
    assert resolve_tailscale_host(detect=lambda: "100.1.2.3") == "100.1.2.3"
    assert capsys.readouterr().err == ""
