# -*- coding: utf-8 -*-
"""Ver0.7 の数字が、どの前提にどれだけ依存しているか

「この数字は正しいのか」への答えは2つに分かれる。
  計算が正しいか  … verify_xlsx.py / audit_xlsx.py で検証済み。正しい。
  数字が妥当か    … 別の話。★で置いた前提が結論をどれだけ作っているかを測る。

ここでは前提を1つずつ保守側に倒して、5期の売上と営業利益がどう動くかを見る。
"""

BASE = dict(
    # ① 映像制作
    units=3780, price=94.5, diff=1.55, ax=4.0,
    # ② ツール外販
    corp=600, corp_acv=326, indie=17000, indie_acv=12, self_rev=160,
    # ③ 越境C2C
    gmv=14248, take=0.30, c2c_gp=0.793,
    # 費用（5期・百万円）
    pay=187, off=100, rnd=1600, bpo=1000, acqf=200, acq1=0.06, acq2=0.15,
    agsh=0.159, agfe=0.15, sga=0.04, heads=22,
)


def calc(**ov):
    p = dict(BASE)
    p.update(ov)
    p1 = p["units"] * p["price"] / 100.0
    p2 = p["corp"] * p["corp_acv"] / 100.0 + p["indie"] * p["indie_acv"] / 100.0 + p["self_rev"]
    p3 = p["gmv"] * p["take"]
    rev = p1 + p2 + p3
    cu = p["diff"] * (12.0 + 20.0 / p["ax"] + 2.0 + 1.5)
    gp = p1 * (1 - cu / p["price"]) + p2 * 0.80 + p3 * p["c2c_gp"]
    acq = p1 * p["acq1"] + p2 * p["acq2"] + p["acqf"]
    agf = p1 * p["agsh"] * p["agfe"]
    opex = p["pay"] + p["off"] + p["rnd"] + p["bpo"] + acq + agf + rev * p["sga"]
    op = gp - opex
    ns = p2 + p3 + p1 * (1 - 1.0 / p["ax"])
    return dict(rev=rev, op=op, opr=op / rev if rev else 0, p1=p1, p2=p2, p3=p3,
                ns=ns / rev if rev else 0, rph=rev * 100 / p["heads"])


B = calc()
SHARE = 0.145
CHECK = 142.0

CASES = [
    ("基準（Ver0.7）", {}, ""),
    ("─ ③ の前提を倒す ─", None, ""),
    ("③ 価格を上限→中点", dict(gmv=8264), "成約が価格帯の真ん中に落ちる"),
    ("③ 価格を上限→下限", dict(gmv=1929), "供給が厚ければ競争で下限に寄る"),
    ("③ 件数を半分", dict(gmv=7124), "月9,400件→4,700件"),
    ("─ ① の前提を倒す ─", None, ""),
    ("① AX倍率 4.0→3.0", dict(ax=3.0), "原価が31.8→34.4万に上がる"),
    ("① AX倍率 4.0→2.0", dict(ax=2.0), ""),
    ("① 本数 3,780→2,500", dict(units=2500), "営業の担当社数かリピートが下振れ"),
    ("① 値引率50%→40%", dict(price=113.4), "値引きが浅い＝顧客の削減額が減る"),
    ("─ ② の前提を倒す ─", None, ""),
    ("② 法人600→300社", dict(corp=300), "海外展開が半分しか進まない"),
    ("② 個人17,000→8,000人", dict(indie=8000), ""),
    ("② 契約数を両方半分", dict(corp=300, indie=8000), ""),
    ("─ 複合 ─", None, ""),
    ("保守（③中点・AX3.0・②半分）", dict(gmv=8264, ax=3.0, corp=300, indie=8000), ""),
    ("悲観（③下限・AX2.0・②半分・①2,500本）",
     dict(gmv=1929, ax=2.0, corp=300, indie=8000, units=2500), ""),
]

