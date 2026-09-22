# -*- coding: utf-8 -*-
"""Ver1.4 の5年計画 — B案（制作を半分に、ツールとC2Cを伸ばす）・強気

Ver1.3 からの変更
  ① 制作      67.1億 → 33.6億（SAM 3% → 1.5%。本数 11,189 → 5,594）
  ② ツール外販 10.5億 → 40.0億（国内だけでなく海外へ）
  ③ C2C       4.9億 → 15.0億（GMV 27億 → 83億）

これで「人手に比例しない収益」が 80% → 90% になり、
制作本数が半分になるぶん AX倍率の前提も軽くなる（4倍計画／3倍でも到達）。

⚠ AX倍率・本数カーブ・契約数・研究開発費はすべて［仮置き］。
"""

Y = ["1期", "2期", "3期", "4期", "5期"]
n = 5

# ── ① 映像制作 ─────────────────────────────────────────
UNITS = [54, 350, 1200, 2800, 5594]
PRICE = [50, 55, 60, 60, 60]
AX = [1.0, 1.5, 2.2, 3.0, 4.0]
DIRECTION_BASE = 20.0


def cost_unit(ax):
    return {"中国クリエイターへの支払": 12.0,
            "制作ディレクション（業務委託）": DIRECTION_BASE / ax,
            "AIツール・素材・レンダリング": 2.0,
            "品質バッファ（作り直し）": 1.5}


# ── ② ツール外販 ───────────────────────────────────────
CORP = [0, 15, 100, 320, 600]          # 法人契約数
CORP_ACV = [0, 250, 280, 300, 320]     # 万円/年
INDIE = [0, 0, 2000, 8000, 17000]      # 個人契約数
INDIE_ACV = 12

# ── ③ 越境C2C ─────────────────────────────────────────
GMV = [50, 400, 1600, 4500, 8300]      # 百万円
TAKE = 0.18

# ── 社員（極小）─────────────────────────────────────────
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

PY_PER_UNIT = 1.0 / 120 + 1.0 / 90

TOOL = [round(CORP[i] * CORP_ACV[i] / 100.0 + INDIE[i] * INDIE_ACV / 100.0) for i in range(n)]
C2C = [round(g * TAKE) for g in GMV]


def calc():
    out = []
    for i in range(n):
        p1 = UNITS[i] * PRICE[i] / 100.0
        rev = p1 + TOOL[i] + C2C[i]
        cu = sum(cost_unit(AX[i]).values())
        gp = p1 * (1 - cu / PRICE[i]) + TOOL[i] * 0.80 + C2C[i] * 0.85
        heads = sum(HEADS[r][i] for r in ROLE)
        pay = sum(HEADS[r][i] * ROLE[r] * BURDEN for r in ROLE) / 100.0
        acq = p1 * 0.06 + TOOL[i] * 0.15 + [6, 40, 90, 150, 200][i]
        sga = rev * 0.04
        op = gp - pay - BPO[i] - RND[i] - acq - sga
        ns = TOOL[i] + C2C[i] + p1 * (1 - 1.0 / AX[i])
        out.append(dict(p1=p1, rev=rev, gp=gp, cu=cu, heads=heads, pay=pay, op=op, ns=ns,
                        gig=UNITS[i] * PY_PER_UNIT / AX[i], acq=acq, sga=sga))
    return out


R = calc()


def row(label, vals, f="{:>9,.0f}"):
    print(label.ljust(26) + "".join(f.format(v) for v in vals))


print("=" * 92)
print("Ver1.4 5年計画（B案・強気／単位 百万円）")
print("=" * 92)
row("", Y, "{:>9}")
print("-" * 92)
row("  ① 映像制作", [r["p1"] for r in R])
row("    受注本数", UNITS)
row("    AX倍率", AX, "{:>9.1f}")
row("  ② ツール外販", TOOL)
row("    法人契約数", CORP)
row("    個人契約数", INDIE)
row("  ③ C2C手数料", C2C)
row("    参考 GMV", GMV)
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
row("参考 業務委託ディレクション", [r["gig"] for r in R])
print("=" * 92)
print()

r = R[-1]
print("=" * 92)
print("AX倍率が3倍でも届きます（本数が半分になったため）")
print("=" * 92)
print("  AX倍率   ディレクション費/本   1本あたり原価   粗利率(制作)   5期の営業利益   営業利益率")
print("  " + "-" * 76)
for k in [1.0, 2.0, 3.0, 4.0]:
    cu = sum(cost_unit(k).values())
    gp = r["p1"] * (1 - cu / 60.0) + TOOL[-1] * 0.80 + C2C[-1] * 0.85
    op = gp - r["pay"] - BPO[-1] - RND[-1] - r["acq"] - r["sga"]
    mk = "  ←計画" if k == 4.0 else ("  ←ここでも成立" if k == 3.0 else "")
    print("  %.1f倍    %8.1f万          %7.1f万      %5.1f%%      %+8.0f百万   %6.1f%%%s"
          % (k, DIRECTION_BASE / k, cu, (1 - cu / 60.0) * 100, op, op / r["rev"] * 100, mk))
print()

print("=" * 92)
print("実在企業と並べる（5期）")
print("=" * 92)
BENCH = [("東映", 1853), ("IMAGICA GROUP(推計)", 1000), ("東映アニメーション", 937),
         ("AOI TYO Holdings", 511), ("東北新社", 477), ("HeyGen (ARR)", 300),
         ("Synthesia (ARR)", 210), ("IG Port", 141)]
rows = BENCH + [("【当社 5期】", r["rev"] / 100)]
for nm, v in sorted(rows, key=lambda x: -x[1]):
    mk = "  ◀" if nm.startswith("【") else ""
    print("  %-22s %7.0f億%s" % (nm, v, mk))
print()
print("  ① 制作 %.1f億 は 東北新社477億の %.0f%%（前案は14%%）" % (r["p1"] / 100, r["p1"] / 100 / 477 * 100))
print("  ② ツール %.1f億 は Synthesia 210億の %.0f%%（前案は5%%）" % (TOOL[-1] / 100, TOOL[-1] / 100 / 210 * 100))
print()

print("=" * 92)
print("時価総額とシードのリターン")
print("=" * 92)
print("  人手に比例しない収益 %.0f%%" % (r["ns"] / r["rev"] * 100))
for ps, pc, pp in [(6, 4, 1.5), (7, 5, 2.0), (8, 6, 2.5)]:
    v = TOOL[-1] * ps + C2C[-1] * pc + r["p1"] * pp
    print("     ツール%d倍+C2C%d倍+制作%.1f倍 = %6.1f億   シード %4.1f倍"
          % (ps, pc, pp, v / 100.0, v * 0.145 / 142))
for psr in [4, 5]:
    v = r["rev"] * psr
    print("     全社PSR%d倍                  = %6.1f億   シード %4.1f倍" % (psr, v / 100.0, v * 0.145 / 142))
