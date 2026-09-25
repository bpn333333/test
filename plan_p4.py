# -*- coding: utf-8 -*-
"""P4（ツール外販）を主役に置いた5年計画と、投資家リターンの試算

制作（P1）は「データを取るための手段」。売上の主役は P4 に移す。
P4 は金額を置かず、顧客数 × 単価から積み上げる。

⚠ 検討用。README.md の確定値ではない。
"""

# ── P4 の積み上げ前提 ［仮置き］────────────────────────────────
# 販売先は「①②で先に取引がある制作会社・クリエイター」。冷たい新規ではない。
CORP   = [0,   8,   40,  120,  250]   # 制作会社（法人）契約数
CORP_ACV = [0, 250, 280,  300,  320]  # 法人の年間単価（万円）
INDIE  = [0,   0,  400, 1200, 2100]   # 個人クリエイター契約数
INDIE_ACV = 12                        # 個人の年間単価（万円）

# ── 他ラインの売上（百万円）［仮置き］──────────────────────────
# 制作は「手段」なので、前の計画（5期10億）から意図的に抑える
P1 = [27, 105, 200, 350, 550]
PF = [ 8,  60, 140, 240, 350]

# ── 粗利率 ──────────────────────────────────────────────────
GM = {"P1": 0.60, "PF": 0.85, "P4": 0.80}

# ── 費用 ［仮置き］──────────────────────────────────────────
HEADS   = [6, 16, 30, 44, 60]          # P4の開発とB2B営業を厚くするので前より多い
PAY_PP  = [5.0, 7.0, 8.0, 9.0, 10.0]
ADS     = [15, 40, 70, 110, 150]       # PFを小さくしたぶん投放も縮む
SGA_OTH = [20, 50, 90, 140, 190]

SEED_CHECK = 142        # シードが入れる額（百万円）
SEED_IPO   = 0.145      # 上場後のシード持分
T_IPO      = 4.9

Y = ["1期", "2期", "3期", "4期", "5期"]


def p4_revenue():
    out = []
    for i in range(5):
        corp = CORP[i] * CORP_ACV[i] / 100.0          # 万円 → 百万円
        indie = INDIE[i] * INDIE_ACV / 100.0
        out.append(round(corp + indie))
    return out


P4 = p4_revenue()
REV = [a + b + c for a, b, c in zip(P1, PF, P4)]
GP = [round(a * GM["P1"] + b * GM["PF"] + c * GM["P4"]) for a, b, c in zip(P1, PF, P4)]
PAY = [round(h * p) for h, p in zip(HEADS, PAY_PP)]
OP = [g - w - a - s for g, w, a, s in zip(GP, PAY, ADS, SGA_OTH)]


def row(label, vals, f="{:>8,}"):
    print(label.ljust(24) + "".join(f.format(v) for v in vals))


print("=" * 80)
print("P4主役の5年計画（単位 百万円）")
print("=" * 80)
row("", Y, "{:>8}")
print("-" * 80)
row("  P4 ツール外販", P4)
row("    うち法人(社数)", CORP)
row("    うち個人(人数)", INDIE)
row("  P1 制作受託", P1)
row("  P2+P3 PF", PF)
row("売上高", REV)
row("  P4比率(%)", [round(a / b * 100) for a, b in zip(P4, REV)])
print("-" * 80)
row("売上総利益", GP)
row("  粗利率(%)", [round(g / r * 100) for g, r in zip(GP, REV)])
row("  人件費", PAY)
row("  流量投放", ADS)
row("  その他販管費", SGA_OTH)
row("営業利益", OP)
row("  営業利益率(%)", [round(o / r * 100, 1) for o, r in zip(OP, REV)], "{:>8}")
row("日本側人員", HEADS)
print("=" * 80)

rev5, op5, p4_5 = REV[4], OP[4], P4[4]
svc5 = P1[4] + PF[4]

print()
print("=" * 80)
print("時価総額 — 「どの倍率を、どの売上に掛けるか」で答えが変わります")
print("=" * 80)
print()
print("【A】全社売上にSaaS倍率を掛ける（松田さんの想定）")
for psr in [6, 7, 8]:
    v = rev5 * psr
    print("     PSR %d倍 × 売上%.1f億 = 時価総額 %6.1f億   シード %5.2f億 → %4.1f倍"
          % (psr, rev5 / 100.0, v / 100.0, v * SEED_IPO / 100.0, v * SEED_IPO / SEED_CHECK))
print()
print("【B】ラインごとに倍率を分ける（市場が実際にやること）")
for psr_saas, psr_svc in [(6, 1.5), (7, 2.0), (8, 2.5)]:
    v = p4_5 * psr_saas + svc5 * psr_svc
    print("     P4 %d倍 + 制作/PF %.1f倍 = 時価総額 %6.1f億   シード %5.2f億 → %4.1f倍"
          % (psr_saas, psr_svc, v / 100.0, v * SEED_IPO / 100.0, v * SEED_IPO / SEED_CHECK))
print()

print("=" * 80)
print("シード15〜20倍には、時価総額がいくら必要か")
print("=" * 80)
for mult in [10, 12, 15, 20]:
    need = SEED_CHECK * mult / SEED_IPO
    print("  %2d倍 → 時価総額 %6.1f億 が必要   （全社PSR換算 %.1f倍 / 売上%.1f億）"
          % (mult, need / 100.0, need / rev5, rev5 / 100.0))


# ══════════════════════════════════════════════════════════════
# 15〜20倍に届かせる2つの経路
# ══════════════════════════════════════════════════════════════
print()
print("=" * 80)
print("経路① P4をもっと伸ばす（ライン別評価【B】で 147億＝15倍 に届く水準）")
print("=" * 80)
svc = P1[4] + PF[4]
for psr_saas, psr_svc in [(6, 1.5), (7, 2.0), (8, 2.5)]:
    need_p4 = (146.9 * 100 - svc * psr_svc) / psr_saas
    corp_only = need_p4 * 100 / 320.0          # 全部を法人(ACV320万)で取った場合の社数
    print("  P4 %d倍/制作PF %.1f倍 なら P4売上 %5.1f億 が必要 "
          "（計画の %.1f倍／法人だけなら約%.0f社）"
          % (psr_saas, psr_svc, need_p4 / 100.0, need_p4 / P4[4], corp_only))

print()
print("=" * 80)
print("経路② シードの持分を増やす（J-KISSのキャップを下げる）")
print("=" * 80)
print("  ※ 持分はキャップにほぼ反比例するとみなした概算。時価総額は全社PSR倍率で置く")
print()
print("  キャップ   持分    120億のとき      136億のとき      156億のとき")
print("  " + "-" * 66)
for cap in [6.0, 5.0, 4.0, 3.0]:
    share = SEED_IPO * (6.0 / cap)
    cells = []
    for v in [12000, 13660, 15620]:
        cells.append("%5.1f倍" % (v * share / SEED_CHECK))
    print("  %4.1f億   %4.1f%%   %s" % (cap, share * 100, "        ".join(cells)))
print()
print("  ⚠ キャップを下げるほど創業者が薄まります。上場時の創業者持分の目安:")
for cap in [6.0, 5.0, 4.0, 3.0]:
    extra = SEED_IPO * (6.0 / cap) - SEED_IPO
    print("     キャップ %.1f億 → 創業者 約%.1f%%（キャップ6億の42.2%%から %.1fpt 減）"
          % (cap, 42.2 - extra * 100, extra * 100))
