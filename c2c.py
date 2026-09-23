# -*- coding: utf-8 -*-
"""事業③ 越境C2C — 単価に幅を持たせ、クリエイター側から下限を決める

値付けの順序を変えた。
  旧: 日本の相場から単価を1つ決める → 件数を掛ける
  新: **中国のクリエイターがその仕事を受けるか** から下限を出す → 幅を持たせる

マーケットプレイスは、供給側が受けてくれなければ1件も成立しない。
だから拘束条件はクリエイター側にある。

  クリエイター受取 ＝ 発注額 × (1 − 手数料率)
  実効時給        ＝ 受取 ÷ 所要時間
  これが中国の実勢を上回らないと、誰も受けない。

出所
  中国の剪辑師（映像編集者）平均月給 8,935元 … Indeed 中国
  為替 1元＝21円［仮置き］

★ 所要時間・価格帯の上限・件数は私が置いた値。
⚠ Ver1.2の一本値（GMV83億・平均9万）には寄せない。積み上げた結果をそのまま出す。
"""

RMB = 21.0                      # 円/元［仮置き］
CN_MONTHLY_RMB = 8935.0         # 元/月。中国の剪辑師 平均月給（Indeed中国）
CN_HOURS = 168.0                # 月あたり労働時間（21日×8h）
FREELANCE = 1.4                 # ★フリーランス割増（社保・不安定性・営業時間の補償）

cn_hourly = CN_MONTHLY_RMB * RMB / CN_HOURS
floor_hourly = cn_hourly * FREELANCE

print("=" * 100)
print("まず、クリエイターがいくらなら受けるか")
print("=" * 100)
print("  中国の剪辑師 平均月給 %s元 × %.0f円 = 月 %s円" % (f"{CN_MONTHLY_RMB:,.0f}", RMB,
                                                  f"{CN_MONTHLY_RMB * RMB:,.0f}"))
print("  月%.0f時間で割ると 時給 %s円（雇用ベース）" % (CN_HOURS, f"{cn_hourly:,.0f}"))
print("  フリーランス割増 ×%.1f  →  **受注の判断ライン 時給 %s円**".replace("**", "")
      % (FREELANCE, f"{floor_hourly:,.0f}"))
print()
print("  ③は1人のクリエイターが完結する仕事なので、発注額はこの時給に工数を掛けたものになる。")
print("  価格の幅＝「工数の幅 × 時給の幅（新人1,600円〜熟練3,500円）」。")
print()

TAKE_PKG = 0.20
TAKE_CUSTOM = 0.15

# ③は「1人のクリエイターが完結する」仕事（松田さんの定義）。
# だから価格は工数に連動する。単純な案件＝短時間＝安い、複雑な案件＝長時間＝高い。
# 時給にも幅がある。新人は判断ラインぎりぎり、熟練は上位の月収水準。
HOURLY_LO = 1600      # 円。受注判断ライン（平均月給8,935元＋フリーランス割増）に余裕を見た額
HOURLY_HI = 3500      # ★熟練クリエイター。月20,000元相当×フリーランス割増


def price_range(hmin, hmax, take):
    """価格帯 ＝ 1人のクリエイターの工賃 ÷ (1 − 手数料率)
       下限: 単純な案件を新人が受ける    上限: 複雑な案件を熟練が受ける"""
    lo = HOURLY_LO * hmin / (1 - take)
    hi = HOURLY_HI * hmax / (1 - take)
    return round(lo / 500) * 500, round(hi / 500) * 500


def block(title, items, take, note=""):
    print("=" * 100)
    print(title + "（手数料率 %.0f%%・1人のクリエイターが完結）" % (take * 100))
    print("=" * 100)
    print("  %-22s %9s %18s %12s %10s"
          % ("商品", "所要時間", "価格帯", "クリエイター受取", "実効時給"))
    print("  " + "-" * 82)
    out = []
    for name, hmin, hmax, cnt, why in items:
        lo, hi = price_range(hmin, hmax, take)
        rl, rh = lo * (1 - take), hi * (1 - take)
        print("  %-22s %3.1f〜%4.1fh %8s〜%8s円 %6s〜%7s円 %5s〜%5s円"
              % (name, hmin, hmax, f"{lo:,}", f"{hi:,}",
                 f"{rl:,.0f}", f"{rh:,.0f}",
                 f"{rl / hmin:,.0f}", f"{rh / hmax:,.0f}"))
        out.append((name, lo, hi, cnt, hmin, hmax, why))
    print()
    if note:
        print("  " + note)
        print()
    return out


