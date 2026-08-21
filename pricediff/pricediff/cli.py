"""コマンドラインインターフェース。

    pricediff run     追跡リストを読んで価格差の一覧を出力する
    pricediff init    設定ファイルと追跡リストの雛形を作る
    pricediff doctor  どのAPIが使える状態かを診断する
"""

from __future__ import annotations

import argparse
import logging
import shutil
import sys
import time
from pathlib import Path
from typing import Optional, Sequence

from . import __version__
from .compare import SORT_KEYS, build_sources, compare_all, filter_rows, sort_rows
from .config import load_config
from .fx import get_fx_rate
from .models import AMAZON, MARKET_LABELS, RAKUTEN, TAOBAO
from .report import render_console, render_summary, write_csv, write_html, write_json
from .sources.http import build_client
from .watchlist import WatchlistError, append_items, load_watchlist, parse_rows

log = logging.getLogger("pricediff")

TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"
DEMO_WATCHLIST = TEMPLATE_DIR / "watchlist.csv"
FORMATS = ("console", "csv", "html", "json")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pricediff",
        description="淘宝 と Amazon.co.jp / 楽天市場 の価格差を、重さと売上ランキング付きで一覧化する",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "例:\n"
            "  pricediff run --demo                 サンプルで動作確認\n"
            "  pricediff init                       雛形を作る\n"
            "  pricediff add < rows.csv             調べた行を貼り付けて追加\n"
            "  pricediff run -w watchlist.csv       一覧を表示\n"
            "  pricediff run -f console,csv,html    ファイルにも書き出す\n"
            "  pricediff run --sort ratio --top 20  差率の高い順に上位20件\n"
            "  pricediff run --cost landed          送料・手数料まで積み上げて比較\n"
        ),
    )
    parser.add_argument("--version", action="version", version=f"pricediff {__version__}")
    sub = parser.add_subparsers(dest="command")

    run = sub.add_parser("run", help="価格差の一覧を出力する")
    run.add_argument("-w", "--watchlist", default="watchlist.csv", help="追跡リスト(CSV/YAML)")
    run.add_argument(
        "--demo",
        action="store_true",
        help="同梱のサンプル(ダミー値)をオフラインで実行する。動作確認用",
    )
    run.add_argument("-c", "--config", default=None, help="設定ファイル(既定: ./config.yaml)")
    run.add_argument(
        "-f",
        "--format",
        default="console",
        help=f"出力形式をカンマ区切りで指定 ({'/'.join(FORMATS)})",
    )
    run.add_argument("-o", "--out-dir", default="out", help="ファイル出力先ディレクトリ")
    run.add_argument("--sort", default=None, choices=SORT_KEYS, help="並べ替え基準(既定: diff)")
    run.add_argument("--top", type=int, default=None, help="上位N件だけ表示")
    run.add_argument("--min-diff", type=float, default=None, help="価格差がこの円未満の行を除外")
    run.add_argument("--max-rank", type=int, default=None, help="ランキングがこの順位より下の行を除外")
    run.add_argument("--fx-rate", type=float, default=None, help="1元あたりの円レートを直接指定")
    run.add_argument(
        "--cost",
        choices=("item", "landed"),
        default=None,
        help="仕入値の取り方。item=商品代のみ(既定) / landed=送料・手数料・税まで積み上げる",
    )
    run.add_argument("--no-cache", action="store_true", help="キャッシュを使わない")
    run.add_argument("--offline", action="store_true", help="APIを一切呼ばず手入力値だけで計算する")
    run.add_argument("--no-links", action="store_true", help="コンソール出力でリンク一覧を省く")
    run.add_argument("-v", "--verbose", action="store_true", help="詳細ログ")

    add = sub.add_parser(
        "add",
        help="ブラウザで調べた行を貼り付けて追跡リストに足す",
        description=(
            "CSV形式の行を標準入力から読み、watchlist.csv に追記します。"
            "1行目がヘッダなら列名に従い、無ければ既定の列順とみなします。"
        ),
    )
    add.add_argument("-w", "--watchlist", default="watchlist.csv", help="追記先(無ければ新規作成)")
    add.add_argument(
        "--update",
        action="store_true",
        help="同じ商品が既にある場合、貼り付けた項目だけを既存行に上書きする",
    )
    add.add_argument("--dry-run", action="store_true", help="書き込まずに結果だけ表示する")

    init = sub.add_parser("init", help="config.yaml と watchlist.csv の雛形を作る")
    init.add_argument("-d", "--dir", default=".", help="作成先ディレクトリ")
    init.add_argument("--force", action="store_true", help="既存ファイルを上書きする")

    doctor = sub.add_parser("doctor", help="APIの設定状況を診断する")
    doctor.add_argument("-c", "--config", default=None, help="設定ファイル")

    return parser