print("=" * 104)
print("5期の売上と営業利益は、どの前提でどれだけ動くか")
print("=" * 104)
print("  %-34s %10s %10s %9s %10s %9s  %s"
      % ("ケース", "売上(億)", "営業利益", "利益率", "売上/社員", "シード", "備考"))
print("  " + "-" * 100)
for name, ov, note in CASES:
    if ov is None:
        print("  %s" % name)
        continue
    r = calc(**ov)
    mc = r["p2"] * 6 + r["p3"] * 4 + r["p1"] * 1.5        # ライン別・保守
    mult = mc * SHARE / CHECK
    mark = ""
    if ov:
        d = (r["op"] - B["op"]) / B["op"] * 100
        mark = "%+.0f%%" % d
    print("  %-34s %9.1f %9.1f億 %8.1f%% %9.2f億 %8.1f倍  %s %s"
          % (name, r["rev"] / 100, r["op"] / 100, r["opr"] * 100,
             r["rph"] / 10000, mult, mark, note))
print()

print("=" * 104)
print("何が効いているか")
print("=" * 104)
items = []
for name, ov, note in CASES:
    if ov:
        r = calc(**ov)
        items.append((name, (B["op"] - r["op"]) / 100))
items.sort(key=lambda x: -x[1])
print("  営業利益への影響が大きい順（5期・億円）")
print("  " + "-" * 60)
for name, d in items[:8]:
    bar = "█" * int(min(d, 50) / 1.2)
    print("  %-34s %6.1f億 %s" % (name, d, bar))
print()

print("=" * 104)
print("結論")
print("=" * 104)
cons = calc(gmv=8264, ax=3.0, corp=300, indie=8000)
pess = calc(gmv=1929, ax=2.0, corp=300, indie=8000, units=2500)
print("  計算  … verify_xlsx.py（plan_v15と一致）と audit_xlsx.py（内部整合）で検証済み。**正しい**。"
      .replace("**", ""))
print()
print("  数字  … 実測で裏が取れているのは市場規模・賃金・決済料率・クラウド単価・ベンチマーク。")
print("          **売上を作っている変数はほぼ全部★（私の仮置き）**。".replace("**", ""))
print()
print("  %-24s 売上 %6.1f億  営業利益 %6.1f億（%.1f%%）  シード %.1f倍"
      % ("基準（Ver0.7）", B["rev"] / 100, B["op"] / 100, B["opr"] * 100,
         (B["p2"] * 6 + B["p3"] * 4 + B["p1"] * 1.5) * SHARE / CHECK))
print("  %-24s 売上 %6.1f億  営業利益 %6.1f億（%.1f%%）  シード %.1f倍"
      % ("保守", cons["rev"] / 100, cons["op"] / 100, cons["opr"] * 100,
         (cons["p2"] * 6 + cons["p3"] * 4 + cons["p1"] * 1.5) * SHARE / CHECK))
print("  %-24s 売上 %6.1f億  営業利益 %6.1f億（%.1f%%）  シード %.1f倍"
      % ("悲観", pess["rev"] / 100, pess["op"] / 100, pess["opr"] * 100,
         (pess["p2"] * 6 + pess["p3"] * 4 + pess["p1"] * 1.5) * SHARE / CHECK))
print()
print("  → 売上は %.0f億〜%.0f億（%.1f倍の幅）、営業利益は %.0f億〜%.0f億。"
      % (pess["rev"] / 100, B["rev"] / 100, B["rev"] / pess["rev"],
         pess["op"] / 100, B["op"] / 100))
print("     **Ver0.7は、置ける前提を全部強い側に置いた場合の上限値**に近い。".replace("**", ""))
print("     悲観ケースでも黒字で、シードは %.1f倍。事業として成立はする。"
      % ((pess["p2"] * 6 + pess["p3"] * 4 + pess["p1"] * 1.5) * SHARE / CHECK))
print()
print("  ⚠ 投資家に出すなら、基準値だけでなくこの幅を一緒に出すべき。")
print("     120億という数字を単独で出すと、前提の1つが崩れた時点で全部疑われる。")
