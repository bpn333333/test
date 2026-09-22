# -*- coding: utf-8 -*-
"""Ver1.5 の5年計画 — 単価を実勢に、本数を営業体制から積み上げる

Ver1.4 からの変更は ① 映像制作だけ。②③ は据え置き。

  単価   60万（見積サイトの相場帯）→ 94.5万（企業の現行支払×50%）  … pricing.py
  本数   SAMの1.5%からの逆算 → アカウント×リピートの積み上げ        … sales.py
  原価   一律20.5万 → 用途ミックスの難度係数を掛ける

結果として ① は 33.6億 → 35.7億。売上はほぼ変わらないが、
本数が 5,594 → 3,780本 に減るため、AX倍率への依存が下がる。

⚠ AX倍率・担当社数・リピート本数・契約数・GMVはすべて［仮置き］。
"""

Y = ["1期", "2期", "3期", "4期", "5期"]
n = 5

# ── ① 映像制作（sales.py / pricing.py から）──────────────
UNITS = [60, 304, 1215, 2543, 3780]
PRICE = [65.0, 75.0, 85.0, 90.0, 94.5]      # 万円。企業の現行支払の50%
DIFF = [1.05, 1.20, 1.38, 1.48, 1.55]       # 用途ミックスの加重難度係数
AX = [1.0, 1.5, 2.2, 3.0, 4.0]
DIRECTION_BASE = 20.0


def cost_unit(ax, diff):
    """1本あたり原価（万円）。難度係数は用途ミックスで決まる"""
    return diff * (12.0 + DIRECTION_BASE / ax + 2.0 + 1.5)


# ── ② ツール外販（据え置き）────────────────────────────
CORP = [0, 15, 100, 320, 600]
CORP_ACV = [0, 250, 280, 300, 320]
INDIE = [0, 0, 2000, 8000, 17000]
INDIE_ACV = 12

# ── ③ 越境C2C（据え置き）──────────────────────────────
GMV = [50, 400, 1600, 4500, 8300]
TAKE = 0.18

# ── 社員（据え置き）────────────────────────────────────
BURDEN = 1.16
ROLE = {"経営・CxO": 900, "モデル開発エンジニア": 850, "制作統括": 650,
        "事業開発・アライアンス": 700, "クリエイターネットワーク統括": 600, "管理・コーポレート": 550}
HEADS = {
    "経営・CxO":                [1, 1,  2,  3,  3],
    "モデル開発エンジニア":       [2, 6, 16, 28, 40],
    "制作統括":                 [1, 2,  3,  3,  3],
    "事業開発・アライアンス":     [1, 2,  4,  5,  6],
    "クリエイターネットワーク統括": [1, 1,  2,  3,  3],
    "管理・コーポレート":         [0, 1,  2,  4,  6],
}
BPO = [0, 10, 120, 450, 1000]
RND = [30, 120, 450, 1000, 1600]
ACQ1 = 0.08      # ①売上に対する獲得費率。代理店手数料を含む
ACQ2 = 0.15
ACQF = [6, 40, 90, 150, 200]

PY_PER_UNIT = 1.0 / 120 + 1.0 / 90
TOOL = [round(CORP[i] * CORP_ACV[i] / 100.0 + INDIE[i] * INDIE_ACV / 100.0) for i in range(n)]
C2C = [round(g * TAKE) for g in GMV]


def calc():
    out = []
    for i in range(n):
        p1 = UNITS[i] * PRICE[i] / 100.0
        rev = p1 + TOOL[i] + C2C[i]
        cu = cost_unit(AX[i], DIFF[i])
        gp = p1 * (1 - cu / PRICE[i]) + TOOL[i] * 0.80 + C2C[i] * 0.85
        heads = sum(HEADS[r][i] for r in ROLE)
        pay = sum(HEADS[r][i] * ROLE[r] * BURDEN for r in ROLE) / 100.0
        acq = p1 * ACQ1 + TOOL[i] * ACQ2 + ACQF[i]
        sga = rev * 0.04
        op = gp - pay - BPO[i] - RND[i] - acq - sga
        ns = TOOL[i] + C2C[i] + p1 * (1 - 1.0 / AX[i])
        out.append(dict(p1=p1, rev=rev, gp=gp, cu=cu, heads=heads, pay=pay, op=op, ns=ns,
                        gig=UNITS[i] * PY_PER_UNIT / AX[i], acq=acq, sga=sga,
                        saving=UNITS[i] * PRICE[i] / 100.0))
    return out


R = calc()


def row(label, vals, f="{:>9,.0f}"):
    print(label.ljust(26) + "".join(f.format(v) for v in vals))


