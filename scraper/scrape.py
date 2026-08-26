#!/usr/bin/env python3
"""HP(Webページ)にアクセスして、画像の保存とテキストの収集を行うツール。

使い方の例:
    python3 scrape.py --url https://example.com --out ./output
    python3 scrape.py --url https://example.com --select "見出し=h1,h2" --select "本文=article p"
    python3 scrape.py --url-file urls.txt --regex "\\d{3}-\\d{4}-\\d{4}" --no-images

取得結果:
    output/
      images/          … ダウンロードした画像
      results.json     … 収集したテキスト・画像の一覧(全情報)
      texts.csv        … 収集したテキスト(表計算ソフト用)
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import mimetypes
import os
import re
import sys
import time
import urllib.robotparser
from dataclasses import dataclass, field
from urllib.parse import urljoin, urlparse, unquote

import requests
from bs4 import BeautifulSoup

DEFAULT_UA = (
    "Mozilla/5.0 (compatible; SimpleScraper/1.0; "
    "+https://github.com/bpn333333/test)"
)

# 画像URLが入りうる属性(遅延読み込み対応)
IMG_ATTRS = ("src", "data-src", "data-original", "data-lazy-src", "data-echo")
SRCSET_ATTRS = ("srcset", "data-srcset")

# style="background-image:url(...)" から拾うための正規表現
BG_IMAGE_RE = re.compile(r"url\(\s*['\"]?(?P<url>[^'\")]+)['\"]?\s*\)", re.I)

SAFE_NAME_RE = re.compile(r"[^A-Za-z0-9._\-ぁ-んァ-ヶ一-龥]+")


# --------------------------------------------------------------------------
# データ構造
# --------------------------------------------------------------------------
@dataclass
class PageResult:
    url: str
    status: int | None = None
    title: str = ""
    texts: dict[str, list[str]] = field(default_factory=dict)
    matches: list[str] = field(default_factory=list)
    images: list[dict] = field(default_factory=list)
    error: str = ""


# --------------------------------------------------------------------------
# 補助関数
# --------------------------------------------------------------------------
def log(msg: str, quiet: bool = False) -> None:
    if not quiet:
        print(msg, file=sys.stderr, flush=True)


def make_session(user_agent: str) -> requests.Session:
    s = requests.Session()
    s.headers.update({
        "User-Agent": user_agent,
        "Accept-Language": "ja,en;q=0.8",
    })
    return s


def fetch(session: requests.Session, url: str, timeout: float,
          retries: int = 3, stream: bool = False) -> requests.Response:
    """指数バックオフ付きでGETする。"""
    last_exc: Exception | None = None
    for attempt in range(retries):
        try:
            res = session.get(url, timeout=timeout, stream=stream)
            # 5xx はリトライする価値がある
            if res.status_code >= 500 and attempt < retries - 1:
                raise requests.HTTPError(f"status {res.status_code}")
            return res
        except Exception as exc:  # noqa: BLE001 - ネットワーク例外はまとめて扱う
            last_exc = exc
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
    raise last_exc  # type: ignore[misc]


class RobotsChecker:
    """robots.txt を見て取得してよいURLか判定する(ドメインごとにキャッシュ)。"""

    def __init__(self, user_agent: str, enabled: bool = True):
        self.user_agent = user_agent
        self.enabled = enabled
        self._cache: dict[str, urllib.robotparser.RobotFileParser | None] = {}

    def allowed(self, url: str) -> bool:
        if not self.enabled:
            return True
        parts = urlparse(url)
        root = f"{parts.scheme}://{parts.netloc}"
        if root not in self._cache:
            rp = urllib.robotparser.RobotFileParser()
            rp.set_url(urljoin(root, "/robots.txt"))
            try:
                rp.read()
            except Exception:  # robots.txt が読めない場合は許可扱い
                rp = None
            self._cache[root] = rp
        rp = self._cache[root]
        if rp is None:
            return True
        return rp.can_fetch(self.user_agent, url)


def parse_selectors(raw: list[str]) -> list[tuple[str, str]]:
    """--select の指定を (ラベル, CSSセレクタ) に分解する。

    "見出し=h1,h2" → ("見出し", "h1,h2")
    "article p"    → ("article p", "article p")
    """
    out: list[tuple[str, str]] = []
    for item in raw:
        if "=" in item:
            label, sel = item.split("=", 1)
            label, sel = label.strip(), sel.strip()
        else:
            label = sel = item.strip()
        if sel:
            out.append((label, sel))
    return out


def safe_filename(name: str, fallback: str = "image") -> str:
    name = unquote(name).strip()
    name = SAFE_NAME_RE.sub("_", name).strip("._")
    if not name:
        name = fallback
    return name[:80]


def guess_extension(url: str, content_type: str) -> str:
    ext = os.path.splitext(urlparse(url).path)[1].lower()
    if ext and len(ext) <= 5 and re.fullmatch(r"\.[a-z0-9]+", ext):
        return ext
    ct = (content_type or "").split(";")[0].strip()
    return mimetypes.guess_extension(ct) or ".img"


# --------------------------------------------------------------------------
# 抽出処理
# --------------------------------------------------------------------------
def collect_image_urls(soup: BeautifulSoup, base_url: str,
                       include_background: bool = True) -> list[str]:
    """ページ内の画像URLを重複なしで集める。"""
    urls: list[str] = []
    seen: set[str] = set()

    def add(raw: str | None) -> None:
        if not raw:
            return
        raw = raw.strip()
        if not raw or raw.startswith("data:") or raw.startswith("javascript:"):
            return
        absolute = urljoin(base_url, raw)
        if urlparse(absolute).scheme not in ("http", "https"):
            return
        if absolute not in seen:
            seen.add(absolute)
            urls.append(absolute)

    for tag in soup.find_all(["img", "source"]):
        for attr in IMG_ATTRS:
            add(tag.get(attr))
        for attr in SRCSET_ATTRS:
            srcset = tag.get(attr)
            if srcset:
                # "a.jpg 1x, b.jpg 2x" の形式
                for candidate in srcset.split(","):
                    add(candidate.strip().split(" ")[0])

    # <link rel="...icon"> や OGP 画像
    for tag in soup.find_all("link", rel=True):
        if any("icon" in r.lower() for r in tag.get("rel", [])):
            add(tag.get("href"))
    for tag in soup.find_all("meta", property=True):
        if tag.get("property", "").lower() in ("og:image", "twitter:image"):
            add(tag.get("content"))

    if include_background:
        for tag in soup.find_all(style=True):
            for m in BG_IMAGE_RE.finditer(tag["style"]):
                add(m.group("url"))

    return urls


def extract_texts(soup: BeautifulSoup,
                  selectors: list[tuple[str, str]]) -> dict[str, list[str]]:
    """CSSセレクタで指定したテキストを収集する。"""
    result: dict[str, list[str]] = {}
    for label, sel in selectors:
        try:
            nodes = soup.select(sel)
        except Exception as exc:  # 不正なセレクタ
            result[label] = [f"[セレクタエラー: {exc}]"]
            continue
        values = []
        for node in nodes:
            text = node.get_text(" ", strip=True)
            if text:
                values.append(text)
        result[label] = values
    return result


def extract_matches(page_text: str, patterns: list[str],
                    keywords: list[str]) -> list[str]:
    """正規表現・キーワードでページ全体のテキストから抜き出す。"""
    found: list[str] = []
    for pat in patterns:
        try:
            for m in re.finditer(pat, page_text):
                found.append(m.group(0))
        except re.error as exc:
            found.append(f"[正規表現エラー {pat}: {exc}]")
    for kw in keywords:
        # キーワードを含む行を丸ごと拾う
        for line in page_text.splitlines():
            if kw in line and line.strip():
                found.append(line.strip())
    # 重複を除きつつ順序を保つ
    return list(dict.fromkeys(found))


# --------------------------------------------------------------------------
# 画像ダウンロード
# --------------------------------------------------------------------------
def download_images(session: requests.Session, urls: list[str], out_dir: str,
                    *, min_bytes: int, max_images: int, delay: float,
                    timeout: float, allowed_ext: list[str] | None,
                    seen_hashes: set[str], quiet: bool) -> list[dict]:
    saved: list[dict] = []
    for url in urls:
        if max_images and len(saved) >= max_images:
            log(f"  画像は上限 {max_images} 件に達したので打ち切ります", quiet)
            break
        try:
            res = fetch(session, url, timeout, stream=True)
            if res.status_code != 200:
                log(f"  × {url} (status {res.status_code})", quiet)
                continue
            content_type = res.headers.get("Content-Type", "")
            data = res.content
        except Exception as exc:  # noqa: BLE001
            log(f"  × {url} ({exc})", quiet)
            continue

        if len(data) < min_bytes:
            log(f"  - スキップ(小さすぎ {len(data)}B): {url}", quiet)
            continue

        ext = guess_extension(url, content_type)
        if allowed_ext and ext.lstrip(".").lower() not in allowed_ext:
            log(f"  - スキップ(拡張子 {ext}): {url}", quiet)
            continue
        if not content_type.startswith("image/") and ext == ".img":
            log(f"  - スキップ(画像ではない {content_type}): {url}", quiet)
            continue

        digest = hashlib.sha1(data).hexdigest()
        if digest in seen_hashes:
            log(f"  - スキップ(内容が重複): {url}", quiet)
            continue
        seen_hashes.add(digest)

        os.makedirs(out_dir, exist_ok=True)
        base = safe_filename(os.path.splitext(os.path.basename(urlparse(url).path))[0])
        filename = f"{base}_{digest[:8]}{ext}"
        path = os.path.join(out_dir, filename)
        with open(path, "wb") as fp:
            fp.write(data)
        saved.append({
            "url": url,
            "file": os.path.relpath(path),
            "bytes": len(data),
            "content_type": content_type,
        })
        log(f"  ✓ {filename} ({len(data):,}B)", quiet)
        if delay:
            time.sleep(delay)
    return saved


# --------------------------------------------------------------------------
# 1ページの処理
# --------------------------------------------------------------------------
def scrape_page(session: requests.Session, url: str, args,
                selectors: list[tuple[str, str]], robots: RobotsChecker,
                images_root: str, seen_hashes: set[str],
                multi: bool) -> PageResult:
    result = PageResult(url=url)
    log(f"\n[取得] {url}", args.quiet)

    if not robots.allowed(url):
        result.error = "robots.txt により禁止されています(--ignore-robots で無視できます)"
        log(f"  ! {result.error}", args.quiet)
        return result

    try:
        res = fetch(session, url, args.timeout)
    except Exception as exc:  # noqa: BLE001
        result.error = str(exc)
        log(f"  ! 取得失敗: {exc}", args.quiet)
        return result

    result.status = res.status_code
    if res.status_code != 200:
        result.error = f"HTTP {res.status_code}"
        log(f"  ! {result.error}", args.quiet)
        return result

    res.encoding = res.apparent_encoding or res.encoding
    soup = BeautifulSoup(res.text, "html.parser")
    result.title = soup.title.get_text(strip=True) if soup.title else ""

    # --- テキスト収集 ---
    if selectors:
        result.texts = extract_texts(soup, selectors)
        for label, values in result.texts.items():
            log(f"  テキスト[{label}]: {len(values)} 件", args.quiet)
    if args.regex or args.contains:
        for junk in soup(["script", "style", "noscript"]):
            junk.decompose()
        page_text = soup.get_text("\n", strip=True)
        result.matches = extract_matches(page_text, args.regex, args.contains)
        log(f"  パターン一致: {len(result.matches)} 件", args.quiet)

    # --- 画像保存 ---
    if not args.no_images:
        img_urls = collect_image_urls(soup, res.url,
                                      include_background=not args.no_background)
        log(f"  画像候補: {len(img_urls)} 件", args.quiet)
        sub = images_root
        if multi:
            host = safe_filename(urlparse(url).netloc)
            path_part = safe_filename(urlparse(url).path, fallback="index")
            sub = os.path.join(images_root, f"{host}_{path_part}")
        result.images = download_images(
            session, img_urls, sub,
            min_bytes=args.min_bytes, max_images=args.max_images,
            delay=args.image_delay, timeout=args.timeout,
            allowed_ext=args.ext, seen_hashes=seen_hashes, quiet=args.quiet,
        )
    return result


# --------------------------------------------------------------------------
# 出力
# --------------------------------------------------------------------------
def write_outputs(results: list[PageResult], out_dir: str, quiet: bool) -> None:
    os.makedirs(out_dir, exist_ok=True)

    json_path = os.path.join(out_dir, "results.json")
    with open(json_path, "w", encoding="utf-8") as fp:
        json.dump([r.__dict__ for r in results], fp, ensure_ascii=False, indent=2)

    csv_path = os.path.join(out_dir, "texts.csv")
    with open(csv_path, "w", encoding="utf-8-sig", newline="") as fp:
        writer = csv.writer(fp)
        writer.writerow(["URL", "ページタイトル", "項目", "テキスト"])
        for r in results:
            for label, values in r.texts.items():
                for v in values:
                    writer.writerow([r.url, r.title, label, v])
            for m in r.matches:
                writer.writerow([r.url, r.title, "パターン一致", m])

    images_csv = os.path.join(out_dir, "images.csv")
    with open(images_csv, "w", encoding="utf-8-sig", newline="") as fp:
        writer = csv.writer(fp)
        writer.writerow(["ページURL", "画像URL", "保存先", "バイト数"])
        for r in results:
            for img in r.images:
                writer.writerow([r.url, img["url"], img["file"], img["bytes"]])

    log(f"\n出力: {json_path}\n      {csv_path}\n      {images_csv}", quiet)


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Webページの画像を保存し、指定したテキストを収集します。",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "例:\n"
            "  python3 scrape.py --url https://example.com\n"
            "  python3 scrape.py --url https://example.com \\\n"
            "      --select \"見出し=h1,h2\" --select \"本文=article p\"\n"
            "  python3 scrape.py --url-file urls.txt --regex \"[\\w.+-]+@[\\w-]+\\.[\\w.]+\"\n"
        ),
    )
    p.add_argument("--url", action="append", default=[], help="対象URL(複数指定可)")
    p.add_argument("--url-file", help="URLを1行ずつ書いたテキストファイル")
    p.add_argument("--out", default="./output", help="出力先ディレクトリ(既定: ./output)")

    g = p.add_argument_group("テキスト収集")
    g.add_argument("--select", action="append", default=[],
                   help='CSSセレクタ。"ラベル=セレクタ" 形式も可(複数指定可)')
    g.add_argument("--regex", action="append", default=[],
                   help="ページ全文から抜き出す正規表現(複数指定可)")
    g.add_argument("--contains", action="append", default=[],
                   help="この文字列を含む行を収集(複数指定可)")

    g = p.add_argument_group("画像保存")
    g.add_argument("--no-images", action="store_true", help="画像を保存しない")
    g.add_argument("--no-background", action="store_true",
                   help="CSS background-image の画像を対象にしない")
    g.add_argument("--ext", help="保存する拡張子をカンマ区切りで限定 例: jpg,png,webp")
    g.add_argument("--min-bytes", type=int, default=1024,
                   help="これより小さい画像は保存しない(既定: 1024)")
    g.add_argument("--max-images", type=int, default=0,
                   help="1ページあたりの保存上限(0で無制限)")
    g.add_argument("--image-delay", type=float, default=0.2,
                   help="画像取得の間隔秒(既定: 0.2)")

    g = p.add_argument_group("アクセス制御")
    g.add_argument("--delay", type=float, default=1.0,
                   help="ページ間の待機秒(既定: 1.0)")
    g.add_argument("--timeout", type=float, default=20.0, help="タイムアウト秒(既定: 20)")
    g.add_argument("--user-agent", default=DEFAULT_UA, help="User-Agent")
    g.add_argument("--ignore-robots", action="store_true",
                   help="robots.txt を無視する(権限のあるサイトのみで使用)")
    p.add_argument("--quiet", action="store_true", help="進捗を表示しない")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    urls: list[str] = list(args.url)
    if args.url_file:
        with open(args.url_file, encoding="utf-8") as fp:
            urls += [line.strip() for line in fp
                     if line.strip() and not line.startswith("#")]
    urls = list(dict.fromkeys(urls))
    if not urls:
        print("エラー: --url か --url-file でURLを指定してください。", file=sys.stderr)
        return 2
    for u in urls:
        if urlparse(u).scheme not in ("http", "https"):
            print(f"エラー: 対応していないURLです: {u}", file=sys.stderr)
            return 2

    args.ext = ([e.strip().lstrip(".").lower() for e in args.ext.split(",")]
                if args.ext else None)

    selectors = parse_selectors(args.select)
    session = make_session(args.user_agent)
    robots = RobotsChecker(args.user_agent, enabled=not args.ignore_robots)
    images_root = os.path.join(args.out, "images")
    seen_hashes: set[str] = set()
    multi = len(urls) > 1

    results: list[PageResult] = []
    for i, url in enumerate(urls):
        results.append(scrape_page(session, url, args, selectors, robots,
                                   images_root, seen_hashes, multi))
        if args.delay and i < len(urls) - 1:
            time.sleep(args.delay)

    write_outputs(results, args.out, args.quiet)

    n_img = sum(len(r.images) for r in results)
    n_txt = sum(sum(len(v) for v in r.texts.values()) + len(r.matches) for r in results)
    n_err = sum(1 for r in results if r.error)
    log(f"\n完了: ページ {len(results)} 件 / 画像 {n_img} 件 / テキスト {n_txt} 件"
        f"{f' / 失敗 {n_err} 件' if n_err else ''}", args.quiet)
    return 1 if n_err == len(results) else 0


if __name__ == "__main__":
    sys.exit(main())
