# -*- coding: utf-8 -*-
"""Ver1.3 の5年計画 — 社員は極小。制作は業務委託と自動化で回す

構造を組み替えた。
  社員      経営・モデル開発エンジニア・各機能の統括・管理のみ
  業務委託  制作ディレクション（一次レビュー）／中国クリエイター → 1本あたりの原価
  外部      CS・オペレーション（BPO）／代理店チャネル → 販管費・獲得費

⚠ AX倍率・本数カーブ・研究開発費・業務委託単価はすべて［仮置き］。
"""

Y = ["1期", "2期", "3期", "4期", "5期"]
n = 5

# ── ① 映像制作 ─────────────────────────────────────────
UNITS = [54, 400, 1800, 5000, 11189]
PRICE = [50, 55, 60, 60, 60]
AX = [1.0, 1.5, 2.2, 3.0, 4.0]

# 1本あたりの原価（万円）— 社員ではなく業務委託と外注で積む
# ★AXは「人数」ではなく「1本あたりのディレクション時間」に効く。
#   業務委託は成果物単位の支払なので、時間が1/4になれば単価も1/4になる。
DIRECTION_BASE = 20.0                       # AXなしのディレクション費（8時間相当）
def cost_unit(ax):
    return {
        "中国クリエイターへの支払": 12.0,
        "制作ディレクション（業務委託）": DIRECTION_BASE / ax,
        "AIツール・素材・レンダリング": 2.0,
        "品質バッファ（作り直し）": 1.5,
    }
COST = cost_unit(4.0)
COST_U = sum(COST.values())

TOOL = [0, 20, 160, 504, 1052]
C2C = [9, 54, 162, 324, 486]

# ── 社員（極小）─────────────────────────────────────────
BURDEN = 1.16
ROLE = {"経営・CxO":900, "モデル開発エンジニア":850, "制作統括":650,
        "事業開発・アライアンス":700, "クリエイターネットワーク統括":600, "管理・コーポレート":550}
HEADS = {
    "経営・CxO":                [1, 1,  2,  3,  3],
    "モデル開発エンジニア":       [2, 5, 12, 22, 34],
    "制作統括":                 [1, 2,  3,  4,  4],
    "事業開発・アライアンス":     [1, 2,  3,  4,  4],
    "クリエイターネットワーク統括": [1, 1,  2,  3,  3],
    "管理・コーポレート":         [0, 1,  2,  4,  6],
}
# 業務委託・外部（社員ではない）
BPO = [0, 8, 90, 350, 800]        # CS・オペレーションのBPO費（百万円）［仮置き］
RND = [30, 90, 350, 800, 1300]    # 研究開発費（GPU・ライセンス・データ基盤）

PY_PER_UNIT = 1.0 / 120 + 1.0 / 90   # 従来の1本あたり人年（AXなし）


def calc():
    out = []
    for i in range(n):
        p1 = UNITS[i] * PRICE[i] / 100.0
        rev = p1 + TOOL[i] + C2C[i]
        cu = sum(cost_unit(AX[i]).values())
        gp = p1 * (1 - cu / PRICE[i]) + TOOL[i] * 0.80 + C2C[i] * 0.85
        heads = sum(HEADS[r][i] for r in ROLE)
        pay = sum(HEADS[r][i] * ROLE[r] * BURDEN for r in ROLE) / 100.0
        acq = p1 * 0.06 + TOOL[i] * 0.15 + [6, 30, 60, 100, 140][i]
        sga = rev * 0.04
        op = gp - pay - BPO[i] - acq - sga - RND[i]
        # 業務委託の制作ディレクション人数（参考。AXで割る）
        gig = UNITS[i] * PY_PER_UNIT / AX[i]
        ns = TOOL[i] + C2C[i] + p1 * (1 - 1.0 / AX[i])
        out.append(dict(p1=p1, rev=rev, gp=gp, heads=heads, pay=pay, op=op, gig=gig,
                        acq=acq, sga=sga, ns=ns, cu=cu))
    return out


R = calc()


def row(label, vals, f="{:>9,.0f}"):
    print(label.ljust(26) + "".join(f.format(v) for v in vals))


print("=" * 90)
print("1本あたりの原価 — 社員ではなく業務委託で積む")
print("=" * 90)
for k, v in COST.items():
    print("  %-30s %5.1f万" % (k, v))
print("  %-30s %5.1f万   （単価60万に対して粗利率 %.0f%%）" % ("合計", COST_U, (1 - COST_U / 60) * 100))
print()