print("=" * 92)
print("Ver1.5 5年計画（単位 百万円）")
print("=" * 92)
row("", Y, "{:>9}")
print("-" * 92)
row("  ① 映像制作", [r["p1"] for r in R])
row("    受注本数", UNITS)
row("    平均単価(万円)", PRICE, "{:>9.1f}")
row("    1本あたり原価(万円)", [r["cu"] for r in R], "{:>9.1f}")
row("    AX倍率", AX, "{:>9.1f}")
row("  ② ツール外販", TOOL)
row("  ③ C2C手数料", C2C)
row("売上高", [r["rev"] for r in R])
print("-" * 92)
row("売上総利益", [r["gp"] for r in R])
row("  粗利率(%)", [r["gp"] / r["rev"] * 100 for r in R], "{:>9.1f}")
row("  人件費（社員）", [r["pay"] for r in R])
row("  研究開発費", RND)
row("  BPO（CS・運用）", BPO)
row("  獲得費", [r["acq"] for r in R])
row("  その他販管費", [r["sga"] for r in R])
row("営業利益", [r["op"] for r in R])
row("  営業利益率(%)", [r["op"] / r["rev"] * 100 for r in R], "{:>9.1f}")
print("-" * 92)
row("★ 社員数", [r["heads"] for r in R])
row("★ 売上/社員(万円)", [r["rev"] * 100 / r["heads"] for r in R])
row("研究開発費 ÷ 売上(%)", [a / r["rev"] * 100 for a, r in zip(RND, R)], "{:>9.1f}")
row("★ 人手に比例しない(%)", [r["ns"] / r["rev"] * 100 for r in R], "{:>9.1f}")
row("業務委託ディレクション", [r["gig"] for r in R])
row("★ 顧客が浮かせる額", [r["saving"] for r in R])
print("=" * 92)
print()

r = R[-1]
print("=" * 92)
print("Ver1.4 との差（5期）")
print("=" * 92)
V14 = dict(p1=3356.4, rev=8810.4, op=2143.5, units=5594, price=60.0, cu=20.5, gig=27.2, ns=90.5)
print("  %-24s %14s %16s" % ("", "Ver1.4", "Ver1.5"))
print("  " + "-" * 58)
print("  %-24s %12s %16s" % ("単価の根拠", "見積サイト相場", "企業の現行支払×50%"))
print("  %-24s %12.1f万 %15.1f万" % ("平均単価", V14["price"], PRICE[-1]))
print("  %-24s %12d本 %15d本" % ("受注本数", V14["units"], UNITS[-1]))
print("  %-24s %12.1f万 %15.1f万" % ("1本あたり原価", V14["cu"], r["cu"]))
print("  %-24s %12.1f億 %15.1f億" % ("① 映像制作", V14["p1"] / 100, r["p1"] / 100))
print("  %-24s %12.1f億 %15.1f億" % ("売上高", V14["rev"] / 100, r["rev"] / 100))
print("  %-24s %12.1f億 %15.1f億" % ("営業利益", V14["op"] / 100, r["op"] / 100))
print("  %-24s %12.1f%% %15.1f%%" % ("営業利益率", V14["op"] / V14["rev"] * 100,
                                     r["op"] / r["rev"] * 100))
print("  %-24s %12.0f名 %15.0f名" % ("業務委託ディレクション", V14["gig"], r["gig"]))
print("  %-24s %12.1f%% %15.1f%%" % ("人手に比例しない", V14["ns"], r["ns"] / r["rev"] * 100))
print("  %-24s %12s %15.0f億" % ("顧客が浮かせる額", "—", r["saving"] / 100))
print()

print("=" * 92)
print("AX倍率を下げても成立するか（5期）")
print("=" * 92)
print("  AX倍率   ディレクション費/本   1本あたり原価   制作粗利率   営業利益   営業利益率")
print("  " + "-" * 74)
for k in [1.0, 2.0, 3.0, 4.0]:
    cu = cost_unit(k, DIFF[-1])
    gp = r["p1"] * (1 - cu / PRICE[-1]) + TOOL[-1] * 0.80 + C2C[-1] * 0.85
    op = gp - r["pay"] - BPO[-1] - RND[-1] - r["acq"] - r["sga"]
    mk = "  ←計画" if k == 4.0 else ("  ←ここでも成立" if k == 3.0 else "")
    print("  %.1f倍    %8.1f万          %7.1f万     %5.1f%%   %+8.0f百万   %6.1f%%%s"
          % (k, DIRECTION_BASE / k * DIFF[-1], cu, (1 - cu / PRICE[-1]) * 100,
             op, op / r["rev"] * 100, mk))
print()

print("=" * 92)
print("時価総額とシードのリターン")
print("=" * 92)
print("  人手に比例しない収益 %.0f%%" % (r["ns"] / r["rev"] * 100))
for ps, pc, pp in [(6, 4, 1.5), (7, 5, 2.0), (8, 6, 2.5)]:
    v = TOOL[-1] * ps + C2C[-1] * pc + r["p1"] * pp
    print("     ツール%d倍+C2C%d倍+制作%.1f倍 = %6.1f億   シード %4.1f倍"
          % (ps, pc, pp, v / 100.0, v * 0.1453 / 142))
for psr in [4, 5]:
    v = r["rev"] * psr
    print("     全社PSR%d倍                  = %6.1f億   シード %4.1f倍" % (psr, v / 100.0, v * 0.1453 / 142))