# (商品, 所要時間min, max, ★価格上限, 5期件数, 考え方)
A = [
    ("SNS用ショート",        0.5, 1.5,  25000, "縦型15〜30秒"),
    ("誕生日ムービー",        1.0, 2.5,  12000, "写真点数と尺で振れる"),
    ("記念日ムービー",        1.0, 3.0,   8000, "還暦・退職は構成が重くなる"),
    ("イベント・余興ムービー",  2.0, 5.0,  10000, "出演者数・編集点で振れる"),
    ("WEBサイト用",          3.0, 8.0,   6000, "ページ構成に合わせるぶん重い"),
    ("ウェディングムービー",    5.0, 15.0,  9000, "3本立て。最も重い"),
]
B = [   # 中身は①と同じ。違いは「③は1人・①は複数スタック」
    ("会社紹介ショート",       6.0, 12.0,  4000, "①の企業VPと同じ内容を1人で作る"),
    ("採用（小規模・1職種）",   8.0, 16.0,  2500, "①の採用と同じ内容を1人で作る"),
    ("商品・サービス紹介",     6.0, 14.0,  5000, "機能数で振れる"),
    ("店舗・施設紹介",        5.0, 10.0,  3500, "撮影なし・生成のみ"),
    ("展示会・イベント告知",    4.0,  9.0,  2000, "①の展示会と同じ内容を1人で作る"),
    ("SNS広告用（縦型3本）",   6.0, 12.0,  6000, "3本セット"),
]
C = [
    ("個人オーダーメイド",     3.0, 10.0,  8000, "パッケージに収まらない個別要望"),
    ("企業オーダーメイド",    10.0, 50.0, 12000, "上限は Ver1.2 の100万に収まるか下で確認"),
]

RA = block("③-A 個人向けパッケージ", A, TAKE_PKG,
           "※ 価格の幅は「工数の幅 × 時給の幅」。上限は複雑な案件を熟練が受けたとき。")
RB = block("③-B 中小企業向けパッケージ（内容は①と同じ）", B, TAKE_PKG,
           "※ 松田さんの定義: ①との違いは中身ではなく体制。③は1人、①は複数スタック。"
           "同じ「会社紹介」でも、人数が違えば価格が変わる。")
RC = block("③-C オーダーメイド（AI-botが仲介）", C, TAKE_CUSTOM,
           "※ 上限は Ver1.2 の100万に収まり、①の最安30万も下回る。"
           "工数連動にした結果、①との食い合いは自然に解消した。")

# ── 価格帯のどこに落ちるか ────────────────────────────
# ★下限寄り60% / 中位30% / 上限寄り10% の分布を仮定する
W = [(0.60, 0.15), (0.30, 0.50), (0.10, 0.85)]   # (構成比, 価格帯の中での位置)


def expected(pmin, pmax):
    return sum(w * (pmin + (pmax - pmin) * pos) for w, pos in W)


print("=" * 100)
print("価格帯のどこに落ちるか（★単純な案件が多いので下限寄り60%／中位30%／上限寄り10%）")
print("=" * 100)
print("  %-22s %10s %10s %12s %10s %14s"
      % ("商品", "下限", "上限", "期待単価", "5期件数", "5期GMV(百万)"))
print("  " + "-" * 84)
tot = {}
for label, rows, take in [("A", RA, TAKE_PKG), ("B", RB, TAKE_PKG), ("C", RC, TAKE_CUSTOM)]:
    g = c = 0
    for name, pmin, pmax, cnt, hmin, hmax, why in rows:
        e = expected(pmin, pmax)
        gm = e * cnt / 1e6
        g += gm
        c += cnt
        print("  %-22s %9s円 %9s円 %11s円 %9s件 %13.0f"
              % (name, f"{pmin:,}", f"{pmax:,}", f"{e:,.0f}", f"{cnt:,}", gm))
    tot[label] = (g, c, take)
    print("  %-22s %31s %11s円 %9s件 %13.0f"
          % ("  小計 " + label, "", f"{g * 1e6 / c:,.0f}", f"{c:,}", g))
    print()

gmv5 = sum(v[0] for v in tot.values())
cnt5 = sum(v[1] for v in tot.values())
rev5 = sum(v[0] * v[2] for v in tot.values())
print("  " + "=" * 84)
print("  %-22s %31s %11s円 %9s件 %13.0f"
      % ("③ 合計（5期）", "", f"{gmv5 * 1e6 / cnt5:,.0f}", f"{cnt5:,}", gmv5))
print("  %-22s 実効手数料率 %.1f%%  →  ③ 売上 %.1f億"
      % ("", rev5 / gmv5 * 100, rev5 / 100))
print()

print("=" * 100)
print("幅で見たときの③（5期）")
print("=" * 100)
for tag, pos in [("全部が下限", 0.0), ("期待値", None), ("全部が上限", 1.0)]:
    g = r = 0
    for label, rows, take in [("A", RA, TAKE_PKG), ("B", RB, TAKE_PKG), ("C", RC, TAKE_CUSTOM)]:
        for name, pmin, pmax, cnt, hmin, hmax, why in rows:
            p = expected(pmin, pmax) if pos is None else pmin + (pmax - pmin) * pos
            g += p * cnt / 1e6
            r += p * cnt / 1e6 * take
    print("  %-12s GMV %6.1f億   ③売上 %5.1f億   平均単価 %8s円"
          % (tag, g / 100, r / 100, f"{g * 1e6 / cnt5:,.0f}"))
