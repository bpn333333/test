"""出力の整形: コンソール表 / CSV / JSON / HTML。"""

from __future__ import annotations

import csv
import html
import json
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Optional

from .models import AMAZON, MARKET_LABELS, RAKUTEN, TAOBAO, ComparisonRow

# --- 全角対応の文字幅計算 ------------------------------------------------
def display_width(text: str) -> int:
    """東アジア文字(全角)を2幅として数える。商品名が日本語/中国語でも崩れないように。"""
    return sum(2 if unicodedata.east_asian_width(ch) in "WF" else 1 for ch in str(text))


def pad(text: str, width: int, align: str = "left") -> str:
    text = str(text)
    padding = max(0, width - display_width(text))
    if align == "right":
        return " " * padding + text
    if align == "center":
        left = padding // 2
        return " " * left + text + " " * (padding - left)
    return text + " " * padding


def truncate(text: str, width: int) -> str:
    """表示幅ベースで切り詰める(末尾は…)。"""
    text = str(text or "")
    if display_width(text) <= width:
        return text
    out, current = "", 0
    for ch in text:
        w = 2 if unicodedata.east_asian_width(ch) in "WF" else 1
        if current + w > width - 1:
            break
        out += ch
        current += w
    return out + "…"


# --- 値の整形 ------------------------------------------------------------
def fmt_yen(value: Optional[float], *, signed: bool = False) -> str:
    if value is None:
        return "-"
    sign = "+" if signed and value > 0 else ""
    return f"{sign}{value:,.0f}"


def fmt_ratio(value: Optional[float]) -> str:
    return "-" if value is None else f"{value * 100:+.0f}%"


def fmt_weight(value: Optional[float]) -> str:
    if value is None:
        return "-"
    if value >= 1000:
        return f"{value / 1000:.2f}kg"
    return f"{value:.0f}g"


def fmt_rank(value: Optional[int]) -> str:
    return "圏外" if value is None else f"{value:,}位"


def row_to_record(row: ComparisonRow) -> dict[str, Any]:
    """1行を、出力形式に依らない素のレコードに落とす。"""
    best_market, best_price = row.best_jp
    taobao, amazon, rakuten = row.taobao, row.amazon, row.rakuten
    return {
        "key": row.key,
        "商品名": row.name,
        "淘宝価格_元": taobao.price if taobao else None,
        "淘宝リンク": taobao.url if taobao else "",
        "日本着原価_円": round(row.cost_jpy) if row.cost_jpy is not None else None,
        "Amazon価格_円": row.amazon_price,
        "Amazonリンク": amazon.url if amazon else "",
        "Amazonランキング": row.amazon_rank,
        "Amazonカテゴリ": amazon.rank_category if amazon else None,
        "楽天価格_円": row.rakuten_price,
        "楽天リンク": rakuten.url if rakuten else "",
        "楽天ランキング": row.rakuten_rank,
        "楽天ジャンル": rakuten.rank_category if rakuten else None,
        "最高値モール": MARKET_LABELS.get(best_market or "", ""),
        "最高値_円": round(best_price) if best_price else None,
        "価格差_円": round(row.best_diff) if row.best_diff is not None else None,
        "価格差率": round(row.best_diff_ratio, 4) if row.best_diff_ratio is not None else None,
        "Amazon価格差_円": round(row.diff(AMAZON)) if row.diff(AMAZON) is not None else None,
        "楽天価格差_円": round(row.diff(RAKUTEN)) if row.diff(RAKUTEN) is not None else None,
        "重さ_g": round(row.weight_g) if row.weight_g else None,
        "重さ取得元": row.weight_source,
        "原価内訳": row.landed.to_dict() if row.landed else None,
        "為替_CNYJPY": round(row.fx_rate, 3) if row.fx_rate else None,
        "警告": "; ".join(row.errors),
    }


