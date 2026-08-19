"""コマンドラインエントリポイント: ``python -m rdcontrol``"""

from __future__ import annotations

import argparse
import logging
import sys
import webbrowser

from .auth import generate_token
from .capture import CaptureUnavailable, ScreenCapture
from .diagnose import diagnose
from .input_control import InputController, InputUnavailable
from .qr import is_printable, render_qr
from .tailscale import NOT_FOUND_HINT, detect_tailscale_ip
from .config import DEFAULT_FPS, DEFAULT_PORT, DEFAULT_QUALITY, Settings, local_lan_address

BANNER = """
╭──────────────────────────────────────────────────────────────╮
│  rdcontrol — ローカルデスクトップのリモート操作サーバー      │
╰──────────────────────────────────────────────────────────────╯
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m rdcontrol",
        description="このマシンのデスクトップを、ブラウザから閲覧・操作できるようにします。",
    )
    parser.add_argument("--host", default="127.0.0.1",
                        help="listen するアドレス (既定: 127.0.0.1 = このマシンからのみ)")
    parser.add_argument("--tailscale", action="store_true",
                        help="Tailscale のアドレスで待ち受ける(外出先・スマホから使う場合はこれ)")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"ポート (既定: {DEFAULT_PORT})")
    parser.add_argument("--token", default=None,
                        help="アクセストークン (既定: 起動ごとにランダム生成)")
    parser.add_argument("--monitor", type=int, default=1,
                        help="表示するモニタ番号 (既定: 1、0 は全モニタ結合)")
    parser.add_argument("--fps", type=int, default=DEFAULT_FPS, help=f"最大フレームレート (既定: {DEFAULT_FPS})")
    parser.add_argument("--quality", type=int, default=DEFAULT_QUALITY,
                        help=f"JPEG 品質 10-95 (既定: {DEFAULT_QUALITY})")
    parser.add_argument("--scale", type=float, default=1.0,
                        help="送信時の縮小率 0.2-1.0 (既定: 1.0)")
    parser.add_argument("--view-only", action="store_true",
                        help="画面共有のみ。マウス・キーボード操作を受け付けない")
    parser.add_argument("--max-clients", type=int, default=4, help="同時接続数の上限 (既定: 4)")
    parser.add_argument("--ssh-target", default="",
                        help="案内に表示する SSH 接続先 (例: user@host)。既定はこのマシンから自動推定")
    parser.add_argument("--open", action="store_true", help="起動後にブラウザを自動で開く")
    parser.add_argument("--list-monitors", action="store_true", help="モニタ一覧を表示して終了")
    parser.add_argument("--diagnose", action="store_true",
                        help="カーソル位置のずれを実測して表示し終了(操作位置が合わないときに使う)")
    parser.add_argument("--log-level", default="info",
                        choices=["debug", "info", "warning", "error"], help="ログレベル")
    return parser


def print_qr(url: str) -> None:
    """接続 URL の QR コードを表示する。スマホのカメラで読み取れる。"""
    code = render_qr(url, indent="      ")
    if code is None:
        print("      (QR コードを出すには pip install qrcode)")
        return
    if not is_printable(code):
        # 日本語 Windows の既定 cp932 ではブロック文字を出せない
        print("      (QR は表示できません。chcp 65001 で UTF-8 にすると表示されます)")
        return
    print()
    print("      ↓ スマホのカメラで読み取れます")
    print(code)
    print()


def print_startup_notice(settings: Settings) -> None:
    print(BANNER)
    print("  ■ このマシンのブラウザで開く")
    print(f"      {settings.url() if settings.is_loopback else settings.tunnel_url()}")
    print()

    if settings.is_tailscale:
        print("  ■ 外出先・スマホから開く(Tailscale 経由)")
        print(f"      {settings.url()}")
        print_qr(settings.url())
        print("      同じ Tailscale アカウントにログインした端末からのみ到達でき、")
        print("      通信は Tailscale(WireGuard)が暗号化します。")
    elif settings.is_loopback:
        print("  ■ 別の端末から使う(SSH トンネル経由。通信は SSH が暗号化します)")
        print("      1) 操作する側の端末で次を実行し、つないだままにする")
        print(f"         {settings.tunnel_command()}")
        print("         ※ 同梱の tunnel.sh / tunnel.bat でも同じことができます")
        print("      2) その端末のブラウザで次を開く")
        print(f"         {settings.tunnel_url()}")
        print()
        print("      スマホから使う場合は Tailscale を推奨します(--tailscale で起動)。")
    else:
        print("  ■ 同じネットワーク上の端末から開く")
        address = settings.host if settings.host not in ("0.0.0.0", "::", "") else local_lan_address()
        if address:
            print(f"      {settings.url_on(address)}")
            print_qr(settings.url_on(address))
        else:
            print("      http://<この PC の LAN アドレス>:"
                  f"{settings.port}/?token={settings.token}")
            print("      (Windows は ipconfig、macOS / Linux は ip addr で確認できます)")
    print()

    print(f"  モニタ: {settings.monitor}   FPS: {settings.fps}   画質: {settings.quality}   "
          f"操作: {'閲覧のみ (--view-only)' if settings.view_only else '有効'}")
    print(f"  トークン: {settings.token}")
    print()
    if settings.is_public:
        print("  ⚠  暗号化されないまま、ループバック以外のアドレスで待ち受けています。")
        print("     同一ネットワーク上の誰でも接続を試せる状態です。信頼できる LAN 内に限ってください。")
        print("     外出先から使う場合は --tailscale を使ってください(ポート開放も不要です)。")
        print()
    print("  終了するには Ctrl+C を押してください。")
    print()


def settings_from_args(args: argparse.Namespace) -> Settings:
    """コマンドライン引数を Settings に変換する(値は許容範囲へ丸める)。"""
    return Settings(
        host=args.host,
        port=args.port,
        token=args.token or generate_token(),
        monitor=args.monitor,
        fps=max(1, min(30, args.fps)),
        quality=max(10, min(95, args.quality)),
        scale=max(0.2, min(1.0, args.scale)),
        view_only=args.view_only,
        max_clients=max(1, args.max_clients),
        ssh_target=args.ssh_target,
    )


def resolve_tailscale_host(detect=detect_tailscale_ip) -> str | None:
    """--tailscale: 待ち受けるべき Tailscale アドレスを返す。見つからなければ案内を出す。"""
    address = detect()
    if address is None:
        print(f"エラー: {NOT_FOUND_HINT}", file=sys.stderr)
    return address


def run_diagnose(monitor: int) -> int:
    """--diagnose: 座標のずれを実測して表示する。"""
    try:
        capture = ScreenCapture(monitor=monitor)
        controller = InputController()
    except (CaptureUnavailable, InputUnavailable) as exc:
        print(f"エラー: {exc}", file=sys.stderr)
        return 1
    try:
        print("カーソルを数か所へ動かして測定します(数秒かかります)...\n")
        for line in diagnose(capture, controller):
            print(line)
    finally:
        capture.close()
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
    )

    if args.list_monitors:
        try:
            capture = ScreenCapture(monitor=1)
        except CaptureUnavailable as exc:
            print(f"エラー: {exc}", file=sys.stderr)
            return 1
        for monitor in capture.monitors():
            role = " (全モニタ結合)" if monitor.index == 0 else ""
            print(f"  {monitor.index}: {monitor.width}x{monitor.height} "
                  f"@ ({monitor.left},{monitor.top}){role}")
        capture.close()
        return 0

    if args.diagnose:
        return run_diagnose(args.monitor)

    if args.tailscale:
        address = resolve_tailscale_host()
        if address is None:
            return 1
        # Tailscale のアドレスにだけ bind する。0.0.0.0 と違い、同じ Wi-Fi に
        # いるだけの無関係な端末からは見えない。
        args.host = address

    settings = settings_from_args(args)

    try:
        import uvicorn

        from .app import create_app

        app = create_app(settings)
    except CaptureUnavailable as exc:
        print(f"エラー: {exc}", file=sys.stderr)
        return 1

    print_startup_notice(settings)
    if args.open:
        webbrowser.open(settings.url())

    uvicorn.run(app, host=settings.host, port=settings.port, log_level=args.log_level,
                ws_max_size=2 * 1024 * 1024)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
