#!/usr/bin/env python3
"""Uber 配達実績の取引明細を読み込み、案件判断に使う指標を出す。

標準ライブラリのみで動く。使い方は uber/README.md を参照。

    python3 uber/analyze.py data/*.csv
    python3 uber/analyze.py data/payments.csv --hours data/online.csv --target 320000
"""

from __future__ import annotations

import argparse
import csv
import io
import re
import sys
from collections import defaultdict
from datetime import datetime, timedelta

# ---------------------------------------------------------------- 列の検出

# Uber の書き出しはロケール・年度で列名が変わるため、候補を総当たりで当てる。
COLUMN_CANDIDATES = {
    "datetime": [
        "リクエスト日時", "受注日時", "開始日時", "配達日時", "取引日時", "日時", "日付",
        "request time", "requested at", "begintrip", "begin trip time", "trip request time",
        "local request timestamp", "datetime", "date/time", "timestamp", "date",
    ],
    "amount": [
        "支払総額", "受取金額", "収益", "売上", "合計", "金額", "報酬",
        "net earnings", "your earnings", "total earnings", "payout", "amount",
        "total", "fare", "gross", "earnings",
    ],
    "type": [
        "取引タイプ", "種類", "内容", "区分", "カテゴリ", "説明",
        "type", "transaction type", "category", "description", "item",
    ],
    "duration": [
        "所要時間", "配達時間", "稼働時間", "時間",
        "duration", "trip duration", "duration (min)", "time online",
    ],
    "distance": [
        "距離", "走行距離", "distance", "trip distance", "distance (km)", "miles",
    ],
}


def _norm(s: str) -> str:
    return re.sub(r"[\s_()（）\[\]/:：・-]", "", (s or "")).lower()


def pick_column(headers, key):
    """候補名に完全一致 → 部分一致の順で列を選ぶ。見つからなければ None。"""
    norm_map = {_norm(h): h for h in headers if h}
    for cand in COLUMN_CANDIDATES[key]:
        if _norm(cand) in norm_map:
            return norm_map[_norm(cand)]
    for cand in COLUMN_CANDIDATES[key]:
        nc = _norm(cand)
        for nh, h in norm_map.items():
            if nc and nc in nh:
                return h
    return None


# ---------------------------------------------------------------- 値の解析

DT_FORMATS = [
    "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d",
    "%Y/%m/%d %H:%M:%S", "%Y/%m/%d %H:%M", "%Y/%m/%d",
    "%m/%d/%Y %H:%M:%S", "%m/%d/%Y %H:%M", "%m/%d/%Y",
    "%d/%m/%Y %H:%M", "%Y年%m月%d日 %H:%M", "%Y年%m月%d日",
    "%m月%d日 %H:%M",
]


def parse_dt(raw):
    if not raw:
        return None
    s = str(raw).strip()
    # タイムゾーン表記・曜日・秒未満を落とす
    s = re.sub(r"\s*[+-]\d{2}:?\d{2}$", "", s)
    s = re.sub(r"\s*(UTC|GMT|JST|Z)$", "", s, flags=re.I)
    s = re.sub(r"\.\d+$", "", s)
    s = re.sub(r"[（(][月火水木金土日][）)]", "", s)
    s = s.replace("午前", "").replace("午後", "").strip()
    for fmt in DT_FORMATS:
        try:
            dt = datetime.strptime(s, fmt)
        except ValueError:
            continue
        if dt.year == 1900:  # 年のない形式
            return None
        return dt
    return None


def parse_amount(raw):
    """'¥1,234' '1234円' '-560' '(560)' などを float にする。"""
    if raw is None:
        return None
    s = str(raw).strip()
    if not s:
        return None
    neg = s.startswith("(") and s.endswith(")")
    s = re.sub(r"[¥￥$,、\s円]", "", s).strip("()")
    if not s or s in {"-", "--"}:
        return None
    try:
        v = float(s)
    except ValueError:
        return None
    return -v if neg else v


def parse_duration_min(raw):
    """'00:12:30' '12分' '12.5' を分に直す。"""
    if raw is None:
        return None
    s = str(raw).strip()
    if not s:
        return None
    m = re.match(r"^(\d+):(\d{2})(?::(\d{2}))?$", s)
    if m:
        h, mi, sec = int(m.group(1)), int(m.group(2)), int(m.group(3) or 0)
        return h * 60 + mi + sec / 60
    m = re.match(r"^(?:(\d+)\s*時間)?\s*(\d+)?\s*分", s)
    if m and (m.group(1) or m.group(2)):
        return int(m.group(1) or 0) * 60 + int(m.group(2) or 0)
    v = parse_amount(s)
    return v


# ---------------------------------------------------------------- 種別の分類