print()
print("  → 下限は「クリエイターが受ける最低ライン」なので、これを割ると供給が付かない。")
print("     上限は日本の発注者が払う気になる上限。実際はこの間に散る。")

# ── 期別（★立ち上がりカーブ）────────────────────────────
RAMP = {"A": [0.01, 0.07, 0.28, 0.62, 1.00],    # 1期から。仲介が要らない
        "B": [0.00, 0.04, 0.22, 0.58, 1.00],    # 2期から
        "C": [0.00, 0.00, 0.15, 0.55, 1.00]}    # 3期から。AI-botの開発後
CANNIB_A = [0.00, 0.0375, 0.18, 0.49, 1.00]     # ②-Cセルフサーブの立ち上がり（selfserve.py）
CANNIB_5 = 0.18                                  # ③-Aの件数のうち共食いする割合（SKU別の加重）

print()
print("=" * 100)
print("期別（②-C セルフサーブの共食いを差し引いた後）")
print("=" * 100)
Y = ["1期", "2期", "3期", "4期", "5期"]
gA5, cA5, _ = tot["A"]; gB5, cB5, _ = tot["B"]; gC5, cC5, _ = tot["C"]
gmv_y, rev_y, cnt_y = [], [], []
for i in range(5):
    a = gA5 * RAMP["A"][i] * (1 - CANNIB_5 * CANNIB_A[i])
    b = gB5 * RAMP["B"][i]
    c = gC5 * RAMP["C"][i]
    gmv_y.append(a + b + c)
    rev_y.append((a + b) * TAKE_PKG + c * TAKE_CUSTOM)
    cnt_y.append(cA5 * RAMP["A"][i] * (1 - CANNIB_5 * CANNIB_A[i])
                 + cB5 * RAMP["B"][i] + cC5 * RAMP["C"][i])
def r2(lab, v, f="{:>11,.0f}"):
    print(lab.ljust(26) + "".join(f.format(x) for x in v))
r2("", Y, "{:>11}")
print("-" * 100)
r2("GMV（百万円）", gmv_y)
r2("取引件数", cnt_y)
r2("平均単価（円）", [g * 1e6 / c if c else 0 for g, c in zip(gmv_y, cnt_y)])
r2("③ 売上（百万円）", rev_y)
r2("  実効手数料率(%)", [r / g * 100 if g else 0 for r, g in zip(rev_y, gmv_y)], "{:>11.1f}")
print("=" * 100)
print()
print("  plan用: GMV = %s" % [round(x) for x in gmv_y])
print("  plan用: C2C = %s" % [round(x) for x in rev_y])
print()
print("=" * 100)
print("⚠ この積み上げの弱点")
print("=" * 100)
ent = [r for r in RC if r[0] == "企業オーダーメイド"][0]
elo, ehi, ecnt = ent[1], ent[2], ent[3]
e = expected(elo, ehi)
print("  1 企業オーダーメイド1商品で、5期GMVの %.0f%%（%.1f億）。価格帯 %s〜%s円、期待単価 %s円。"
      % (e * ecnt / 1e6 / gmv5 * 100, e * ecnt / 1e8, f"{elo:,}", f"{ehi:,}", f"{e:,.0f}"))
print("    下限に張り付くと ③売上は %.2f億 減る。" % ((e - elo) * ecnt / 1e6 * TAKE_CUSTOM / 100))
print()
print("  2 工数連動にしたことで、③の最高額（%s円）が ① の最安（30万）を下回った。"
      % f"{ehi:,}")
print("    前回指摘した①との食い合いは、値付けの筋を直した結果として消えた。")
print()
print("  3 年間 %s件（月 %s件）。1人のクリエイターが完結する前提なので、"
      % (f"{int(cnt5):,}", f"{int(cnt5 / 12):,}"))
print("    必要なクリエイター数がそのまま制約になる。下で確認する。")
print()
tot_h = 0
for label, rows in [("A", RA), ("B", RB), ("C", RC)]:
    for name, lo, hi, cnt, hmin, hmax, why in rows:
        tot_h += cnt * (hmin + hmax) / 2
print("  必要な稼働時間 年 %s時間 ÷ 1人あたり年1,800時間 = **稼働クリエイター %s人**"
      .replace("**", "") % (f"{tot_h:,.0f}", f"{tot_h / 1800:,.0f}"))
print("  登録はその2〜3倍が要る（全員が常時稼働はしない）。%s〜%s人規模。"
      % (f"{tot_h / 1800 * 2:,.0f}", f"{tot_h / 1800 * 3:,.0f}"))
print()
print("  ① の分も足すと、中国側のクリエイター網はさらに大きくなる。")
print("  **ここが③の本当の制約。単価でも件数でもなく、人が集まるか。**".replace("**", ""))
