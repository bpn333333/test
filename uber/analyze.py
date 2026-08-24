#!/usr/bin/env python3
"""配達1件ごとの記録から「どう動けば効率よく稼げるか」を出す。

出すのは指標ではなく行動。具体的には次の4つ。
  1. 受注判断  — どの条件の注文を断ると時給が上がるか（閾値の総当たり）
  2. 稼働枠    — 何曜日の何時に走るか
  3. 待機場所  — どのエリアで待つか
  4. 避ける店  — 待たされて損をしている受取先

使い方は uber/README.md を参照。
"""

from __future__ import annotations

import argparse
import csv
import io
import re
import statistics
import sys
from collections import defaultdict
from datetime import datetime, timedelta

# ---------------------------------------------------------------- 列の検出

COLUMN_CANDIDATES = {
    "datetime": ["受注日時", "リクエスト日時", "開始日時", "配達日時", "取引日時", "日時", "日付",
                 "request time", "requested at", "begintrip", "trip request time", "timestamp", "date"],
    "amount": ["報酬", "受取金額", "支払総額", "合計", "収益", "売上", "金額",
               "net earnings", "your earnings", "total earnings", "payout", "amount", "total", "fare"],
    "duration": ["所要時間", "配達時間", "稼働時間", "時間", "duration", "trip duration"],
    "distance": ["距離", "走行距離", "distance", "trip distance"],
    "pickup": ["受取場所", "受取店舗", "店舗", "レストラン", "ピックアップ", "受取",
               "pickup", "restaurant", "merchant", "store", "pickup address"],
    "dropoff": ["配達先", "お届け先", "エリア", "配達エリア", "dropoff", "destination", "drop off address"],
    "tip": ["チップ", "tip", "gratuity"],
    "promo": ["プロモ", "クエスト", "ブースト", "インセンティブ", "ボーナス",
              "promotion", "quest", "boost", "incentive", "bonus", "surge"],
    "wait": ["待ち時間", "待機時間", "店舗待ち", "wait time", "waiting"],
}


def _norm(s):
    return re.sub(r"[\s_()（）\[\]/:：・-]", "", (s or "")).lower()


def pick_column(headers, key):
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
    "%Y年%m月%d日 %H:%M", "%Y年%m月%d日",
]


def parse_dt(raw):
    if not raw:
        return None
    s = str(raw).strip()
    s = re.sub(r"\s*[+-]\d{2}:?\d{2}$", "", s)
    s = re.sub(r"\s*(UTC|GMT|JST|Z)$", "", s, flags=re.I)
    s = re.sub(r"\.\d+$", "", s)
    s = re.sub(r"[（(][月火水木金土日][）)]", "", s).strip()
    for fmt in DT_FORMATS:
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


def parse_num(raw):
    if raw is None:
        return None
    s = str(raw).strip()
    if not s:
        return None
    neg = s.startswith("(") and s.endswith(")")
    s = re.sub(r"[¥￥$,、\s円kmKM分]", "", s).strip("()")
    if not s or s in {"-", "--"}:
        return None
    try:
        v = float(s)
    except ValueError:
        return None
    return -v if neg else v


def parse_minutes(raw):
    if raw is None:
        return None
    s = str(raw).strip()
    if not s:
        return None
    m = re.match(r"^(\d+):(\d{2})(?::(\d{2}))?$", s)
    if m:
        return int(m.group(1)) * 60 + int(m.group(2)) + int(m.group(3) or 0) / 60
    m = re.match(r"^(?:(\d+)\s*時間)?\s*(\d+)?\s*分", s)
    if m and (m.group(1) or m.group(2)):
        return int(m.group(1) or 0) * 60 + int(m.group(2) or 0)
    return parse_num(s)


# ---------------------------------------------------------------- 読み込み

def read_rows(path):
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
        delim = csv.Sniffer().sniff(sample, delimiters=",\t;").delimiter
    except csv.Error:
        delim = "\t" if sample.count("\t") > sample.count(",") else ","
    return list(csv.DictReader(io.StringIO(text), delimiter=delim))