TYPE_BUCKETS = [
    ("チップ", ["チップ", "tip", "gratuity"]),
    ("インセンティブ", ["クエスト", "ブースト", "プロモ", "ボーナス", "インセンティブ", "キャンペーン",
                        "quest", "boost", "promotion", "surge", "incentive", "bonus"]),
    ("調整・その他", ["調整", "返金", "キャンセル", "参照", "紹介",
                      "adjustment", "refund", "cancel", "referral", "miscellaneous"]),
    ("配達", ["配達", "配送", "trip", "delivery", "fare", "order", "デリバリー"]),
]


def bucket_of(raw_type):
    s = (raw_type or "").lower()
    for name, keys in TYPE_BUCKETS:
        if any(k.lower() in s for k in keys):
            return name
    return "配達" if not s else "調整・その他"


# ---------------------------------------------------------------- 読み込み

def read_rows(path):
    """エンコーディングと区切り文字を推定して dict のリストを返す。"""
    raw = open(path, "rb").read()
    text = None
    for enc in ("utf-8-sig", "utf-8", "cp932", "shift_jis", "euc_jp"):
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    if text is None:
        raise SystemExit(f"{path}: 文字コードを判別できませんでした")
    sample = text[:8192]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",\t;")
        delim = dialect.delimiter
    except csv.Error:
        delim = "\t" if sample.count("\t") > sample.count(",") else ","
    return list(csv.DictReader(io.StringIO(text), delimiter=delim))


def load(paths, tz_shift=0.0):
    records, notes = [], []
    for path in paths:
        rows = read_rows(path)
        if not rows:
            notes.append(f"{path}: 行がありません（スキップ）")
            continue
        headers = list(rows[0].keys())
        cols = {k: pick_column(headers, k) for k in COLUMN_CANDIDATES}
        if not cols["datetime"] or not cols["amount"]:
            notes.append(f"{path}: 日時列または金額列を特定できず（列: {', '.join(h for h in headers if h)[:120]}）")
            continue
        notes.append(
            f"{path}: 日時={cols['datetime']} / 金額={cols['amount']}"
            + (f" / 種別={cols['type']}" if cols["type"] else " / 種別=なし")
        )
        kept = 0
        for r in rows:
            dt = parse_dt(r.get(cols["datetime"]))
            amt = parse_amount(r.get(cols["amount"]))
            if dt is None or amt is None:
                continue
            if tz_shift:
                dt += timedelta(hours=tz_shift)
            records.append({
                "dt": dt,
                "amount": amt,
                "raw_type": (r.get(cols["type"]) or "").strip() if cols["type"] else "",
                "duration": parse_duration_min(r.get(cols["duration"])) if cols["duration"] else None,
                "distance": parse_amount(r.get(cols["distance"])) if cols["distance"] else None,
            })
            kept += 1
        notes[-1] += f" → {kept}件"
    records.sort(key=lambda x: x["dt"])
    return records, notes


# ---------------------------------------------------------------- 稼働時間

def estimate_sessions(records, gap_min=45, tail_min=20):
    """取引の間隔から稼働セッションを復元する。

    実測のオンライン時間がない場合の代替。連続する取引の間隔が gap_min を超えたら
    別セッションとみなし、各セッションの実働 = (最終取引 - 最初の取引) + tail_min。
    """
    trips = [r for r in records if bucket_of(r["raw_type"]) == "配達"] or records
    if not trips:
        return []
    sessions, cur = [], [trips[0]]
    for prev, r in zip(trips, trips[1:]):
        if (r["dt"] - prev["dt"]).total_seconds() / 60 > gap_min:
            sessions.append(cur)
            cur = []
        cur.append(r)
    sessions.append(cur)
    out = []
    for s in sessions:
        span = (s[-1]["dt"] - s[0]["dt"]).total_seconds() / 60 + tail_min
        out.append({"start": s[0]["dt"], "end": s[-1]["dt"], "minutes": span, "trips": len(s)})
    return out


def load_hours(path, tz_shift=0.0):
    """オンライン時間の実測CSV（あれば）を日付→時間で返す。"""
    rows = read_rows(path)
    if not rows:
        return {}
    headers = list(rows[0].keys())
    dcol = pick_column(headers, "datetime")
    hcol = pick_column(headers, "duration")
    if not dcol or not hcol:
        return {}
    per_day = defaultdict(float)
    for r in rows:
        dt = parse_dt(r.get(dcol))
        mins = parse_duration_min(r.get(hcol))
        if dt is None or mins is None:
            continue
        if tz_shift:
            dt += timedelta(hours=tz_shift)
        # 1桁台なら「時間」表記とみなす
        per_day[dt.date()] += mins * 60 if mins < 24 else mins
    return dict(per_day)


# ---------------------------------------------------------------- 出力

