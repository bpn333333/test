#!/usr/bin/env python3
"""
店舗条件コレクタ

風俗ポータルの店舗一覧を巡回し、各店舗ページの本文から
「外国人OK」「キャンセル料無料」などの条件を判定して集計する。

ポータル側の絞り込み条件に存在しない条件（キャンセル料など）を
拾うため、DOM構造ではなく本文テキストのパターン照合で判定する。
サイト改修に強く、プロファイルを足せば他ポータルにも使い回せる。

依存: 標準ライブラリのみ

  python3 collect.py --profile profiles/example.yaml --limit 50
  python3 collect.py --profile profiles/example.yaml --out result.csv
"""

import argparse
import csv
import gzip
import hashlib
import json
import os
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
from dataclasses import dataclass, field, asdict

try:
    import yaml
except ImportError:
    yaml = None

UA = "ShopConditionCollector/1.0 (research; contact: set-your-email)"

# 判定の3値。exclude が include に優先する（否定表現の方が確度が高いため）
YES, NO, UNKNOWN = "yes", "no", "unknown"


# --------------------------------------------------------------------------
# 取得
# --------------------------------------------------------------------------

class Fetcher:
    """レート制限・リトライ・ディスクキャッシュ付きのHTTP取得。"""

    def __init__(self, delay=2.0, cache_dir=None, timeout=20, retries=3):
        self.delay = delay
        self.cache_dir = cache_dir
        self.timeout = timeout
        self.retries = retries
        self._last_request = 0.0
        self.stats = {"fetched": 0, "cached": 0, "failed": 0}
        if cache_dir:
            os.makedirs(cache_dir, exist_ok=True)

    def _cache_path(self, url):
        digest = hashlib.sha256(url.encode()).hexdigest()[:20]
        return os.path.join(self.cache_dir, digest + ".html.gz")

    def _throttle(self):
        elapsed = time.time() - self._last_request
        if elapsed < self.delay:
            time.sleep(self.delay - elapsed)
        self._last_request = time.time()

    def get(self, url):
        """HTMLを文字列で返す。取得できなければ None。"""
        if self.cache_dir:
            path = self._cache_path(url)
            if os.path.exists(path):
                self.stats["cached"] += 1
                with gzip.open(path, "rt", encoding="utf-8") as fh:
                    return fh.read()

        html = None
        for attempt in range(self.retries):
            self._throttle()
            try:
                req = urllib.request.Request(url, headers={
                    "User-Agent": UA,
                    "Accept-Language": "ja,en;q=0.8",
                })
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    raw = resp.read()
                    html = decode_html(raw, resp.headers.get("Content-Type", ""))
                break
            except urllib.error.HTTPError as exc:
                # 404 はリトライしても無駄
                if exc.code in (404, 410):
                    break
                time.sleep(2 ** attempt)
            except Exception:
                time.sleep(2 ** attempt)

        if html is None:
            self.stats["failed"] += 1
            return None

        self.stats["fetched"] += 1
        if self.cache_dir:
            with gzip.open(self._cache_path(url), "wt", encoding="utf-8") as fh:
                fh.write(html)
        return html


def decode_html(raw, content_type=""):
    """日本語サイトは Shift_JIS / EUC-JP が残っているので順に試す。"""
    charset = None
    match = re.search(r"charset=([\w\-]+)", content_type, re.I)
    if match:
        charset = match.group(1)
    if not charset:
        head = raw[:4096].decode("ascii", "ignore")
        match = re.search(r'charset=["\']?([\w\-]+)', head, re.I)
        if match:
            charset = match.group(1)

    candidates = [charset, "utf-8", "cp932", "euc_jp", "iso2022_jp"]
    for enc in candidates:
        if not enc:
            continue
        try:
            return raw.decode(enc)
        except (UnicodeDecodeError, LookupError):
            continue
    return raw.decode("utf-8", "replace")


# --------------------------------------------------------------------------
# 本文の正規化と判定
# --------------------------------------------------------------------------

_TAG_STRIP = re.compile(
    r"<(script|style|noscript)\b[^>]*>.*?</\1>", re.I | re.S)
_TAGS = re.compile(r"<[^>]+>")
_WS = re.compile(r"\s+")


