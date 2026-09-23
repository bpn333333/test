# -*- coding: utf-8 -*-
"""事業計画_Ver1.5.xlsx を実際に再計算し、plan_v15.py と突き合わせる

openpyxl は数式を書くだけでキャッシュ値を持たないので、formulas でワークブックを解く。
同じ計算を Python で書き直すだけでは「数式が隣の行を指している」類のミスを拾えない。

  pip install formulas
  python verify_xlsx15.py
"""
import sys
import formulas
import openpyxl

FN = "事業計画_Ver1.5.xlsx"
xl = formulas.ExcelModel().loads(FN).finish()
sol = xl.calculate()
KEY = {k.upper(): v for k, v in sol.items()}
wb = openpyxl.load_workbook(FN)
C5 = ["C", "D", "E", "F", "G"]
OK = [True]


def cell(sheet, ref):
    v = KEY.get("'[%s]%s'!%s" % (FN.upper(), sheet.upper(), ref.upper()))
    try:
        return float(v.value[0, 0])
    except Exception:
        return v


def find(sheet, label, col=1):
    for row in wb[sheet].iter_rows(min_col=col, max_col=col):
        if row[0].value == label:
            return row[0].row
    raise KeyError(sheet + "/" + label)


def check(sheet, label, expect, tol=2.0, cols=None, fmt="%10.1f"):
    r = find(sheet, label)
    cols = cols or C5
    got = [cell(sheet, "%s%d" % (c, r)) for c in cols]
    bad = [i for i, (g, e) in enumerate(zip(got, expect))
           if not isinstance(g, float) or abs(g - e) > tol]
    if bad:
        OK[0] = False
    print("%s%-26s" % ("NG  " if bad else "OK  ", label)
          + "".join(fmt % g if isinstance(g, float) else "%10s" % "?" for g in got))
    if bad:
        print("    %-26s" % "  期待（plan_v15）" + "".join(fmt % e for e in expect))


I5 = ["I", "J", "K", "L", "M"]
print("=" * 96)
print("商品マスタ① — 平均単価・難度は構成比からの導出")
print("=" * 96)
check("商品マスタ①", "平均単価（万円）", [65.5, 75.6, 85.7, 89.6, 94.5], 0.2, I5)
check("商品マスタ①", "平均難度係数", [1.23, 1.34, 1.45, 1.50, 1.55], 0.01, I5, "%10.2f")
check("商品マスタ①", "1本あたり原価（万円）", [43.7, 38.6, 35.7, 33.2, 31.8], 0.2, I5)
check("商品マスタ①", "受注本数（営業体制シート）", [60, 304, 1215, 2543, 3780], 1, I5, "%10.0f")
check("商品マスタ①", "① 売上（百万円）", [39, 230, 1041, 2279, 3572], 3, I5, "%10.0f")

print()
print("=" * 96)
print("営業体制 — チャネルの積み上げ")
print("=" * 96)
check("営業体制", "受注本数 合計", [60, 304, 1215, 2543, 3780], 1, None, "%10.0f")
check("営業体制", "取引アカウント数", [15, 55, 175, 321, 460], 1, None, "%10.0f")

print()
print("=" * 96)
print("商品マスタ②③")
print("=" * 96)
check("商品マスタ②", "積み上げACV（万円）", [0, 265, 290, 308, 326], 2, None, "%10.0f")
check("商品マスタ②", "② 売上 合計（百万円）", [0, 46, 559, 2024, 4156], 3, None, "%10.0f")
check("商品マスタ③", "GMV 合計", [13, 163, 1857, 5839, 10245], 20, None, "%10.0f")
check("商品マスタ③", "③ 売上（手数料30%）", [4, 49, 557, 1752, 3074], 8, None, "%10.0f")
check("商品マスタ③", "売上総利益", [3, 39, 441, 1388, 2435], 10, None, "%10.0f")

