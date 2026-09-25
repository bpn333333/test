# -*- coding: utf-8 -*-
"""制作でSAMの3%を取る。人員はAXで対処し、その利益率改善を数字で示す

「人手に比例しない収益」の定義を立て直す。

  売上が増えても人員が比例して増えない収益、と定義する。

  ② ツール外販     顧客+1 に対して人員+0        → 100% 比例しない
  ③ C2C手数料      取引+1 に対して人員+0        → 100% 比例しない
  ① 映像制作（AX後） 本数+4 に対して人員+1        → 増分の75%は人を増やさずに取れる

  したがって ① も、AX倍率に応じた分だけ「人手に比例しない」側に入る。

⚠ AX倍率は未実証の［仮置き］。この計画はそこに乗る。
"""

# ── 市場 ───────────────────────────────────────────────
TAM_2031 = 5400 * ((5400 / 4238) ** (1 / 3.0)) ** 4   # 億円・外挿［仮置き］
SAM_2031 = TAM_2031 * 0.30
TARGET = 0.03

PRICE, COST = 60.0, 18.5          # 万円/本
DIR_Y, SALES_Y, CRE_Y = 120.0, 90.0, 36.0
AX = 4                             # AX倍率［仮置き］

TOOL, C2C = 1052, 486              # 百万円
OTHER_HEADS = 32                   # ツール開発・C2C運営・管理

P1 = SAM_2031 * TARGET * 100       # 百万円
units = P1 / (PRICE / 100.0)
py_per_unit = 1.0 / DIR_Y + 1.0 / SALES_Y


def plan(ax):
    prod = units * py_per_unit / ax
    cre_mgr = max(3, units / (CRE_Y * ax) / 15.0)
    heads = prod + OTHER_HEADS + cre_mgr
    gp = P1 * (1 - COST / PRICE) + TOOL * 0.80 + C2C * 0.85
    rev = P1 + TOOL + C2C
    pay = heads * 10                       # 1,000万/人
    acq = P1 * 0.06 + 140 + TOOL * 0.15    # 制作案件の獲得 + C2C発注者獲得 + ツール営業CS
    sga = rev * 0.04                       # オフィス・SaaS・法務・インフラ
    op = gp - pay - acq - sga
    return dict(rev=rev, heads=heads, prod=prod, gp=gp, pay=pay, acq=acq, sga=sga, op=op,
                creators=units / (CRE_Y * ax))


print("=" * 82)
print("目標 — 映像制作でSAMの3%")
print("=" * 82)
print("  2031年 TAM %.0f億 → SAM %.0f億（30%%）→ その3%% = %.1f億" % (TAM_2031, SAM_2031, P1 / 100))
print("  必要な受注本数 %.0f本/年（月%.0f本）" % (units, units / 12))
print()

print("=" * 82)
print("AXが利益率をどう変えるか — 同じ売上を、何人で作るか")
print("=" * 82)
print("  AX倍率  日本側人員   人件費    売上総利益   営業利益    営業利益率  売上/人")
print("  " + "-" * 74)
for k in [1, 2, 3, 4, 5]:
    r = plan(k)
    mark = "  ←採用" if k == AX else ""
    print("  %2d倍    %6.0f名   %5.0f百万   %5.0f百万   %+6.0f百万   %6.1f%%   %5.0f万%s"
          % (k, r["heads"], r["pay"], r["gp"], r["op"], r["op"] / r["rev"] * 100,
             r["rev"] / r["heads"] * 100, mark))
print()
a, b = plan(1), plan(AX)
print("  → AXなし（%.0f名）と AX%d倍（%.0f名）の差は、人件費だけで %.0f百万（%.1f億）。"
      % (a["heads"], AX, b["heads"], a["pay"] - b["pay"], (a["pay"] - b["pay"]) / 100))
print("     営業利益率は %.1f%% → %.1f%%。**AXは原価ではなく、利益率そのものを作ります。**"
      .replace("**", "") % (a["op"] / a["rev"] * 100, b["op"] / b["rev"] * 100))
print()

print("=" * 82)
print("「人手に比例しない収益」の定義を立て直す")
print("=" * 82)
r = plan(AX)
non_ax = (1 - 1.0 / AX)                     # ①のうち人を増やさずに取れる割合
ns = TOOL + C2C + P1 * non_ax
print("  定義: 売上が増えても人員が比例して増えない収益")
print()
print("  ② ツール外販   %5.0f百万 × 100%%          = %5.0f百万" % (TOOL, TOOL))
print("  ③ C2C手数料    %5.0f百万 × 100%%          = %5.0f百万" % (C2C, C2C))
print("  ① 映像制作     %5.0f百万 × %2.0f%%（AX%d倍） = %5.0f百万" % (P1, non_ax * 100, AX, P1 * non_ax))
print("  " + "-" * 56)
print("  合計 %5.0f百万 ／ 売上 %.0f百万 = **%.0f%%**".replace("**", "") % (ns, r["rev"], ns / r["rev"] * 100))
print()
print("  ①は「同じ人数で4倍作れる」ので、増える4本のうち3本は人を増やさずに取れます。")
print("  だから①も、AX倍率に応じた分だけ人手に比例しない側に入ります。")
print()

print("=" * 82)
print("5期の全体像（AX%d倍）" % AX)
print("=" * 82)
print("  売上    ① 制作 %.0f ／ ② ツール %d ／ ③ C2C %d  = %.0f百万（%.1f億）"
      % (P1, TOOL, C2C, r["rev"], r["rev"] / 100))
print("  人員    %.0f名（制作 %.0f ／ ツール・C2C・管理 %d ／ クリエイター管理 %.0f）"
      % (r["heads"], r["prod"], OTHER_HEADS, r["heads"] - r["prod"] - OTHER_HEADS))
print("  中国側  稼働 %.0f名 ／ 登録 %.0f名" % (r["creators"], r["creators"] * 1.5))
print()
print("  売上総利益  %5.0f百万（%.0f%%）" % (r["gp"], r["gp"] / r["rev"] * 100))
print("   − 人件費   %5.0f百万" % r["pay"])
print("   − 獲得費   %5.0f百万（制作案件6%% ＋ C2C発注者 ＋ ツール営業CS15%%）" % r["acq"])
print("   − その他   %5.0f百万（売上の4%%）" % r["sga"])
print("  営業利益    %5.0f百万（%.1f%%）" % (r["op"], r["op"] / r["rev"] * 100))
print("  売上/人     %.0f万円" % (r["rev"] / r["heads"] * 100))
print()

print("=" * 82)
print("時価総額とシードのリターン")
print("=" * 82)
print("  人手に比例しない収益 %.0f%% を根拠に、全社へSaaS寄りの倍率を当てる" % (ns / r["rev"] * 100))
for psr in [4, 5, 6]:
    v = r["rev"] * psr
    print("     PSR%d倍 = %6.1f億   シード %4.1f倍" % (psr, v / 100.0, v * 0.145 / 142))
print()
print("  ＜保守＞ラインごとに倍率を分けた場合")
for ps, pc, pp in [(6, 4, 1.5), (7, 5, 2.0)]:
    v = TOOL * ps + C2C * pc + P1 * pp
    print("     ツール%d倍 + C2C%d倍 + 制作%.1f倍 = %6.1f億   シード %4.1f倍"
          % (ps, pc, pp, v / 100.0, v * 0.145 / 142))
