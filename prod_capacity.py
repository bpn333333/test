# -*- coding: utf-8 -*-
"""映像制作（①）の5期売上は、いくらが妥当か

Ver1.2 は 4.8億で置いているが、これは C2C 案を組むときに「受託色を薄める」ため
上から抑えた数字で、積み上げた根拠がない。需要側（コストメリットで取れるシェア）と
供給側（人員の上限）の両方から出し直す。

⚠ 市場の外挿と配分は［仮置き］。単価・原価・処理量は BUSINESS_PLAN 7-1 / MARKET_SIZING 第7章。
"""

# ── 市場（実測は2027年度まで。以降は外挿＝仮置き）──────────────
TAM = {2024: 4238, 2025: 4580, 2027: 5400}      # 億円・矢野経済研究所
CAGR = (TAM[2027] / TAM[2024]) ** (1 / 3.0) - 1
TAM_2031 = TAM[2027] * (1 + CAGR) ** 4
SAM_RATE = 0.30                                  # MARKET_SIZING 第5章［仮置き］
SAM_2031 = TAM_2031 * SAM_RATE

# ── 1本あたり（BUSINESS_PLAN 7-1）──────────────────────────
PRICE = 60.0          # 当社の受注単価（万円・5期）
COST = 18.5           # 原価（クリエイター12 + レビュー3 + ツール2 + バッファ1.5）
MARKET_PRICE = 100.0  # 発注者が従来払っていた額（企業VPの中央値付近・万円）

# ── 処理量（MARKET_SIZING 第7章）───────────────────────────
DIR_PER_MONTH = 10    # ディレクター1名の月間処理本数（3期以降）
SALES_PER_MONTH = 5   # 営業1名の月間受注本数
REPEAT = 0.50         # リピート率［仮置き］。1名の実効受注はこのぶん増える
CREATOR_PER_MONTH = 3 # 中国側クリエイター1名の月間制作本数

print("=" * 78)
print("① 需要側 — コストメリットで、どれだけ取れるか")
print("=" * 78)
print("  発注者から見た節約   %.0f万 → %.0f万（▲%.0f%%）" % (MARKET_PRICE, PRICE, (1 - PRICE / MARKET_PRICE) * 100))
print("  当社から見た粗利     %.0f万 − %.1f万 = %.1f万（粗利率 %.0f%%）"
      % (PRICE, COST, PRICE - COST, (PRICE - COST) / PRICE * 100))
print()
print("  市場（億円）  2025年度 %d【実測】 → 2027年度 %d【実測予測】 → 2031年 %.0f【外挿・仮置き】"
      % (TAM[2025], TAM[2027], TAM_2031))
print("  SAM（億円）   2031年 %.0f（TAMの%.0f%%。CM・実写必須・機密案件・代理店固定を除いた残り）"
      % (SAM_2031, SAM_RATE * 100))
print()
print("  5期の制作売上   SAMに対するシェア   必要な受注本数")
print("  " + "-" * 56)
for rev in [4.8, 10.0, 15.0, 20.0, 30.0]:
    share = rev / SAM_2031 * 100
    units = rev * 10000 / PRICE
    print("  %5.1f億          %6.3f%%           %6.0f本/年" % (rev, share, units))
print()
print("  → 30億でも SAM の %.1f%%。市場の広さはこの規模では制約になりません。" % (30 / SAM_2031 * 100))
print("     制約は供給側（人員）です。")
print()

print("=" * 78)
print("② 供給側 — 人員でいくらまで作れるか")
print("=" * 78)
dir_year = DIR_PER_MONTH * 12
sales_year = SALES_PER_MONTH * 12 * (1 + REPEAT)
print("  ディレクター1名  年%d本（月%d本）" % (dir_year, DIR_PER_MONTH))
print("  営業1名          年%.0f本（月%d本 × リピート%.0f%%）" % (sales_year, SALES_PER_MONTH, REPEAT * 100))
print("  クリエイター1名  年%d本（月%d本・中国側／原価に含む）" % (CREATOR_PER_MONTH * 12, CREATOR_PER_MONTH))
print()
print("  制作売上   本数    ディレクター  営業    日本側の制作要員  クリエイター(稼働/登録)")
print("  " + "-" * 74)
rows = []
for rev in [4.8, 10.0, 15.0, 20.0]:
    units = rev * 10000 / PRICE
    d = units / dir_year
    sa = units / sales_year
    jp = d + sa
    cw = units / (CREATOR_PER_MONTH * 12)
    rows.append((rev, units, d, sa, jp, cw))
    print("  %5.1f億   %5.0f本   %5.1f名      %5.1f名   %6.1f名        %4.0f名 / %4.0f名"
          % (rev, units, d, sa, jp, cw, cw * 1.5))
print()

TOTAL_HEADS = 60   # Ver1.2 の5期・日本側人員
print("  Ver1.2 の5期は日本側 %d名。制作に何名まで割けるか:" % TOTAL_HEADS)
print()
print("  制作売上   制作要員   残り（ツール開発・C2C運営・管理）  成立するか")
print("  " + "-" * 66)
for rev, units, d, sa, jp, cw in rows:
    rest = TOTAL_HEADS - jp - 3     # クリエイター管理3名を別途
    if rest >= 28:
        judge = "○  ツール・C2Cに十分回せる"
    elif rest >= 22:
        judge = "△  ツール・C2Cがぎりぎり"
    else:
        judge = "×  ツール外販10.5億を支えられない"
    print("  %5.1f億   %5.1f名    %5.1f名                         %s" % (rev, jp, rest, judge))
print()

print("=" * 78)
print("③ 制作を10億に戻した場合の全体")
print("=" * 78)
TOOL, C2C = 1052, 486          # 百万円（Ver1.2 のまま）
for p1 in [480, 1000]:
    rev = p1 + TOOL + C2C
    nonlabor = (TOOL + C2C) / rev * 100
    gp = p1 * 0.60 + TOOL * 0.80 + C2C * 0.85
    extra_heads = (p1 - 480) / 10000.0 * (1 / (PRICE / 10000) / dir_year + 1 / (PRICE / 10000) / sales_year)
    pay = 600 + max(0, (p1 - 480) / 72.0 * 2 * 10)   # 7,200万/2名 あたり 10百万/人
    op = gp - pay - 140 - 190
    tag = "Ver1.2（現状）" if p1 == 480 else "制作を10億に戻す"
    print()
    print("  【%s】" % tag)
    print("    売上   ① 制作 %4d ／ ② ツール %4d ／ ③ C2C %3d  = %4d百万（%.1f億）"
          % (p1, TOOL, C2C, rev, rev / 100.0))
    print("    人手に比例しない収益  %.0f%%" % nonlabor)
    print("    営業利益  約%4.0f百万（%.1f%%）" % (op, op / rev * 100))
    for psr in [6, 7, 8]:
        v = rev * psr
        print("    PSR%d倍 → 時価総額 %5.1f億   シード %4.1f倍" % (psr, v / 100.0, v * 0.145 / 142))