def load(paths, tz_shift=0.0):
    trips, notes = [], []
    for path in paths:
        rows = read_rows(path)
        if not rows:
            notes.append(f"{path}: 行がありません")
            continue
        headers = list(rows[0].keys())
        cols = {k: pick_column(headers, k) for k in COLUMN_CANDIDATES}
        if not cols["datetime"] or not cols["amount"]:
            notes.append(f"{path}: 日時列/金額列を特定できず（列: {', '.join(h for h in headers if h)[:120]}）")
            continue
        found = [f"{k}={v}" for k, v in cols.items() if v]
        notes.append(f"{path}: " + " / ".join(found))
        kept = 0
        for r in rows:
            dt = parse_dt(r.get(cols["datetime"]))
            amt = parse_num(r.get(cols["amount"]))
            if dt is None or amt is None:
                continue
            if tz_shift:
                dt += timedelta(hours=tz_shift)
            trips.append({
                "dt": dt,
                "amount": amt,
                "minutes": parse_minutes(r.get(cols["duration"])) if cols["duration"] else None,
                "km": parse_num(r.get(cols["distance"])) if cols["distance"] else None,
                "pickup": (r.get(cols["pickup"]) or "").strip() if cols["pickup"] else "",
                "area": (r.get(cols["dropoff"]) or "").strip() if cols["dropoff"] else "",
                "tip": parse_num(r.get(cols["tip"])) if cols["tip"] else None,
                "promo": parse_num(r.get(cols["promo"])) if cols["promo"] else None,
                "wait": parse_minutes(r.get(cols["wait"])) if cols["wait"] else None,
            })
            kept += 1
        notes[-1] += f" → {kept}件"
    trips.sort(key=lambda x: x["dt"])
    return trips, notes


# ---------------------------------------------------------------- 稼働の復元

def build_sessions(trips, gap_min=45):
    """連続稼働のかたまりを復元し、各件の『次の注文までの空き時間』も埋める。"""
    if not trips:
        return []
    sessions, cur = [], [trips[0]]
    for prev, t in zip(trips, trips[1:]):
        if (t["dt"] - prev["dt"]).total_seconds() / 60 > gap_min:
            sessions.append(cur)
            cur = []
        cur.append(t)
    sessions.append(cur)
    for s in sessions:
        for a, b in zip(s, s[1:]):
            span = (b["dt"] - a["dt"]).total_seconds() / 60
            a["cycle"] = span                      # 受注から次の受注までの実サイクル
            if a["minutes"] is not None:
                a["idle"] = max(0.0, span - a["minutes"])
        s[-1].setdefault("cycle", s[-1]["minutes"] or 0)
    return sessions


def online_minutes(sessions, tail_min=20):
    return sum((s[-1]["dt"] - s[0]["dt"]).total_seconds() / 60 + tail_min for s in sessions)


def per_min(t):
    """1件の分あたり単価。所要時間がなければサイクルで代用。"""
    d = t.get("minutes") or t.get("cycle")
    return t["amount"] / d if d and d > 0 else None


# ---------------------------------------------------------------- 出力補助

WD = ["月", "火", "水", "木", "金", "土", "日"]


def yen(v):
    return f"¥{v:,.0f}"


def h1(t):
    print(f"\n{'=' * 64}\n{t}\n{'=' * 64}")


def h2(t):
    print(f"\n--- {t} " + "-" * max(0, 58 - len(t)))


def pct(vals, p):
    if not vals:
        return None
    s = sorted(vals)
    i = min(len(s) - 1, max(0, int(round((len(s) - 1) * p / 100))))
    return s[i]


# ---------------------------------------------------------------- 1. 受注判断