# --- コンソール ----------------------------------------------------------
CONSOLE_COLUMNS = [
    ("#", 3, "right"),
    ("商品名", 26, "left"),
    ("原価", 8, "right"),
    ("Amazon", 8, "right"),
    ("楽天", 8, "right"),
    ("価格差", 9, "right"),
    ("差率", 6, "right"),
    ("重さ", 7, "right"),
    ("Amazonランク", 12, "right"),
    ("楽天ランク", 10, "right"),
]


def render_console(rows: Iterable[ComparisonRow], *, show_links: bool = True) -> str:
    rows = list(rows)
    lines: list[str] = []

    header = " ".join(pad(name, width, "center") for name, width, _ in CONSOLE_COLUMNS)
    separator = " ".join("-" * width for _, width, _ in CONSOLE_COLUMNS)
    lines.append(header)
    lines.append(separator)

    for index, row in enumerate(rows, start=1):
        values = [
            str(index),
            truncate(row.name, 26),
            fmt_yen(row.cost_jpy),
            fmt_yen(row.amazon_price),
            fmt_yen(row.rakuten_price),
            fmt_yen(row.best_diff, signed=True),
            fmt_ratio(row.best_diff_ratio),
            fmt_weight(row.weight_g),
            fmt_rank(row.amazon_rank),
            fmt_rank(row.rakuten_rank),
        ]
        lines.append(
            " ".join(
                pad(value, width, align)
                for value, (_, width, align) in zip(values, CONSOLE_COLUMNS)
            )
        )

    if show_links and rows:
        lines.append("")
        lines.append("商品リンク:")
        for index, row in enumerate(rows, start=1):
            parts = []
            for market in (TAOBAO, AMAZON, RAKUTEN):
                offer = row.offers.get(market)
                if offer and offer.url:
                    parts.append(f"{MARKET_LABELS[market]} {offer.url}")
            if parts:
                lines.append(f"  {index:>2}. {truncate(row.name, 24)}")
                for part in parts:
                    lines.append(f"      {part}")

    warnings = [(index, row) for index, row in enumerate(rows, start=1) if row.errors]
    if warnings:
        lines.append("")
        lines.append("警告:")
        for index, row in warnings:
            for error in row.errors:
                lines.append(f"  {index:>2}. {truncate(row.name, 20)}: {error}")

    return "\n".join(lines)


def render_summary(rows: list[ComparisonRow], fx, elapsed: Optional[float] = None) -> str:
    priced = [r for r in rows if r.best_diff is not None]
    lines = [f"対象 {len(rows)}件 / 価格差を算出できたもの {len(priced)}件", f"為替: {fx.describe()}"]
    if priced:
        total = sum(r.best_diff for r in priced)
        lines.append(
            f"価格差の平均 {fmt_yen(total / len(priced))}円 / "
            f"最大 {fmt_yen(max(r.best_diff for r in priced))}円"
        )
    if elapsed is not None:
        lines.append(f"所要 {elapsed:.1f}秒")
    return "\n".join(lines)


# --- ファイル出力 --------------------------------------------------------
CSV_COLUMNS = [
    "商品名",
    "淘宝価格_元",
    "日本着原価_円",
    "Amazon価格_円",
    "楽天価格_円",
    "最高値モール",
    "価格差_円",
    "価格差率",
    "Amazon価格差_円",
    "楽天価格差_円",
    "重さ_g",
    "重さ取得元",
    "Amazonランキング",
    "Amazonカテゴリ",
    "楽天ランキング",
    "楽天ジャンル",
    "淘宝リンク",
    "Amazonリンク",
    "楽天リンク",
    "警告",
]


def write_csv(rows: Iterable[ComparisonRow], path: str | Path) -> Path:
    path = Path(path).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    # Excel でそのまま開けるよう BOM 付き UTF-8
    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row_to_record(row))
    return path


def write_json(rows: Iterable[ComparisonRow], path: str | Path, *, meta: Optional[dict] = None) -> Path:
    path = Path(path).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "meta": meta or {},
        "items": [row_to_record(row) for row in rows],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