WD = ["月", "火", "水", "木", "金", "土", "日"]


def yen(v):
    return f"¥{v:,.0f}"


def h1(t):
    print(f"\n{'=' * 62}\n{t}\n{'=' * 62}")


def h2(t):
    print(f"\n--- {t} " + "-" * max(0, 56 - len(t)))


def report(records, notes, hours_by_day, target, gap_min, tail_min):
    h1("0. 読み込み")
    for n in notes:
        print("  " + n)
    if not records:
        raise SystemExit("\n有効な取引が0件です。README.md の『取れなかったとき』を参照してください。")

    first, last = records[0]["dt"], records[-1]["dt"]
    days = max(1, (last.date() - first.date()).days + 1)
    total = sum(r["amount"] for r in records)
    print(f"\n  取引 {len(records):,} 件 / {first:%Y-%m-%d} 〜 {last:%Y-%m-%d}（{days}日間）")
    print(f"  総額 {yen(total)}")

    # ---- 収入の内訳
    h1("1. 収入の構造")
    by_bucket = defaultdict(float)
    cnt_bucket = defaultdict(int)
    for r in records:
        b = bucket_of(r["raw_type"])
        by_bucket[b] += r["amount"]
        cnt_bucket[b] += 1
    h2("種別")
    for b, v in sorted(by_bucket.items(), key=lambda x: -x[1]):
        print(f"  {b:<12} {yen(v):>12}  ({v / total * 100:5.1f}%)  {cnt_bucket[b]:>5}件")
    incentive = by_bucket.get("インセンティブ", 0.0)
    if total:
        share = incentive / total * 100
        print(f"\n  インセンティブ依存度: {share:.1f}%")
        if share >= 25:
            print("  → 依存度が高い。プロモが縮むと収入が直撃する。恒久収入として計上しないこと。")
        elif share > 0:
            print("  → 依存度は許容範囲。基本報酬で成立している。")

    h2("月別")
    by_month = defaultdict(float)
    days_in_month = defaultdict(set)
    for r in records:
        k = f"{r['dt']:%Y-%m}"
        by_month[k] += r["amount"]
        days_in_month[k].add(r["dt"].date())
    for k in sorted(by_month):
        d = len(days_in_month[k])
        print(f"  {k}  {yen(by_month[k]):>12}   稼働{d:>2}日   1日平均 {yen(by_month[k] / d)}")

    # ---- 実効時給
    h1("2. 実効時給（PLAN.md の基準線の検証）")
    if hours_by_day:
        total_hours = sum(hours_by_day.values())
        basis = "オンライン時間の実測値"
    else:
        sessions = estimate_sessions(records, gap_min, tail_min)
        total_hours = sum(s["minutes"] for s in sessions) / 60
        basis = f"取引間隔からの推定（{gap_min}分以上空いたら別セッション / 各セッションに{tail_min}分の尾を加算）"
        print(f"  稼働セッション {len(sessions)} 回")
    if total_hours <= 0:
        print("  稼働時間を算出できませんでした。")
        return
    hourly = total / total_hours
    print(f"  算出根拠: {basis}")
    print(f"  総稼働 {total_hours:,.1f} 時間 / 総額 {yen(total)}")
    print(f"\n  ★ 実効時給 = {yen(hourly)} / 時")

    print("\n  PLAN.md の基準線との比較")
    print(f"    保守見積 ¥2,000  → 実測は {hourly / 2000:.2f} 倍")
    for label, mult in (("見送りライン ¥3,000（1.5倍）", 1.5), ("狙い ¥5,000（2.5倍）", 2.5)):
        print(f"    {label:<28} 実測ベースだと {yen(hourly * mult)}")
    if hourly < 2000:
        print("\n  → 実測が保守見積を下回っている。PLAN.md の基準線 ¥2,000 は楽観。"
              "\n     案件の足切りラインを引き下げるか、Uber 側の稼働枠を組み替える必要がある。")
    elif hourly < 2500:
        print("\n  → 実測は保守見積とほぼ同水準。基準線 ¥2,000 は妥当。据え置きでよい。")
    else:
        print("\n  → 実測が保守見積を上回る。基準線を ¥2,000 に据えたまま運用するのは安全側。"
              "\n     ただし『Uber 増枠』の試算は実測値で置き直すと余力が増える。")

    # ---- 曜日 × 時間帯
    h1("3. どこで稼げているか（曜日 × 時間帯）")
    cell_amt = defaultdict(float)
    cell_cnt = defaultdict(int)
    for r in records:
        cell_amt[(r["dt"].weekday(), r["dt"].hour)] += r["amount"]
        cell_cnt[(r["dt"].weekday(), r["dt"].hour)] += 1
    hours_present = sorted({h for _, h in cell_amt})
    if hours_present:
        h2("売上（千円）")
        print("      " + "".join(f"{h:>5}" for h in hours_present))
        for w in range(7):
            row = "".join(
                (f"{cell_amt[(w, h)] / 1000:>5.0f}" if cell_amt.get((w, h)) else "    ·")
                for h in hours_present
            )
            print(f"  {WD[w]}  {row}")

    h2("時間帯別の1件単価（件数10件以上）")
    by_hour_amt, by_hour_cnt = defaultdict(float), defaultdict(int)
    for r in records:
        by_hour_amt[r["dt"].hour] += r["amount"]
        by_hour_cnt[r["dt"].hour] += 1
    ranked = [(h, by_hour_amt[h] / by_hour_cnt[h], by_hour_cnt[h])
              for h in by_hour_amt if by_hour_cnt[h] >= 10]
    ranked.sort(key=lambda x: -x[1])
    for h, per, c in ranked[:8]:
        print(f"  {h:>2}時台  1件 {yen(per):>8}   {c:>5}件   計 {yen(by_hour_amt[h])}")
    if not ranked:
        print("  （データが少なく、時間帯別の判断はまだできません）")

    current = set(range(18, 22))  # PLAN.md の現行デリバリー枠 18-21時
    outside = [(h, per, c) for h, per, c in ranked if h not in current]
    if outside:
        h2("増枠候補（現行の 18-21 時枠の外で単価が高い時間帯）")
        for h, per, c in outside[:5]:
            print(f"  {h:>2}時台  1件 {yen(per):>8}（{c}件の実績）")
        print("\n  → 増枠するならこの時間帯から。総稼働時間を増やす前に、"
              "\n     単価の低い枠を高い枠に置き換えられないかを先に見ること。")

    h2("曜日別")
    wd_amt, wd_days = defaultdict(float), defaultdict(set)
    for r in records:
        wd_amt[r["dt"].weekday()] += r["amount"]
        wd_days[r["dt"].weekday()].add(r["dt"].date())
    for w in range(7):
        if wd_days[w]:
            print(f"  {WD[w]}  計 {yen(wd_amt[w]):>12}   稼働{len(wd_days[w]):>2}日   "
                  f"1日平均 {yen(wd_amt[w] / len(wd_days[w]))}")

    # ---- 目標シミュレーション
    h1(f"4. 目標シミュレーション（月 {yen(target)}）")
    need_h = target / hourly
    print(f"  実効時給 {yen(hourly)} で月 {yen(target)} を作るのに必要な稼働: {need_h:,.1f} 時間/月")
    print(f"    週6日で割ると {need_h / 26:.1f} 時間/日")
    print(f"    週5日で割ると {need_h / 22:.1f} 時間/日")
    if need_h / 22 > 8:
        print("\n  → 週5×8時間で届かない。この目標を Uber 単独で埋めるのは非現実的。"
              "\n     PLAN.md 第3章の保険を複数本立てる前提で計画すること。")
    elif need_h / 22 > 6:
        print("\n  → 週5でほぼフル稼働。案件の稼働と並行させる余地はほとんど残らない。")
    else:
        print("\n  → 週5で1日6時間以内に収まる。案件と並行できる水準。")

    if by_month:
        recent = sorted(by_month)[-1]
        print(f"\n  直近月（{recent}）の実績 {yen(by_month[recent])} との差分: "
              f"{yen(target - by_month[recent])}")


