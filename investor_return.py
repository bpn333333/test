# -*- coding: utf-8 -*-
"""シード投資家のリターン試算

「1.5億を入れたら何年でいくらになるか」への回答。
前提はすべて README.md 第1章 と CAP_TABLE.md 第5章。数字を変えたらそちらも直すこと。

⚠ これは事業計画からの逆算であって、投資の推奨でも利回りの保証でもない。
"""

# ── 前提 ────────────────────────────────────────────────────────
CHECK      = 142        # シード投資家が実際に入れる額（百万円）。残り8百万は創業者の資本金
T_IPO      = 4.9        # 2026/10 出資 → 2031/9 上場 までの年数
LOCKUP     = 0.5        # ロックアップ 90〜180日。全株売れるまで
SEED_IPO   = 0.145      # 上場後のシード持分（CAP_TABLE 第5章）
SEED_PRE   = 0.181      # 公募前のシード持分（M&A はこちらで分配される）

# 5期の想定時価総額（README 1-4。3手法の試算レンジ）
IPO_CASES  = [("下限", 3600), ("中心", 6400), ("上限", 10300)]

# M&A で売る場合の評価帯（デッキ「出口とリターン」）
MA_CASES   = [("4期 2030", 4.0, 2000, 4500), ("5期 2031", 5.0, 3800, 6400)]


def irr(mult, years):
    return mult ** (1.0 / years) - 1.0


def line(label, value, mult, years):
    print("  %-8s 評価額 %6.2f億 → 取り分 %6.2f億   %5.1f倍   IRR %5.1f%% (%.1f年)"
          % (label, value / 100.0, value * SEED_IPO / 100.0, mult, irr(mult, years) * 100, years))


print("=" * 78)
print("シード投資家 %d百万円（1.42億）が、何年でいくらになるか" % CHECK)
print("=" * 78)
print()
print("【本命】2031年に東証グロース上場。上場後のシード持分 %.1f%%" % (SEED_IPO * 100))
print("  出資 2026年10月 → 上場 2031年9月 = %.1f年。ロックアップ後の全株売却まで %.1f年"
      % (T_IPO, T_IPO + LOCKUP))
print()
for label, mcap in IPO_CASES:
    proceeds = mcap * SEED_IPO
    mult = proceeds / CHECK
    print("  %-4s 時価総額 %5.1f億 → シードの取り分 %5.2f億   %4.1f倍" % (label, mcap / 100.0, proceeds / 100.0, mult))
    print("       IRR  上場時点(%.1f年) %5.1f%%   /   ロックアップ明け(%.1f年) %5.1f%%"
          % (T_IPO, irr(mult, T_IPO) * 100, T_IPO + LOCKUP, irr(mult, T_IPO + LOCKUP) * 100))
print()

print("【代替】M&Aで売却。公募がないのでシード持分は %.1f%%" % (SEED_PRE * 100))
print()
for label, yrs, lo, hi in MA_CASES:
    for tag, v in [("下限", lo), ("上限", hi)]:
        proceeds = v * SEED_PRE
        mult = proceeds / CHECK
        print("  %-9s %s 売却額 %5.1f億 → 取り分 %5.2f億   %4.1f倍   IRR %5.1f%% (%.1f年)"
              % (label, tag, v / 100.0, proceeds / 100.0, mult, irr(mult, yrs) * 100, yrs))
print()

print("=" * 78)
print("【比較】シード期のVCが普通に求める水準")
print("=" * 78)
for mult in [3, 5, 10, 20]:
    need = CHECK * mult / SEED_IPO
    print("  %2d倍で返すには … 上場時の時価総額 %6.1f億 が必要   (IRR %.1f%%/5年)"
          % (mult, need / 100.0, irr(mult, T_IPO) * 100))
print()
print("  本計画の中心値は 64.0億 → %.1f倍。" % (6400 * SEED_IPO / CHECK))
print("  シード期のファンドは「当たりで10倍以上」を前提に組むことが多い。")
print("  10倍に必要な 97.9億 は、本計画の上限ケース(103億)でようやく届く水準。")


# ── 感応度 ──────────────────────────────────────────────────────
print()
print("=" * 78)
print("感応度① 上場が遅れた場合（中心値 64億・6.5倍のまま、年数だけ延びる）")
print("=" * 78)
m = 6400 * SEED_IPO / CHECK
for yrs, tag in [(4.9, "2031年 計画どおり"), (5.9, "2032年 1年遅れ"), (6.9, "2033年 2年遅れ"), (7.9, "2034年 3年遅れ")]:
    print("  %-18s %.1f年 → %4.1f倍   IRR %5.1f%%" % (tag, yrs, m, irr(m, yrs) * 100))

print()
print("=" * 78)
print("感応度② J-KISSのキャップ（CAP_TABLE 第4章の交渉帯は 6〜10億）")
print("=" * 78)
print("  ※ 持分はキャップにほぼ反比例するとみなした概算")
BASE_CAP = 6.0
for cap in [6.0, 7.0, 8.0, 10.0]:
    share = SEED_IPO * (BASE_CAP / cap)
    proceeds = 6400 * share
    mult = proceeds / CHECK
    mark = "  ←計画" if cap == BASE_CAP else ""
    print("  キャップ %4.1f億 → 上場後持分 %4.1f%%  取り分 %5.2f億  %4.1f倍  IRR %5.1f%%%s"
          % (cap, share * 100, proceeds / 100.0, mult, irr(mult, T_IPO) * 100, mark))