def _setup_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.WARNING,
        format="%(levelname)s %(name)s: %(message)s",
        stream=sys.stderr,
    )


def cmd_add(args: argparse.Namespace) -> int:
    if sys.stdin.isatty():
        print("CSV形式の行を貼り付けて、最後に Ctrl-D を押してください:", file=sys.stderr)
    text = sys.stdin.read()

    try:
        items = parse_rows(text)
    except WatchlistError as exc:
        print(f"エラー: {exc}", file=sys.stderr)
        return 2

    if args.dry_run:
        for item in items:
            print(f"  + {item.key}  {item.name}  淘宝{item.taobao_price_cny}元")
        print(f"\n{len(items)}件を読み取りました(--dry-run のため書き込んでいません)")
        return 0

    try:
        added, skipped = append_items(args.watchlist, items, update=args.update)
    except WatchlistError as exc:
        print(f"エラー: {exc}", file=sys.stderr)
        return 2

    for item in added:
        print(f"  + {item.key}  {item.name}")
    for item in skipped:
        print(f"  = {item.name}(既に同じ商品があります。更新するなら --update)")
    print(f"\n{len(added)}件を {args.watchlist} に反映しました"
          + (f" / {len(skipped)}件は重複のため見送り" if skipped else ""))
    return 0


def cmd_init(args: argparse.Namespace) -> int:
    target = Path(args.dir).expanduser()
    target.mkdir(parents=True, exist_ok=True)
    pairs = [
        (TEMPLATE_DIR / "config.yaml", target / "config.yaml"),
        (TEMPLATE_DIR / "watchlist.csv", target / "watchlist.csv"),
        (TEMPLATE_DIR / "env.example", target / ".env.example"),
    ]
    for source, destination in pairs:
        if not source.is_file():
            log.warning("雛形が見つかりません: %s", source)
            continue
        if destination.exists() and not args.force:
            print(f"skip  {destination}(既に存在。上書きするなら --force)")
            continue
        shutil.copyfile(source, destination)
        print(f"作成  {destination}")
    print("\n次にやること:")
    print("  1. .env.example を .env にコピーしてAPIキーを記入(無くても手入力で動きます)")
    print("  2. watchlist.csv に調べたい商品を追加")
    print("  3. pricediff run -w watchlist.csv -f console,csv,html")
    return 0


