# -*- coding: utf-8 -*-
"""改訂方針（2026-09-22）にもとづく5年計画の再計算

変更点
  - 視聴プラットフォーム（視聴課金P2・広告P3）を削除
  - 越境C2C発注プラットフォームの「取引手数料」を新P2として置く
  - ツール外販（P4）を3期→2期に前倒し、5期を厚くする
  - 視聴者獲得費（流量投放）を削除し、発注者獲得のマーケ費に置き換える

⚠ 検討用。新しく置いた数字はすべて［仮置き］。
"""

Y = ["1期", "2期", "3期", "4期", "5期"]

# ── P2 越境C2C発注PF：GMV × 手数料率 ［すべて仮置き］──────────
GMV   = [50, 300, 900, 1800, 2700]   # 流通総額（百万円）。1期はPF公開6ヶ月目からの半年分
TAKE  = 0.18                          # 取引手数料率。国内C2C（ココナラ等）の約22%より低く置く

# ── P4 ツール外販：顧客数 × 単価 ［すべて仮置き］──────────────
CORP      = [0,   8,   40,  120,  250]   # 制作会社（法人）契約数
CORP_ACV  = [0, 250,  280,  300,  320]   # 法人の年間単価（万円）
INDIE     = [0,   0,  400, 1200, 2100]   # 個人クリエイター契約数
INDIE_ACV = 12                           # 個人の年間単価（万円）

# ── P1 制作受託（法人案件）［仮置き］─────────────────────────
# 受託色を薄めるため、制作主軸案（5期10億）から抑えている
P1 = [27, 105, 200, 320, 480]

GM = {"P1": 0.60, "P2": 0.85, "P4": 0.80}

# ── 費用 ［仮置き］──────────────────────────────────────────
HEADS   = [6, 16, 30, 44, 60]
PAY_PP  = [5.0, 7.0, 8.0, 9.0, 10.0]
MKT     = [6, 30, 60, 100, 140]        # 発注者の獲得。旧「視聴者獲得（流量投放）」の置き換え
SGA_OTH = [20, 50, 90, 140, 190]

SEED_IPO = 0.145        # 上場後のシード持分（キャップ6億・調達1.42億のとき）

P2 = [round(g * TAKE) for g in GMV]
P4 = [round(CORP[i] * CORP_ACV[i] / 100.0 + INDIE[i] * INDIE_ACV / 100.0) for i in range(5)]
REV = [a + b + c for a, b, c in zip(P1, P2, P4)]
GP = [round(a * GM["P1"] + b * GM["P2"] + c * GM["P4"]) for a, b, c in zip(P1, P2, P4)]
PAY = [round(h * p) for h, p in zip(HEADS, PAY_PP)]
OP = [g - w - m - s for g, w, m, s in zip(GP, PAY, MKT, SGA_OTH)]
NONLABOR = [(b + c) / r * 100 for b, c, r in zip(P2, P4, REV)]


def row(label, vals, f="{:>9,}"):
    print(label.ljust(26) + "".join(f.format(v) for v in vals))


print("=" * 86)
print("改訂版 5年計画（単位 百万円）")
print("=" * 86)
row("", Y, "{:>9}")
print("-" * 86)
row("  P1 制作受託（法人）", P1)
row("  P2 C2C発注PF 手数料", P2)
row("    参考: GMV", GMV)
row("  P4 ツール外販", P4)
row("    うち法人(社)", CORP)
row("    うち個人(人)", INDIE)
row("売上高", REV)
row("  人手に比例しない%", [round(x) for x in NONLABOR])
print("-" * 86)
row("売上総利益", GP)
row("  粗利率(%)", [round(g / r * 100) for g, r in zip(GP, REV)])
row("  人件費", PAY)
row("  発注者の獲得（マーケ）", MKT)
row("  その他販管費", SGA_OTH)
row("営業利益", OP)
row("  営業利益率(%)", [round(o / r * 100, 1) for o, r in zip(OP, REV)], "{:>9}")
row("日本側人員", HEADS)
print("=" * 86)

rev5 = REV[4]
print()
print("=" * 86)
print("時価総額とシードのリターン")
print("=" * 86)
print("  人手に比例しない収益が5期で %.0f%%。SaaS寄りの倍率を主張する根拠はここ。" % NONLABOR[4])
print()
print("  PSR   時価総額    シード持分14.5%（調達1.42億・キャップ6億）")
print("  " + "-" * 64)
for psr in [6, 7, 8]:
    v = rev5 * psr
    print("  %d倍   %6.1f億    %5.2f億 → %4.1f倍" % (psr, v / 100.0, v * SEED_IPO / 100.0, v * SEED_IPO / 142))
print()
print("  ＜参考＞調達1.2億・キャップ5億に変えた場合（持分14.7%・放出19%は同じ）")
print("  " + "-" * 64)
for psr in [6, 7, 8]:
    v = rev5 * psr
    print("  %d倍   %6.1f億    %5.2f億 → %4.1f倍" % (psr, v / 100.0, v * 0.147 / 100.0, v * 0.147 / 120))