def to_text(html):
    """HTMLから可読テキストを抽出し、表記ゆれを吸収した形に正規化する。"""
    text = _TAG_STRIP.sub(" ", html)
    text = _TAGS.sub(" ", text)
    text = urllib.parse.unquote(text)
    for entity, char in (("&nbsp;", " "), ("&amp;", "&"),
                         ("&lt;", "<"), ("&gt;", ">"), ("&quot;", '"')):
        text = text.replace(entity, char)
    # 全角英数と半角カナを統一。「外国人ＯＫ」と「外国人OK」を同一視するため
    text = unicodedata.normalize("NFKC", text)
    return _WS.sub(" ", text).strip()


def title_of(html):
    match = re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.S)
    if not match:
        return ""
    return _WS.sub(" ", _TAGS.sub("", match.group(1))).strip()


@dataclass
class Rule:
    name: str
    include: list = field(default_factory=list)
    exclude: list = field(default_factory=list)

    def judge(self, text):
        """(判定, 根拠となった語) を返す。否定表現を優先。"""
        hit_ex = [w for w in self.exclude if w in text]
        if hit_ex:
            return NO, hit_ex[0]
        hit_in = [w for w in self.include if w in text]
        if hit_in:
            return YES, hit_in[0]
        return UNKNOWN, ""


# --------------------------------------------------------------------------
# プロファイル
# --------------------------------------------------------------------------

@dataclass
class Profile:
    name: str
    listing_urls: list
    shop_link_pattern: str
    base_url: str = ""
    rules: list = field(default_factory=list)
    delay: float = 2.0

    @classmethod
    def load(cls, path):
        with open(path, encoding="utf-8") as fh:
            if path.endswith((".yaml", ".yml")):
                if yaml is None:
                    sys.exit("PyYAML が必要です: pip install pyyaml "
                             "(または JSON プロファイルを使用)")
                data = yaml.safe_load(fh)
            else:
                data = json.load(fh)

        listing = data["listing"]
        if "urls" in listing:
            urls = list(listing["urls"])
        else:
            template = listing["url_template"]
            start = listing.get("page_start", 1)
            count = listing.get("page_max", 10)
            urls = [template.format(page=p) for p in range(start, start + count)]

        rules = [Rule(name=n, include=r.get("include", []),
                      exclude=r.get("exclude", []))
                 for n, r in data.get("rules", {}).items()]

        return cls(
            name=data["name"],
            base_url=data.get("base_url", ""),
            listing_urls=urls,
            shop_link_pattern=listing["shop_link_pattern"],
            rules=rules,
            delay=data.get("delay", 2.0),
        )


# --------------------------------------------------------------------------
# 収集本体
# --------------------------------------------------------------------------

def robots_allows(url, ua=UA):
    """robots.txt を確認する。判断できない場合は None を返す。"""
    parts = urllib.parse.urlsplit(url)
    robots_url = f"{parts.scheme}://{parts.netloc}/robots.txt"
    parser = urllib.robotparser.RobotFileParser()
    parser.set_url(robots_url)
    try:
        parser.read()
    except Exception:
        return None
    return parser.can_fetch(ua, url)


def collect_shop_urls(profile, fetcher, limit=None):
    """一覧ページを巡回して店舗詳細URLを集める。空ページで打ち切る。"""
    pattern = re.compile(profile.shop_link_pattern)
    seen, ordered = set(), []
    empty_streak = 0

    for page_url in profile.listing_urls:
        html = fetcher.get(page_url)
        if not html:
            empty_streak += 1
            if empty_streak >= 2:
                break
            continue

        found = 0
        for match in pattern.finditer(html):
            href = match.group(1) if match.groups() else match.group(0)
            full = urllib.parse.urljoin(profile.base_url or page_url, href)
            full = full.split("#")[0]
            if full not in seen:
                seen.add(full)
                ordered.append(full)
                found += 1

        print(f"  一覧 {page_url} -> 新規 {found} 件 (累計 {len(ordered)})",
              file=sys.stderr)

        empty_streak = empty_streak + 1 if found == 0 else 0
        if empty_streak >= 2:
            print("  新規0が続いたため一覧の巡回を終了", file=sys.stderr)
            break
        if limit and len(ordered) >= limit:
            break

    return ordered[:limit] if limit else ordered


