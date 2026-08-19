"""Tailscale のアドレス検出。

外出先やスマホから使うときの推奨経路。Tailscale は WireGuard で暗号化した
仮想 LAN を張るため、ルーターのポート開放をせずに、同じ Tailscale アカウントに
ログインした端末からだけ接続できる状態を作れる。

このモジュールは「このマシンに割り当てられた Tailscale の IPv4 アドレス」を
突き止めるところまでを担当する。見つかったアドレスにだけ bind することで、
同じ Wi-Fi にいる無関係な端末からは見えないようにできる。
"""

from __future__ import annotations

import ipaddress
import re
import socket
import subprocess
import sys

# Tailscale が使う CGNAT 帯。ここに含まれるアドレスは Tailscale 経由とみなす。
TAILSCALE_NETWORK = ipaddress.ip_network("100.64.0.0/10")

COMMAND_TIMEOUT = 5.0

# tailscale CLI の場所。PATH に無いことが多いので既定のインストール先も見る。
_EXTRA_PATHS = {
    "win32": [
        r"C:\Program Files\Tailscale\tailscale.exe",
        r"C:\Program Files (x86)\Tailscale IPN\tailscale.exe",  # 旧バージョン
    ],
    "darwin": [
        "/Applications/Tailscale.app/Contents/MacOS/Tailscale",
        "/usr/local/bin/tailscale",
        "/opt/homebrew/bin/tailscale",
    ],
    "linux": ["/usr/bin/tailscale", "/usr/local/bin/tailscale"],
}

# OS のネットワーク設定を一覧するコマンド(CLI が見つからないときの保険)
_INTERFACE_COMMANDS = {
    "win32": ["ipconfig"],
    "darwin": ["ifconfig"],
    "linux": ["ip", "-4", "addr"],
}

_IPV4_PATTERN = re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b")

NOT_FOUND_HINT = """Tailscale のアドレスが見つかりませんでした。次を確認してください。
  1. Tailscale をインストールし、ログインしていますか(https://tailscale.com/download)
  2. Tailscale が「接続中」になっていますか
  3. `tailscale ip -4` を実行すると 100.x.x.x が表示されますか
接続する側の端末(スマホなど)にも、同じアカウントで Tailscale を入れてください。"""


def is_tailscale_address(host: str) -> bool:
    """そのアドレスが Tailscale のものか。"""
    try:
        return ipaddress.ip_address(host) in TAILSCALE_NETWORK
    except ValueError:
        return False


def parse_tailscale_ip(output: str) -> str | None:
    """`tailscale ip -4` の出力から IPv4 アドレスを取り出す。

    複数行返ることがあるため、Tailscale の帯に入る最初の行を採用する。
    """
    for line in output.splitlines():
        candidate = line.strip()
        if candidate and is_tailscale_address(candidate):
            return candidate
    return None


def _run(command: list[str]) -> str | None:
    try:
        result = subprocess.run(
            command, capture_output=True, text=True, timeout=COMMAND_TIMEOUT, check=False
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return result.stdout if result.returncode == 0 else None


def _commands() -> list[list[str]]:
    commands = [["tailscale", "ip", "-4"]]
    for path in _EXTRA_PATHS.get(sys.platform, []):
        commands.append([path, "ip", "-4"])
    return commands


def find_tailscale_address(text: str) -> str | None:
    """ネットワーク設定の出力から Tailscale のアドレスを探す。"""
    for candidate in _IPV4_PATTERN.findall(text):
        if is_tailscale_address(candidate):
            return candidate
    return None


def _address_from_interfaces(run=None) -> str | None:
    """CLI が見つからない場合の保険。自ホストの設定からアドレスを探す。"""
    run = _run if run is None else run
    try:
        infos = socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET)
    except OSError:
        infos = []
    for info in infos:
        if is_tailscale_address(info[4][0]):
            return info[4][0]

    command = _INTERFACE_COMMANDS.get(sys.platform)
    if command is None:
        return None
    output = run(command)
    return find_tailscale_address(output) if output else None


def detect_tailscale_ip(run=_run) -> str | None:
    """このマシンの Tailscale IPv4 アドレスを返す。見つからなければ None。"""
    for command in _commands():
        output = run(command)
        if output and (address := parse_tailscale_ip(output)):
            return address
    return _address_from_interfaces(run=run)
