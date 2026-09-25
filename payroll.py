# -*- coding: utf-8 -*-
"""人件費を職種別に積む

これまで「1人あたり人件費」を 500→1,000万 と上げていたが、向きが逆だった。
創業期はコア人材（幹部・エンジニア）しかいないので単価が高く、
規模が出るとディレクター・CS・オペレーションの比率が上がって平均は下がる。

年収 × 1.16（法定福利費・採用教育の按分）を人件費として置く。
"""

BURDEN = 1.16   # 年収に対する会社負担の倍率［仮置き］

# 職種: (年収・万円)
ROLE = {
    "経営・CxO":        900,
    "エンジニア":        800,
    "制作ディレクター":   550,
    "営業・アカウント":   550,
    "クリエイター管理":   500,
    "管理・コーポレート": 550,
    "CS・オペレーション": 400,
}

# 期ごとの人数
HEADS = {
    #                1期 2期 3期 4期 5期
    "経営・CxO":        [1,  1,  2,  3,  3],
    "エンジニア":        [2,  4,  7, 10, 14],
    "制作ディレクター":   [1,  4, 12, 22, 34],
    "営業・アカウント":   [1,  4,  8, 14, 20],
    "クリエイター管理":   [1,  1,  2,  3,  5],
    "管理・コーポレート": [0,  2,  2,  3,  4],
    "CS・オペレーション": [0,  0,  2,  7, 12],
}

Y = ["1期", "2期", "3期", "4期", "5期"]
n = len(Y)

total_heads, total_pay, avg = [], [], []
for i in range(n):
    h = sum(HEADS[r][i] for r in ROLE)
    pay = sum(HEADS[r][i] * ROLE[r] * BURDEN for r in ROLE)   # 万円
    total_heads.append(h)
    total_pay.append(pay / 100.0)          # 百万円
    avg.append(pay / h)                    # 万円/人

print("=" * 80)
print("職種別の人員計画")
print("=" * 80)
print("  職種                年収     " + "".join("%6s" % y for y in Y))
print("  " + "-" * 64)
for r in ROLE:
    print("  %-18s %4d万  " % (r, ROLE[r]) + "".join("%6d" % HEADS[r][i] for i in range(n)))
print("  " + "-" * 64)
print("  %-18s        " % "合計（日本側）" + "".join("%6d" % h for h in total_heads))
print()

print("=" * 80)
print("人件費の平均単価は、下がっていきます")
print("=" * 80)
print("  " + " " * 20 + "".join("%9s" % y for y in Y))
print("  " + "-" * 66)
print("  人件費（百万円）    " + "".join("%9.0f" % p for p in total_pay))
print("  1人あたり（万円）   " + "".join("%9.0f" % a for a in avg))
print()
print("  → 創業期は幹部とエンジニアだけなので %.0f万。" % avg[0])
print("     規模が出るとディレクター・CS・オペレーションの比率が上がり、5期は %.0f万。" % avg[-1])
print("     ※ 年収 × %.2f（法定福利費・採用教育の按分）を人件費としています。" % BURDEN)
print()

# 職種構成の変化
print("  職種構成の変化（人数比）")
print("  " + " " * 20 + "".join("%9s" % y for y in Y))
for r in ["経営・CxO", "エンジニア", "制作ディレクター", "CS・オペレーション"]:
    print("  %-18s" % r + "".join("%8.0f%%" % (HEADS[r][i] / total_heads[i] * 100) for i in range(n)))
print()

# ── 5期の損益に効かせる ────────────────────────────────
P1, TOOL, C2C = 6713, 1052, 486
REV = P1 + TOOL + C2C
gp = P1 * (1 - 18.5 / 60.0) + TOOL * 0.80 + C2C * 0.85
acq = P1 * 0.06 + 140 + TOOL * 0.15
sga = REV * 0.04

print("=" * 80)
print("5期の営業利益 — 人件費を積み直した結果")
print("=" * 80)
for label, pay in [("旧（1,000万/人 × 92名）", 920), ("新（職種別の積み上げ）", total_pay[-1])]:
    op = gp - pay - acq - sga
    print("  %-26s 人件費 %4.0f百万 → 営業利益 %4.0f百万（%.1f%%）"
          % (label, pay, op, op / REV * 100))
print()
op_new = gp - total_pay[-1] - acq - sga
print("  売上総利益 %.0f百万（%.0f%%）" % (gp, gp / REV * 100))
print("   − 人件費 %.0f ／ 獲得費 %.0f ／ その他 %.0f" % (total_pay[-1], acq, sga))
print("  営業利益   %.0f百万（%.1f%%）" % (op_new, op_new / REV * 100))
print("  売上/人    %.0f万円" % (REV / total_heads[-1] * 100))
