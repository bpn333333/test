"""コマンドラインエントリポイント: ``python -m rdcontrol``"""

from __future__ import annotations

import argparse
import logging
import sys
import webbrowser

from .auth import generate_token
from .capture import CaptureUnavailable, ScreenCapture
from .config import DEFAULT_FPS, DEFAULT_PORT, DEFAULT_QUALITY, Settings

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
    parser.add_argument("--log-level", default="info",
                        choices=["debug", "info", "warning", "error"], help="ログレベル")
    return parser


def print_startup_notice(settings: Settings) -> None:
    print(BANNER)
    print("  ■ このマシンのブラウザで開く")
    print(f"      {settings.url()}")
    print()
    print("  ■ 別の端末から使う(SSH トンネル経由。通信は SSH が暗号化します)")
    print("      1) 操作する側の端末で次を実行し、つないだままにする")
    print(f"         {settings.tunnel_command()}")
    print("         ※ 同梱の tunnel.sh / tunnel.bat でも同じことができます")
    print("      2) その端末のブラウザで次を開く")
    print(f"         {settings.tunnel_url()}")
    print()
    print(f"  モニタ: {settings.monitor}   FPS: {settings.fps}   画質: {settings.quality}   "
          f"操作: {'閲覧のみ (--view-only)' if settings.view_only else '有効'}")
    print(f"  トークン: {settings.token}")
    print()
    if settings.is_public:
        print("  ⚠  ループバック以外のアドレスで待ち受けています。")
        print("     同一ネットワーク上の誰でも接続を試せる状態で、通信は暗号化されません。")
        print("     インターネット越しに使うなら --host は既定のまま、上の SSH トンネルを使ってください。")
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