print()
print("=" * 96)
print("損益計算書 — plan_v15.py と突き合わせ")
print("=" * 96)
check("損益計算書", "① 映像制作", [39, 230, 1041, 2279, 3572], 3, None, "%10.0f")
check("損益計算書", "② ツール外販", [0, 46, 559, 2024, 4156], 3, None, "%10.0f")
check("損益計算書", "③ C2C手数料", [4, 49, 557, 1752, 3074], 8, None, "%10.0f")
check("損益計算書", "売上高", [43, 325, 2157, 6055, 10802], 20, None, "%10.0f")
check("損益計算書", "売上総利益", [16, 188, 1496, 4441, 8130], 20, None, "%10.0f")
check("損益計算書", "人件費（社員）", [44, 77, 129, 172, 187], 2, None, "%10.0f")
check("損益計算書", "開発委託費（オフショア）", [26, 47, 74, 84, 100], 3, None, "%10.0f")
check("損益計算書", "獲得費", [8, 61, 236, 590, 1038], 4, None, "%10.0f")
check("損益計算書", "営業利益", [-94, -142, 384, 1852, 3689], 20, None, "%10.0f")
check("損益計算書", "社員数", [5, 9, 15, 20, 22], 0.5, None, "%10.0f")
check("損益計算書", "顧客が浮かせる額", [39, 230, 1041, 2279, 3572], 3, None, "%10.0f")

print()
print("=" * 96)
print("資金計画・資本構成")
print("=" * 96)
for lab in ["営業キャッシュフロー", "期末キャッシュ残高"]:
    r = find("資金計画", lab)
    got = [cell("資金計画", "%s%d" % (c, r)) for c in C5]
    print("    %-26s" % lab + "".join("%10.0f" % g if isinstance(g, float) else "%10s" % "?"
                                      for g in got))
    if any(isinstance(g, float) and g < 0 for g in got) and lab.startswith("期末"):
        OK[0] = False
        print("    ⚠ 期末キャッシュがマイナスの期がある")

WALK = [("設立（資本金800万）", [100.0, 0.0, 0.0, 0.0, 0.0]),
        ("シリーズA ＋ J-KISS転換", [54.9, 6.1, 18.9, 20.0, 0.0]),
        ("ESOP補充", [52.7, 9.9, 18.1, 19.2, 0.0]),
        ("IPO 公募", [42.2, 7.9, 14.5, 15.4, 20.0]),
        ("売出し（既存株主が売る）", [42.2, 7.9, 9.0, 15.4, 25.5])]
print()
for lab, exp in WALK:
    r = find("資本構成の推移", lab, col=2)
    got = [cell("資本構成の推移", "%s%d" % (c, r)) * 100 for c in ["D", "E", "F", "G", "H"]]
    tot = cell("資本構成の推移", "I%d" % r) * 100
    bad = any(abs(got[i] - exp[i]) > 0.2 for i in range(5)) or abs(tot - 100) > 0.1
    if bad:
        OK[0] = False
    print("%s%-24s" % ("NG  " if bad else "OK  ", lab)
          + "".join("%8.1f%%" % g for g in got) + "  計%.1f%%" % tot)

fr = find("資本構成の推移", "流通株式比率")
flo = cell("資本構成の推移", "E%d" % fr)
print("    流通株式比率 %.1f%%（基準25%%に対して %+.1fポイント）%s"
      % (flo * 100, (flo - 0.25) * 100, "  ○" if flo >= 0.25 else "  × 不足"))
if flo < 0.25:
    OK[0] = False

print()
print("=" * 96)
print("シードのリターン")
print("=" * 96)
for lab in ["ライン別・保守", "ライン別・中庸", "ライン別・強気", "全社 PSR 4倍", "全社 PSR 5倍"]:
    r = find("サマリー", lab)
    v = [cell("サマリー", "%s%d" % (c, r)) for c in ["C", "D", "E", "F"]]
    print("    %-16s 時価総額 %6.0f億   取り分 %6.2f億   %5.1f倍   IRR %5.1f%%"
          % (lab, v[0], v[1], v[2], v[3] * 100))

print()
print("判定:", "全て一致" if OK[0] else "不一致あり")
sys.exit(0 if OK[0] else 1)