def accept_rules(trips, sessions, online_h):
    """『この条件を断っていたら時給はどうなったか』を総当たりで試す。

    断って空いた時間の扱いで結果が変わるため、上下2つの見方を両方出す。
      働いた分の単価 = 受けた注文の 報酬合計 ÷ 所要時間合計
                       （空き時間が同水準の注文で埋まる前提＝上限）
      実効時給       = 受けた注文の 報酬合計 ÷ 総オンライン時間
                       （空き時間が一切埋まらない前提＝下限）
    2つの差が小さい条件ほど、実行しても取りこぼしが少ない。
    """
    h1("1. 受注判断 — どの注文を断ると時給が上がるか")

    usable = [t for t in trips if per_min(t) is not None]
    if not usable:
        print("  所要時間の情報がないため、受注判断は算出できません。")
        print("  → README の収集項目に『所要時間』を必ず含めてください。")
        return None

    base_amt = sum(t["amount"] for t in usable)
    base_work = sum((t.get("minutes") or t.get("cycle") or 0) for t in usable)
    base_permin = base_amt / base_work if base_work else 0
    base_hourly = base_amt / online_h if online_h else 0
    print(f"  現状（全件受注）  働いた分の単価 {yen(base_permin * 60)}/h   "
          f"実効時給 {yen(base_hourly)}/h")

    rates = sorted(per_min(t) for t in usable)
    print(f"\n  1件の分あたり単価の分布（{len(usable)}件）")
    for label, p in (("下位10%", 10), ("下位25%", 25), ("中央", 50), ("上位25%", 75), ("上位10%", 90)):
        v = pct(rates, p)
        print(f"    {label:<8} {yen(v)}/分  = {yen(v * 60)}/h 相当")

    # 候補ルールを総当たり
    cands = []
    for p in (10, 15, 20, 25, 30, 40):
        thr = pct(rates, p)
        cands.append((f"分あたり {yen(thr)} 未満を断る（下位{p}%）",
                      lambda t, thr=thr: per_min(t) >= thr))
    kms = [t["km"] for t in usable if t.get("km")]
    if kms:
        for p in (75, 85, 90):
            thr = pct(kms, p)
            cands.append((f"{thr:.1f}km 以上を断る（上位{100 - p}%の長距離）",
                          lambda t, thr=thr: (t.get("km") or 0) < thr))
        per_km = [t["amount"] / t["km"] for t in usable if t.get("km")]
        for p in (15, 25):
            thr = pct(per_km, p)
            cands.append((f"1kmあたり {yen(thr)} 未満を断る",
                          lambda t, thr=thr: not t.get("km") or t["amount"] / t["km"] >= thr))
    amts = sorted(t["amount"] for t in usable)
    for p in (10, 20):
        thr = pct(amts, p)
        cands.append((f"報酬 {yen(thr)} 未満を断る", lambda t, thr=thr: t["amount"] >= thr))

    print("\n  ルールを適用した場合の試算")
    print(f"    {'ルール':<38}{'働いた分':>10}{'実効時給':>10}{'断る件数':>9}")
    results = []
    for name, keep in cands:
        kept = [t for t in usable if keep(t)]
        if not kept or len(kept) == len(usable):
            continue
        amt = sum(t["amount"] for t in kept)
        work = sum((t.get("minutes") or t.get("cycle") or 0) for t in kept)
        if not work:
            continue
        upper = amt / work * 60
        lower = amt / online_h if online_h else 0
        results.append((name, upper, lower, len(usable) - len(kept)))
        print(f"    {name:<38}{yen(upper):>10}{yen(lower):>10}{len(usable) - len(kept):>7}件")

    if not results:
        print("    有効な閾値が見つかりませんでした。")
        return None

    # 「働いた分の単価が上がり、かつ実効時給の落ち込みが小さい」ものを推す
    scored = [(u - base_permin * 60, u, l, n, c) for n, u, l, c in results]
    scored.sort(key=lambda x: -(x[0] - max(0, base_hourly - x[2])))
    gain, upper, lower, name, cnt = scored[0]
    h2("結論")
    print(f"  採用するルール: {name}")
    print(f"    働いた分の単価  {yen(base_permin * 60)} → {yen(upper)}  （+{yen(gain)}）")
    print(f"    断る件数        {cnt}件 / {len(usable)}件（{cnt / len(usable) * 100:.0f}%）")
    if lower < base_hourly:
        print(f"\n  ただし断った時間が全く埋まらないと実効時給は {yen(base_hourly)} → {yen(lower)} に下がる。")
        print("  → **注文が途切れない時間帯でだけ**このルールを使うこと。")
        print("     暇な時間帯で選り好みすると、空き時間の損の方が大きくなる。")
    else:
        print("\n  空き時間が埋まらない前提でも時給が下がらない。無条件で適用してよい。")
    return {"rule": name, "upper": upper, "lower": lower, "base_hourly": base_hourly}


# ---------------------------------------------------------------- 2. 稼働枠

