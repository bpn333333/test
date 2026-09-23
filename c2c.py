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
print("  以降、すべての商品で「最悪ケース（価格は下限・時間は上限）でも時給がこの線を超えるか」を見る。")
print()

TAKE_PKG = 0.20
TAKE_CUSTOM = 0.15
TARGET_HOURLY = 1600            # ★設計に使う時給（判断ラインに少し余裕を見る）


def floor_price(hours_max, take):
    """所要時間の上限でも時給を確保できる、発注額の下限"""
    return TARGET_HOURLY * hours_max / (1 - take)


def block(title, items, take, note=""):
    print("=" * 100)
    print(title + "（手数料率 %.0f%%）" % (take * 100))
    print("=" * 100)
    print("  %-22s %8s %16s %10s %10s %10s %8s"
          % ("商品", "所要時間", "価格帯", "下限の受取", "下限の時給", "★上限", "判定"))
    print("  " + "-" * 92)
    out = []
    for name, hmin, hmax, pmax, cnt, why in items:
        pmin = round(floor_price(hmax, take) / 1000) * 1000
        recv = pmin * (1 - take)
        hourly = recv / hmax
        ok = "○" if hourly >= floor_hourly else "×"
        print("  %-22s %3.0f〜%3.0fh %7s〜%7s円 %9s円 %9s円 %9s円 %6s"
              % (name, hmin, hmax, f"{pmin:,}", f"{pmax:,}", f"{recv:,.0f}",
                 f"{hourly:,.0f}", f"{pmax:,}", ok))
        out.append((name, pmin, pmax, cnt, hmin, hmax, why))
    print()
    if note:
        print("  " + note)
        print()
    return out


# (商品, 所要時間min, max, ★価格上限, 5期件数, 考え方)
A = [
    ("SNS用ショート",        0.5, 1.5,   10000, 25000, "縦型15〜30秒。尺と本数で振れる"),
    ("誕生日ムービー",        1.0, 2.5,   15000, 12000, "写真点数と尺で振れる"),
    ("記念日ムービー",        1.0, 3.0,   18000,  8000, "還暦・退職は構成が重くなる"),
    ("イベント・余興ムービー",  2.0, 5.0,   30000, 10000, "出演者数・編集点で振れる"),
    ("WEBサイト用",          3.0, 8.0,   50000,  6000, "ページ構成に合わせるぶん重い"),
    ("ウェディングムービー",    5.0, 15.0,  80000,  9000, "3本立て。最も重く、最も値段が付く"),
]
B = [
    ("会社紹介ショート",       6.0, 12.0, 120000,  4000, "仕様固定。①の企業VP50万の下"),
    ("採用（小規模・1職種）",   8.0, 16.0, 180000,  2500, "社員インタビュー1〜2名"),
    ("商品・サービス紹介",     6.0, 14.0, 150000,  5000, "機能数で振れる"),
    ("店舗・施設紹介",        5.0, 10.0, 100000,  3500, "撮影なし・生成のみ"),
    ("展示会・イベント告知",    4.0,  9.0,  80000,  2000, "ループ素材。最も軽い"),
    ("SNS広告用（縦型3本）",   6.0, 12.0, 120000,  6000, "3本セット。1本あたりは安い"),
]
C = [
    ("個人オーダーメイド",     3.0, 10.0, 150000,  8000, "パッケージに収まらない個別要望"),
    ("企業オーダーメイド",    10.0, 50.0, 1000000, 12000, "上限100万［Ver1.2の決定］"),
]

RA = block("③-A 個人向けパッケージ", A, TAKE_PKG,
           "※ ウェディングの下限が30,000円になるのは、3本立てで最大15時間かかるため。\n"
           "     ここを25,000円に置くと時給1,333円で、中国のクリエイターは受けない。")
RB = block("③-B 中小企業向けパッケージ（★内容は私の提案）", B, TAKE_PKG,
           "※ 上限は①の最安（展示会30万）を超えないように 18万で止めた。")
RC = block("③-C オーダーメイド（AI-botが仲介）", C, TAKE_CUSTOM,
           "※ 手数料15%なので、同じ時給でも下限は少し下がる。\n"
           "     企業オーダーメイドは幅が最も広い。10時間なら19,000円、50時間なら94,000円が下限。")

# ── 価格帯のどこに落ちるか ────────────────────────────
# ★下限寄り60% / 中位30% / 上限寄り10% の分布を仮定する
W = [(0.60, 0.15), (0.30, 0.50), (0.10, 0.85)]   # (構成比, 価格帯の中での位置)


def expected(pmin, pmax):
    return sum(w * (pmin + (pmax - pmin) * pos) for w, pos in W)


print("=" * 100)
print("価格帯のどこに落ちるか（★下限寄り60%／中位30%／上限寄り10%と仮定）")
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
ent_g = [p for n, pmin, pmax, cnt, hmin, hmax, why in RC if n == "企業オーダーメイド"]
e = expected(94000, 1000000)
print("  1 企業オーダーメイド1商品で、5期GMVの %.0f%%（%.0f億）を占める。"
      % (e * 12000 / 1e6 / gmv5 * 100, e * 12000 / 1e8))
print("    価格帯が 94,000〜1,000,000円 と最も広く、期待値 %s円 の置き方で全体が動く。"
      % f"{e:,.0f}")
print("    ここだけ下限に張り付くと ③売上は %.1f億 減る。" % ((e - 94000) * 12000 / 1e6 * 0.15 / 100))
print()
print("  2 その期待単価 %s円 は、① の最安（展示会 30万）を上回っている。"
      % f"{e:,.0f}")
print("    「①は当社が品質を保証する／③は発注者が自分でやり取りする」で線を引いているが、")
print("    実際には食い合う。①側の件数を削るか、③-Cの上限を下げるかの判断が要る。")
print()
print("  3 年間 %s件（月 %s件）。うち企業オーダーメイドが %s件（月 %s件）。"
      % (f"{int(cnt5):,}", f"{int(cnt5 / 12):,}", "12,000", "1,000"))
print("    発注者が自分で中国のクリエイターと要件を詰める取引が月1,000件。ここは検証が要る。")