def cmd_doctor(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    checks = [
        ("楽天市場 (楽天ウェブサービス)", config.has_rakuten_api(),
         "RAKUTEN_APPLICATION_ID を設定してください: https://webservice.rakuten.co.jp/"),
        ("Amazon.co.jp (PA-API 5.0)", config.has_amazon_api(),
         "AMAZON_ACCESS_KEY / AMAZON_SECRET_KEY / AMAZON_PARTNER_TAG を設定してください"),
        ("淘宝 (淘宝開放平台)", config.has_taobao_api(),
         "TAOBAO_APP_KEY / TAOBAO_APP_SECRET を設定してください(未設定でもCSVの手入力価格で動きます)"),
    ]
    print("APIの設定状況\n")
    for label, ok, hint in checks:
        print(f"  [{'✓' if ok else ' '}] {label}")
        if not ok:
            print(f"      → {hint}")
    print(f"\n為替: {config.get('fx', 'source')} / 既定レート {config.get('fx', 'cny_jpy')}円")
    print(f"キャッシュ: {'有効' if config.get('cache', 'enabled') else '無効'} "
          f"({config.get('cache', 'dir')}, TTL {config.get('cache', 'ttl_seconds')}秒)")
    if not any(ok for _, ok, _ in checks):
        print("\nAPIキーが1つも設定されていません。watchlist.csv に価格を手入力すれば計算はできます。")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    config = load_config(args.config)

    if args.demo:
        args.watchlist = str(DEMO_WATCHLIST)
        args.offline = True
        print("デモ: 同梱サンプル(数値はすべてダミー)をオフラインで表示します", file=sys.stderr)

    if args.no_cache:
        config.set(False, "cache", "enabled")
    for value, path in (
        (args.cost, ("cost", "mode")),
        (args.sort, ("output", "sort")),
        (args.top, ("output", "top")),
        (args.min_diff, ("output", "min_diff_jpy")),
        (args.max_rank, ("output", "max_rank")),
    ):
        if value is not None:
            config.set(value, *path)

    try:
        items = load_watchlist(args.watchlist)
    except WatchlistError as exc:
        print(f"エラー: {exc}", file=sys.stderr)
        print("雛形を作るには: pricediff init", file=sys.stderr)
        return 2

    client = build_client(config)
    fx = get_fx_rate(config, None if args.offline else client, override=args.fx_rate)
    sources = {} if args.offline else build_sources(config, client)

    if sources:
        print(
            "取得元: " + ", ".join(MARKET_LABELS.get(m, m) + " API" for m in sources)
            + (" / それ以外はCSVの手入力値" if len(sources) < 3 else ""),
            file=sys.stderr,
        )
    else:
        print(
            "APIは使わず、CSVの手入力値のみで計算します"
            + ("(--offline 指定)" if args.offline else "(APIキー未設定)"),
            file=sys.stderr,
        )

    def progress(index: int, total: int, item) -> None:
        if sources:
            print(f"\r取得中 {index}/{total}: {item.name[:24]}", end="", file=sys.stderr, flush=True)

    started = time.time()
    rows = compare_all(items, config, fx, sources, progress=progress)
    if sources:
        print("\r" + " " * 60 + "\r", end="", file=sys.stderr)
    elapsed = time.time() - started

    rows = sort_rows(rows, str(config.get("output", "sort", default="diff")))
    rows = filter_rows(
        rows,
        min_diff_jpy=config.get("output", "min_diff_jpy"),
        max_rank=config.get("output", "max_rank"),
        top=config.get("output", "top"),
    )

    formats = [f.strip() for f in args.format.split(",") if f.strip()]
    unknown = [f for f in formats if f not in FORMATS]
    if unknown:
        print(f"エラー: 未知の出力形式 {', '.join(unknown)}", file=sys.stderr)
        return 2

    mode = str(config.get("cost", "mode", default="item"))
    if "console" in formats:
        print(render_console(rows, show_links=not args.no_links, mode=mode))
        print()
        print(render_summary(rows, fx, elapsed))

    out_dir = Path(args.out_dir)
    stamp = time.strftime("%Y%m%d-%H%M")
    meta = {
        "fx_rate": fx.rate,
        "fx_source": fx.source,
        "cost_mode": mode,
        "watchlist": str(args.watchlist),
    }
    if "csv" in formats:
        print(f"CSV : {write_csv(rows, out_dir / f'pricediff-{stamp}.csv')}")
    if "html" in formats:
        print(f"HTML: {write_html(rows, out_dir / f'pricediff-{stamp}.html', fx=fx, mode=mode)}")
    if "json" in formats:
        print(f"JSON: {write_json(rows, out_dir / f'pricediff-{stamp}.json', meta=meta)}")

    # 1件も価格差を出せなかった場合は失敗として扱う(cron等で気づけるように)
    return 0 if any(r.best_diff is not None for r in rows) else 1


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    _setup_logging(getattr(args, "verbose", False))

    if args.command == "add":
        return cmd_add(args)
    if args.command == "init":
        return cmd_init(args)
    if args.command == "doctor":
        return cmd_doctor(args)
    if args.command == "run":
        return cmd_run(args)

    parser.print_help()
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
