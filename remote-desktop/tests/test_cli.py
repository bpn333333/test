"""CLI と、SSH トンネル案内の組み立てに関するテスト。"""

import shutil
import subprocess
from pathlib import Path

import pytest

from rdcontrol.__main__ import build_parser, print_startup_notice, settings_from_args
from rdcontrol.config import Settings, local_ssh_target, ssh_tunnel_command


def parse(*argv) -> Settings:
    return settings_from_args(build_parser().parse_args(list(argv)))


def test_defaults_listen_on_loopback_only():
    settings = parse()
    assert settings.host == "127.0.0.1"
    assert not settings.is_public
    assert len(settings.token) >= 30


def test_out_of_range_values_are_clamped():
    settings = parse("--fps", "999", "--quality", "1", "--scale", "5", "--max-clients", "0")
    assert settings.fps == 30
    assert settings.quality == 10
    assert settings.scale == 1.0
    assert settings.max_clients == 1


def test_explicit_host_is_reported_as_public():
    assert parse("--host", "0.0.0.0").is_public


def test_tunnel_command_forwards_the_configured_port():
    command = ssh_tunnel_command(9000, "nori@desk.local")
    assert "-L 9000:127.0.0.1:9000" in command
    assert command.endswith("nori@desk.local")
    # 手元のポートが埋まっていたら黙って続行しない
    assert "ExitOnForwardFailure=yes" in command
    # 無言で切られた接続を検知する
    assert "ServerAliveInterval=30" in command


def test_tunnel_url_points_at_the_local_end_of_the_tunnel():
    settings = Settings(token="abc", port=9000)
    assert settings.tunnel_url() == "http://127.0.0.1:9000/?token=abc"


def test_ssh_target_can_be_overridden_and_is_otherwise_guessed():
    assert parse("--ssh-target", "nori@desk.local").tunnel_command().endswith("nori@desk.local")
    guessed = parse().tunnel_command()
    assert guessed.endswith(local_ssh_target())
    assert "@" in local_ssh_target()


def test_startup_notice_shows_both_the_tunnel_command_and_the_url(capsys):
    settings = parse("--token", "SAMPLE", "--ssh-target", "nori@desk.local")
    print_startup_notice(settings)
    output = capsys.readouterr().out
    assert settings.tunnel_command() in output
    assert "http://127.0.0.1:8765/?token=SAMPLE" in output
    assert "SSH トンネル" in output


def test_startup_notice_warns_when_listening_beyond_loopback(capsys):
    print_startup_notice(parse("--host", "0.0.0.0", "--token", "SAMPLE"))
    output = capsys.readouterr().out
    assert "⚠" in output
    assert "暗号化されない" in output


def test_startup_notice_is_quiet_about_exposure_on_loopback(capsys):
    print_startup_notice(parse("--token", "SAMPLE"))
    assert "⚠" not in capsys.readouterr().out


# --- tunnel.sh(接続する側で使うスクリプト)-------------------------------

TUNNEL_SH = Path(__file__).resolve().parents[1] / "tunnel.sh"


def run_tunnel(*argv) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["bash", str(TUNNEL_SH), *argv], capture_output=True, text=True, timeout=10
    )


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash が無い環境")
def test_tunnel_script_requires_a_target():
    result = run_tunnel()
    assert result.returncode == 2
    assert "使い方" in result.stderr


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash が無い環境")
@pytest.mark.parametrize("port", ["abc", "0", "70000"])
def test_tunnel_script_rejects_bad_ports(port):
    result = run_tunnel("user@host", port)
    assert result.returncode == 2
    assert "ポート番号が不正です" in result.stderr


# --- 経路ごとの案内表示 -----------------------------------------------------

def test_tailscale_notice_shows_the_reachable_url_without_a_warning(capsys):
    print_startup_notice(parse("--host", "100.101.102.103", "--token", "SAMPLE"))
    output = capsys.readouterr().out
    assert "http://100.101.102.103:8765/?token=SAMPLE" in output
    assert "Tailscale" in output
    assert "⚠" not in output          # Tailscale 経由は暗号化されるので警告しない
    assert "ssh -N" not in output     # トンネルの案内は不要


def test_plain_lan_notice_keeps_the_warning_and_points_at_tailscale(capsys):
    print_startup_notice(parse("--host", "0.0.0.0", "--token", "SAMPLE"))
    output = capsys.readouterr().out
    assert "⚠" in output
    assert "--tailscale" in output
