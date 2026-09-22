# -*- coding: utf-8 -*-
"""別会社（子会社）でアダルト系AI映像を手がけた場合の試算

前提: 実在のAV IP（出演者の肖像）をライセンスし、AI生成作品を他社PF（FANZA等）で販売する。
本体（AI映像制作会社）とは別法人。本体の5年計画には一切含めない。

⚠ 検討用。市場データの出所が乏しい領域なので、金額はすべて［仮置き］。
⚠ 法務・決済・上場の制約が金額より先に効く。詳細は ADULT_SUBSIDIARY.md。
"""

# ── 1作品あたりの経済 ［すべて仮置き］──────────────────────────
PRICE      = 1500     # 販売価格（円）
PF_TAKE    = 0.50     # 他社PF（FANZA等）の手数料。当社取り分は残り
UNITS      = 300      # 1作品あたりの平均販売本数。★最も弱い前提
IP_ROYALTY = 0.20     # IP権利者へのレベニューシェア（当社取り分に対して）
COST_PER   = 50000    # 1作品あたりのAI制作原価（円）

# ── 作品数 ［仮置き］──────────────────────────────────────────
WORKS = [120, 480, 1200]          # 1年目=月10本, 2年目=月40本, 3年目=月100本
UNITS_Y = [300, 300, 340]         # 本数は3年目にやや改善する想定

# ── 費用 ［仮置き］──────────────────────────────────────────
HEADS   = [2, 4, 6]
PAY_PP  = [600, 650, 700]         # 万円/人・年
SGA_OTH = [800, 1500, 2500]       # 万円（審査対応・法務・システム・決済まわり）

Y = ["1年目", "2年目", "3年目"]


def yen_to_man(v):
    return v / 10000.0


rev, gp, roy, cost = [], [], [], []
for i in range(3):
    per_work_rev = UNITS_Y[i] * PRICE * (1 - PF_TAKE)      # 当社取り分（円）
    r = WORKS[i] * per_work_rev
    ro = r * IP_ROYALTY
    c = WORKS[i] * COST_PER
    rev.append(yen_to_man(r))
    roy.append(yen_to_man(ro))
    cost.append(yen_to_man(c))
    gp.append(yen_to_man(r - ro - c))

pay = [h * p for h, p in zip(HEADS, PAY_PP)]
op = [g - w - s for g, w, s in zip(gp, pay, SGA_OTH)]


def row(label, vals, f="{:>12,.0f}"):
    print(label.ljust(28) + "".join(f.format(v) for v in vals))


print("=" * 76)
print("アダルト系AI映像 子会社 — 3年の試算（単位 万円）")
print("=" * 76)
row("", Y, "{:>12}")
print("-" * 76)
row("  作品数（本）", WORKS)
row("  1作品あたり販売本数", UNITS_Y)
row("売上高（当社取り分）", rev)
row("  IP使用料（20%）", [-v for v in roy])
row("  AI制作原価", [-v for v in cost])
row("売上総利益", gp)
row("  粗利率(%)", [g / r * 100 for g, r in zip(gp, rev)], "{:>12.0f}")
row("  人件費", pay)
row("  その他販管費", SGA_OTH)
row("営業利益", op)
print("=" * 76)
print()
print("  3年目で 売上 %.1f億 / 営業利益 %.1f億 （営業利益率 %.0f%%）"
      % (rev[2] / 10000, op[2] / 10000, op[2] / rev[2] * 100))
print()

# ── 感応度: 1作品あたり販売本数（最も弱い前提）────────────────
print("=" * 76)
print("感応度 — 1作品あたりの平均販売本数（3年目・1,200本制作）")
print("=" * 76)
print("  この数字だけで事業の成否が決まる。FANZA同人の動画は当たり外れが大きい。")
print()
for u in [600, 340, 200, 100]:
    r = 1200 * u * PRICE * (1 - PF_TAKE) / 10000.0
    g = r * (1 - IP_ROYALTY) - 1200 * COST_PER / 10000.0
    o = g - pay[2] - SGA_OTH[2]
    mark = "  ←標準" if u == 340 else ""
    print("  平均%4d本 → 売上 %6.0f万 / 営業利益 %+7.0f万%s" % (u, r, o, mark))
print()

# ── IPを自社保有する場合（AV制作会社を取得するケース）──────────
print("=" * 76)
print("参考 — IPを自社で持つ場合（AV制作会社を取得する場合）")
print("=" * 76)
print("  IP使用料20%が消えるかわりに、取得対価と人件費・管理コストが乗る。")
print()
for i in [2]:
    saved = roy[i]
    print("  3年目のIP使用料 %.0f万 が不要になる → 営業利益 %.0f万 → %.0f万"
          % (saved, op[i], op[i] + saved))
print("  ただし取得対価の回収年数は、対象会社の実績次第。ここでは置けない。")