def main():
    p = argparse.ArgumentParser(description="Uber 配達実績の取引明細を分析する")
    p.add_argument("files", nargs="+", help="取引明細の CSV / TSV")
    p.add_argument("--hours", help="オンライン時間の実測CSV（あれば実効時給が推定でなく実測になる）")
    p.add_argument("--target", type=int, default=320000, help="月次の目標収入（既定: 320000）")
    p.add_argument("--tz-shift", type=float, default=0.0,
                   help="時刻の補正時間。Uber の書き出しがUTCなら 9 を指定")
    p.add_argument("--gap-min", type=int, default=45, help="セッションの区切りとみなす無取引の分数")
    p.add_argument("--tail-min", type=int, default=20, help="各セッションの末尾に加算する分数")
    a = p.parse_args()

    records, notes = load(a.files, a.tz_shift)
    hours = load_hours(a.hours, a.tz_shift) if a.hours else {}
    report(records, notes, hours, a.target, a.gap_min, a.tail_min)

    if not a.tz_shift and records:
        night = sum(1 for r in records if r["dt"].hour in (0, 1, 2, 3, 4, 5))
        if night > len(records) * 0.4:
            print("\n[注意] 深夜帯の取引が異常に多い。書き出しがUTCの可能性がある。"
                  "\n       --tz-shift 9 を付けて再実行してください。")


if __name__ == "__main__":
    main()