# --- HTML ---------------------------------------------------------------
HTML_STYLE = """
:root{color-scheme:light dark;--bg:#ffffff;--fg:#1a1a1a;--muted:#6b7280;--line:#e5e7eb;
--head:#f7f7f8;--pos:#0f7b3f;--neg:#b3261e;--accent:#1a56db;--chip:#f1f5f9}
@media (prefers-color-scheme:dark){:root{--bg:#16181d;--fg:#e8eaed;--muted:#9aa0a6;--line:#2c2f36;
--head:#1e2127;--pos:#5ad18a;--neg:#f2837b;--accent:#7aa7ff;--chip:#22262e}}
*{box-sizing:border-box}
body{margin:0;padding:24px;background:var(--bg);color:var(--fg);
font-family:-apple-system,BlinkMacSystemFont,"Hiragino Sans","Noto Sans JP","Yu Gothic",sans-serif;
font-size:14px;line-height:1.6}
h1{font-size:20px;margin:0 0 4px}
.meta{color:var(--muted);font-size:12px;margin-bottom:16px}
.cards{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:16px}
.card{background:var(--chip);border:1px solid var(--line);border-radius:8px;padding:8px 12px}
.card b{display:block;font-size:18px}
.card span{color:var(--muted);font-size:11px}
.wrap{overflow-x:auto;border:1px solid var(--line);border-radius:8px}
table{border-collapse:collapse;width:100%;min-width:900px}
th,td{padding:8px 10px;border-bottom:1px solid var(--line);text-align:right;white-space:nowrap}
th{background:var(--head);position:sticky;top:0;cursor:pointer;user-select:none;font-weight:600}
th:hover{color:var(--accent)}
th.asc::after{content:" ▲"}th.desc::after{content:" ▼"}
td.name,th.name{text-align:left;white-space:normal;min-width:220px;max-width:340px}
tbody tr:hover{background:var(--head)}
a{color:var(--accent);text-decoration:none}a:hover{text-decoration:underline}
.links{display:flex;gap:6px;margin-top:4px}
.links a{font-size:11px;border:1px solid var(--line);border-radius:4px;padding:1px 6px;color:var(--muted)}
.pos{color:var(--pos);font-weight:600}.neg{color:var(--neg)}
.muted{color:var(--muted)}
footer{margin-top:16px;color:var(--muted);font-size:11px}
"""

HTML_SCRIPT = """
document.querySelectorAll('th[data-idx]').forEach(function(th){
  th.addEventListener('click', function(){
    var table = th.closest('table');
    var idx = +th.dataset.idx;
    var asc = !th.classList.contains('asc');
    table.querySelectorAll('th').forEach(function(h){h.classList.remove('asc','desc')});
    th.classList.add(asc ? 'asc' : 'desc');
    var rows = Array.from(table.querySelectorAll('tbody tr'));
    rows.sort(function(a, b){
      var x = a.children[idx].dataset.v, y = b.children[idx].dataset.v;
      var nx = parseFloat(x), ny = parseFloat(y);
      var bothNum = !isNaN(nx) && !isNaN(ny);
      if (x === '' || x == null) return 1;
      if (y === '' || y == null) return -1;
      var cmp = bothNum ? nx - ny : String(x).localeCompare(String(y), 'ja');
      return asc ? cmp : -cmp;
    });
    var body = table.querySelector('tbody');
    rows.forEach(function(r){ body.appendChild(r) });
  });
});
"""

HTML_HEADERS = [
    ("商品名", "name"),
    ("原価(円)", ""),
    ("Amazon(円)", ""),
    ("楽天(円)", ""),
    ("価格差(円)", ""),
    ("差率", ""),
    ("重さ", ""),
    ("Amazonランキング", ""),
    ("楽天ランキング", ""),
]


def _cell(value: str, sort_value: Any = "", css: str = "") -> str:
    classes = f' class="{css}"' if css else ""
    return f'<td data-v="{html.escape(str(sort_value))}"{classes}>{value}</td>'