def when_to_work(trips, sessions):
    h1("2. 稼働枠 — いつ走るか")

    # 時間帯ごとに「その時間に稼働していた分数」と「稼いだ額」を積む
    hour_amt, hour_min, hour_cnt = defaultdict(float), defaultdict(float), defaultdict(int)
    for s in sessions:
        for t in s:
            hour_amt[t["dt"].hour] += t["amount"]
            hour_min[t["dt"].hour] += t.get("cycle") or t.get("minutes") or 0
            hour_cnt[t["dt"].hour] += 1

    rows = [(h, hour_amt[h] / hour_min[h] * 60, hour_cnt[h], hour_amt[h])
            for h in hour_amt if hour_min[h] > 0 and hour_cnt[h] >= 5]
    rows.sort(key=lambda x: -x[1])
    if not rows:
        print("  データが少なく、時間帯の判断はできません。")
        return
    h2("時間帯別の時給（5件以上の実績がある時間帯）")
    print(f"    {'時':>4}{'時給':>11}{'件数':>7}{'合計':>12}")
    for h, hourly, c, amt in rows:
        bar = "█" * max(1, int(hourly / max(r[1] for r in rows) * 24))
        print(f"    {h:>2}時{yen(hourly):>11}{c:>6}件{yen(amt):>12}  {bar}")

    best = [h for h, _, _, _ in rows[:4]]
    worst = [h for h, _, _, _ in rows[-3:] if len(rows) > 5]
    h2("結論")
    print(f"  最も濃い時間帯: {'、'.join(f'{h}時台' for h in sorted(best))}")
    print("  → ここは何があっても走る。ここを外すと同じ稼働時間でも収入が落ちる。")
    if worst:
        print(f"\n  薄い時間帯: {'、'.join(f'{h}時台' for h in sorted(worst))}")
        print("  → 稼働時間を削るならここから。走っても時給が伸びない。")

    # 曜日 × 時間帯
    h2("曜日 × 時間帯の時給")
    cell_amt, cell_min = defaultdict(float), defaultdict(float)
    for s in sessions:
        for t in s:
            k = (t["dt"].weekday(), t["dt"].hour)
            cell_amt[k] += t["amount"]
            cell_min[k] += t.get("cycle") or t.get("minutes") or 0
    hs = sorted({h for _, h in cell_amt})
    print("      " + "".join(f"{h:>6}" for h in hs))
    for w in range(7):
        cells = []
        for h in hs:
            k = (w, h)
            if cell_min.get(k, 0) > 0:
                cells.append(f"{cell_amt[k] / cell_min[k] * 60 / 1000:>6.1f}")
            else:
                cells.append("     ·")
        print(f"  {WD[w]}  " + "".join(cells))
    print("  （単位: 千円/時。· は実績なし）")

    wd_amt, wd_min = defaultdict(float), defaultdict(float)
    for s in sessions:
        for t in s:
            wd_amt[t["dt"].weekday()] += t["amount"]
            wd_min[t["dt"].weekday()] += t.get("cycle") or t.get("minutes") or 0
    ranked = sorted(((w, wd_amt[w] / wd_min[w] * 60) for w in wd_amt if wd_min[w] > 0),
                    key=lambda x: -x[1])
    print("\n  曜日別の時給: " + " / ".join(f"{WD[w]} {yen(v)}" for w, v in ranked))


# ---------------------------------------------------------------- 3. 待機場所

def where_to_wait(trips):
    h1("3. 待機場所 — どこで待つか")
    areas = defaultdict(list)
    for t in trips:
        if t.get("area"):
            areas[t["area"]].append(t)
    if not areas:
        print("  配達先エリアの情報がないため算出できません。")
        print("  → 収集項目に『配達先エリア』を含めると、次の待機場所が決まります。")
        return
    rows = []
    for a, ts in areas.items():
        if len(ts) < 5:
            continue
        mins = sum((t.get("minutes") or t.get("cycle") or 0) for t in ts)
        if mins <= 0:
            continue
        rows.append((a, sum(t["amount"] for t in ts) / mins * 60, len(ts)))
    rows.sort(key=lambda x: -x[1])
    if not rows:
        print("  エリアごとの件数が少なく、判断できません。")
        return
    h2("エリア別の時給（5件以上）")
    for a, hourly, c in rows[:12]:
        print(f"    {a[:24]:<26}{yen(hourly):>10}{c:>6}件")
    h2("結論")
    print(f"  配達後に戻るべきエリア: {rows[0][0]}（{yen(rows[0][1])}/h）")
    if len(rows) > 2:
        print(f"  流れたら損なエリア  : {rows[-1][0]}（{yen(rows[-1][1])}/h）")
        print("  → 下位エリアへの配達を終えたら、その場で待たずに上位エリアへ戻る。")


# ---------------------------------------------------------------- 4. 避ける店