def inspect_shop(url, html, rules):
    text = to_text(html)
    row = {"url": url, "title": title_of(html), "text_len": len(text)}
    for rule in rules:
        verdict, evidence = rule.judge(text)
        row[rule.name] = verdict
        row[rule.name + "_evidence"] = evidence
    return row


def summarize(rows, rules):
    total = len(rows)
    summary = {"total_shops": total, "by_rule": {}}
    for rule in rules:
        counts = {YES: 0, NO: 0, UNKNOWN: 0}
        for row in rows:
            counts[row.get(rule.name, UNKNOWN)] += 1
        summary["by_rule"][rule.name] = counts

    # 全ルールが yes の店舗数（求めている交差集合）
    if rules:
        names = [r.name for r in rules]
        both = [r for r in rows if all(r.get(n) == YES for n in names)]
        summary["all_conditions_met"] = {
            "count": len(both),
            "rules": names,
            "shops": [{"title": r["title"], "url": r["url"]} for r in both[:100]],
        }
    return summary


def main():
    ap = argparse.ArgumentParser(description="店舗条件コレクタ")
    ap.add_argument("--profile", required=True, help="プロファイル (yaml/json)")
    ap.add_argument("--out", default="shops.csv", help="CSV出力先")
    ap.add_argument("--summary", default="summary.json", help="集計JSON出力先")
    ap.add_argument("--cache", default=".cache", help="HTMLキャッシュ先")
    ap.add_argument("--limit", type=int, help="収集する店舗数の上限")
    ap.add_argument("--delay", type=float, help="リクエスト間隔(秒)")
    ap.add_argument("--list-only", action="store_true",
                    help="店舗URLの収集のみ行い、詳細は取得しない")
    ap.add_argument("--force", action="store_true",
                    help="robots.txt が拒否していても続行する")
    args = ap.parse_args()

    profile = Profile.load(args.profile)
    delay = args.delay if args.delay is not None else profile.delay
    fetcher = Fetcher(delay=delay, cache_dir=args.cache)

    probe = profile.listing_urls[0]
    allowed = robots_allows(probe)
    if allowed is False and not args.force:
        sys.exit(f"robots.txt が {probe} の取得を許可していません。"
                 "対象サイトの利用規約を確認してください。"
                 "意図的に続行する場合は --force。")
    if allowed is None:
        print("robots.txt を確認できませんでした。続行します。", file=sys.stderr)

    print(f"[1/2] 店舗URLを収集 (profile={profile.name}, delay={delay}s)",
          file=sys.stderr)
    shop_urls = collect_shop_urls(profile, fetcher, limit=args.limit)
    print(f"  店舗URL {len(shop_urls)} 件", file=sys.stderr)

    if args.list_only:
        for url in shop_urls:
            print(url)
        return

    print(f"[2/2] 各店舗ページを判定", file=sys.stderr)
    rows = []
    for index, url in enumerate(shop_urls, 1):
        html = fetcher.get(url)
        if not html:
            continue
        rows.append(inspect_shop(url, html, profile.rules))
        if index % 25 == 0:
            print(f"  {index}/{len(shop_urls)}", file=sys.stderr)

    if rows:
        with open(args.out, "w", newline="", encoding="utf-8-sig") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)

    summary = summarize(rows, profile.rules)
    summary["fetch_stats"] = fetcher.stats
    summary["profile"] = profile.name
    with open(args.summary, "w", encoding="utf-8") as fh:
        json.dump(summary, fh, ensure_ascii=False, indent=2)

    print("\n===== 集計 =====", file=sys.stderr)
    print(f"判定した店舗数: {summary['total_shops']}", file=sys.stderr)
    for name, counts in summary["by_rule"].items():
        print(f"  {name}: OK {counts[YES]} / NG {counts[NO]} "
              f"/ 判定不能 {counts[UNKNOWN]}", file=sys.stderr)
    if "all_conditions_met" in summary:
        met = summary["all_conditions_met"]
        print(f"  全条件を満たす店舗: {met['count']} 件", file=sys.stderr)
    print(f"\nCSV: {args.out}\nJSON: {args.summary}", file=sys.stderr)


if __name__ == "__main__":
    main()