def render_html(rows: list[ComparisonRow], *, fx=None, title: str = "淘宝 × 日本 価格差レポート") -> str:
    generated = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M")
    priced = [r for r in rows if r.best_diff is not None]
    avg = sum(r.best_diff for r in priced) / len(priced) if priced else None

    cards = [
        ("対象商品", f"{len(rows)}件"),
        ("価格差 平均", f"{fmt_yen(avg)}円" if avg is not None else "-"),
        ("価格差 最大", f"{fmt_yen(max((r.best_diff for r in priced), default=None))}円" if priced else "-"),
        ("為替", f"{fx.rate:.2f}円/元" if fx else "-"),
    ]
    card_html = "".join(
        f'<div class="card"><span>{html.escape(label)}</span><b>{html.escape(value)}</b></div>'
        for label, value in cards
    )

    header_html = "".join(
        f'<th data-idx="{index}" class="{css}">{html.escape(label)}</th>'
        for index, (label, css) in enumerate(HTML_HEADERS)
    )

    body_rows = []
    for row in rows:
        links = []
        for market in (TAOBAO, AMAZON, RAKUTEN):
            offer = row.offers.get(market)
            if offer and offer.url:
                links.append(
                    f'<a href="{html.escape(offer.url)}" target="_blank" rel="noopener">'
                    f"{MARKET_LABELS[market]}</a>"
                )
        name_cell = (
            f'<td class="name" data-v="{html.escape(row.name)}">{html.escape(row.name)}'
            f'<div class="links">{"".join(links)}</div></td>'
        )
        diff_css = "pos" if (row.best_diff or 0) > 0 else ("neg" if row.best_diff is not None else "muted")
        body_rows.append(
            "<tr>"
            + name_cell
            + _cell(fmt_yen(row.cost_jpy), row.cost_jpy if row.cost_jpy is not None else "")
            + _cell(fmt_yen(row.amazon_price), row.amazon_price if row.amazon_price else "")
            + _cell(fmt_yen(row.rakuten_price), row.rakuten_price if row.rakuten_price else "")
            + _cell(fmt_yen(row.best_diff, signed=True), row.best_diff if row.best_diff is not None else "", diff_css)
            + _cell(fmt_ratio(row.best_diff_ratio), row.best_diff_ratio if row.best_diff_ratio is not None else "", diff_css)
            + _cell(fmt_weight(row.weight_g), row.weight_g or "")
            + _cell(fmt_rank(row.amazon_rank), row.amazon_rank or "", "" if row.amazon_rank else "muted")
            + _cell(fmt_rank(row.rakuten_rank), row.rakuten_rank or "", "" if row.rakuten_rank else "muted")
            + "</tr>"
        )

    return f"""<!DOCTYPE html>
<html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title><style>{HTML_STYLE}</style></head>
<body>
<h1>{html.escape(title)}</h1>
<div class="meta">生成 {generated} ／ 価格差 = 日本側の最高値 − 日本着原価(商品代+中国国内送料+代行手数料+国際送料+税)。
ランキングは Amazon 売れ筋ランキングと楽天ジャンル別ランキング。列見出しをクリックすると並べ替えできます。</div>
<div class="cards">{card_html}</div>
<div class="wrap"><table><thead><tr>{header_html}</tr></thead><tbody>
{chr(10).join(body_rows)}
</tbody></table></div>
<footer>pricediff — 価格・ランキングは取得時点のもの。仕入れ判断の前に必ず実ページで確認してください。</footer>
<script>{HTML_SCRIPT}</script>
</body></html>"""


def write_html(rows: list[ComparisonRow], path: str | Path, *, fx=None, title: Optional[str] = None) -> Path:
    path = Path(path).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        render_html(rows, fx=fx, title=title or "淘宝 × 日本 価格差レポート"), encoding="utf-8"
    )
    return path