def which_pickups(trips):
    h1("4. 受取先 — どの店を避けるか")
    shops = defaultdict(list)
    for t in trips:
        if t.get("pickup"):
            shops[t["pickup"]].append(t)
    if not shops:
        print("  受取店舗の情報がないため算出できません。")
        print("  → 収集項目に『受取場所』を含めると、待たされて損をしている店が特定できます。")
        return
    rows = []
    for s, ts in shops.items():
        if len(ts) < 3:
            continue
        mins = sum((t.get("minutes") or t.get("cycle") or 0) for t in ts)
        if mins <= 0:
            continue
        waits = [t["wait"] for t in ts if t.get("wait") is not None]
        rows.append((s, sum(t["amount"] for t in ts) / mins * 60, len(ts),
                     statistics.mean(waits) if waits else None))
    if not rows:
        print("  店舗ごとの件数が少なく、判断できません。")
        return
    rows.sort(key=lambda x: x[1])
    h2("時給が低い受取先（3件以上）")
    for s, hourly, c, w in rows[:10]:
        wtxt = f"  平均待ち {w:.0f}分" if w is not None else ""
        print(f"    {s[:28]:<30}{yen(hourly):>10}{c:>5}件{wtxt}")
    h2("結論")
    print(f"  断る候補: {rows[0][0]}（{yen(rows[0][1])}/h）")
    print("  → 同じ店で繰り返し低い時給が出ているなら、その店からの依頼は受けない。")
    print("     店は選べないが、鳴った時点で店名は見える。低単価店 × 長距離は即断る。")


# ---------------------------------------------------------------- まとめ

def action_summary(rule, trips, sessions, online_h):
    h1("まとめ — 明日からやること")
    n = 1
    if rule:
        print(f"  {n}. 受注: {rule['rule']}")
        print("     ただし注文が途切れる時間帯では全部受ける（空き時間の損の方が大きい）")
        n += 1
    print(f"  {n}. 稼働: 上の2節で時給が高い時間帯に寄せる。薄い時間帯から削る")
    n += 1
    print(f"  {n}. 移動: 配達後は時給の高いエリアへ戻る。低いエリアで待たない")
    n += 1
    print(f"  {n}. 記録: 2週間後にもう一度データを取り、この数字が動いたかで効果を測る")
    print("\n  ※ 一度に全部変えないこと。まず受注ルールだけを2週間試し、")
    print("     実効時給が上がったことを確認してから次を足す。")


def main():
    p = argparse.ArgumentParser(description="配達1件ごとの記録から効率化の行動を出す")
    p.add_argument("files", nargs="+")
    p.add_argument("--tz-shift", type=float, default=0.0, help="UTC書き出しなら 9")
    p.add_argument("--gap-min", type=int, default=45, help="別セッションとみなす無注文の分数")
    p.add_argument("--tail-min", type=int, default=20, help="各セッション末尾に加算する分数")
    a = p.parse_args()

    trips, notes = load(a.files, a.tz_shift)
    h1("0. 読み込み")
    for nte in notes:
        print("  " + nte)
    if not trips:
        raise SystemExit("\n有効な配達記録が0件です。README の収集手順を確認してください。")

    sessions = build_sessions(trips, a.gap_min)
    online_h = online_minutes(sessions, a.tail_min) / 60
    total = sum(t["amount"] for t in trips)
    print(f"\n  配達 {len(trips):,} 件 / {trips[0]['dt']:%Y-%m-%d} 〜 {trips[-1]['dt']:%Y-%m-%d}")
    print(f"  稼働 {len(sessions)} 回・{online_h:,.1f} 時間 / 総額 {yen(total)}")
    if online_h:
        print(f"  いまの実効時給 {yen(total / online_h)}/h")

    missing = [k for k, label in (("minutes", "所要時間"), ("km", "距離"),
                                  ("pickup", "受取場所"), ("area", "配達先エリア"))
               if not any(t.get(k) for t in trips)]
    if missing:
        labels = {"minutes": "所要時間", "km": "距離", "pickup": "受取場所", "area": "配達先エリア"}
        print(f"\n  [不足] {'、'.join(labels[m] for m in missing)} が無いため、"
              "対応する節は算出できません。")

    rule = accept_rules(trips, sessions, online_h)
    when_to_work(trips, sessions)
    where_to_wait(trips)
    which_pickups(trips)
    action_summary(rule, trips, sessions, online_h)

    if not a.tz_shift:
        night = sum(1 for t in trips if t["dt"].hour < 6)
        if night > len(trips) * 0.4:
            print("\n[注意] 深夜帯が多すぎます。書き出しがUTCの可能性。--tz-shift 9 で再実行してください。")


if __name__ == "__main__":
    main()