print("=" * 90)
print("Ver1.3 5年計画（単位 百万円）")
print("=" * 90)
row("", Y, "{:>9}")
print("-" * 90)
row("  ① 映像制作", [r["p1"] for r in R])
row("    受注本数", UNITS)
row("    AX倍率", AX, "{:>9.1f}")
row("  ② ツール外販", TOOL)
row("  ③ C2C手数料", C2C)
row("売上高", [r["rev"] for r in R])
print("-" * 90)
row("売上総利益", [r["gp"] for r in R])
row("  粗利率(%)", [r["gp"]/r["rev"]*100 for r in R], "{:>9.1f}")
row("  1本あたり原価(万)", [r["cu"] for r in R], "{:>9.1f}")
row("  人件費（社員）", [r["pay"] for r in R])
row("  BPO（CS・運用）", BPO)
row("  研究開発費", RND)
row("  獲得費", [r["acq"] for r in R])
row("  その他販管費", [r["sga"] for r in R])
row("営業利益", [r["op"] for r in R])
row("  営業利益率(%)", [r["op"] / r["rev"] * 100 for r in R], "{:>9.1f}")
print("-" * 90)
row("★ 社員数", [r["heads"] for r in R])
row("  社員1人あたり人件費(万)", [r["pay"] * 100 / r["heads"] for r in R])
row("★ 売上/社員(万円)", [r["rev"] * 100 / r["heads"] for r in R])
row("参考: 業務委託ディレクション", [r["gig"] for r in R])
row("参考: 中国クリエイター(稼働)", [u / (36 * a) for u, a in zip(UNITS, AX)])
row("人手に比例しない(%)", [r["ns"] / r["rev"] * 100 for r in R], "{:>9.1f}")
print("=" * 90)
print()

print("=" * 90)
print("AXは、1本あたりの原価に効きます")
print("=" * 90)
print("  業務委託は成果物単位の支払なので、ディレクション時間が1/4になれば単価も1/4になります。")
print()
print("  AX倍率   ディレクション費/本   1本あたり原価   粗利率   5期の営業利益   営業利益率")
print("  " + "-" * 74)
r5 = R[-1]
for k in [1.0, 2.0, 3.0, 4.0]:
    cu = sum(cost_unit(k).values())
    gp = r5["p1"] * (1 - cu / 60.0) + TOOL[-1] * 0.80 + C2C[-1] * 0.85
    op = gp - r5["pay"] - BPO[-1] - RND[-1] - r5["acq"] - r5["sga"]
    mark = "  ←採用" if k == 4.0 else ""
    print("  %.1f倍    %8.1f万          %7.1f万     %5.1f%%   %+8.0f百万   %6.1f%%%s"
          % (k, DIRECTION_BASE / k, cu, (1 - cu / 60.0) * 100, op, op / r5["rev"] * 100, mark))
print()
cu1 = sum(cost_unit(1.0).values())
gp1 = r5["p1"] * (1 - cu1 / 60.0) + TOOL[-1] * 0.80 + C2C[-1] * 0.85
op1 = gp1 - r5["pay"] - BPO[-1] - RND[-1] - r5["acq"] - r5["sga"]
print("  → AXなしなら営業利益率 %.1f%%。AX4倍で %.1f%%。売上は同じ %.1f億です。"
      % (op1 / r5["rev"] * 100, r5["op"] / r5["rev"] * 100, r5["rev"] / 100))
print("     AXは原価を下げる装置であり、そこで浮いた分を研究開発（5期 %d百万）へ戻しています。" % RND[-1])
print()
print("  ＜社員の平均単価について＞")
print("  安い職種（ディレクター・CS）が社外に出るので、社員の平均単価は上がります。")
print("  1期 %.0f万 → 5期 %.0f万。ただし社員数は %d名、総人件費は %.0f百万に収まります。"
      % (R[0]["pay"] * 100 / R[0]["heads"], r5["pay"] * 100 / r5["heads"], r5["heads"], r5["pay"]))
print()

print("=" * 90)
print("時価総額とシードのリターン（5期）")
print("=" * 90)
r = R[-1]
print("  売上 %.1f億 ／ 営業利益 %.1f億（%.1f%%）／ 社員 %d名 ／ 売上/社員 %.2f億"
      % (r["rev"] / 100, r["op"] / 100, r["op"] / r["rev"] * 100, r["heads"], r["rev"] / r["heads"] / 100))
for psr in [3, 4, 5]:
    v = r["rev"] * psr
    print("     全社PSR%d倍 = %6.1f億   シード %4.1f倍" % (psr, v / 100.0, v * 0.145 / 142))
print("  ＜保守＞ライン別")
for ps, pc, pp in [(6, 4, 1.5), (7, 5, 2.0)]:
    v = TOOL[-1] * ps + C2C[-1] * pc + r["p1"] * pp
    print("     ツール%d倍+C2C%d倍+制作%.1f倍 = %6.1f億   シード %4.1f倍"
          % (ps, pc, pp, v / 100.0, v * 0.145 / 142))
