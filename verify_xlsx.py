# -*- coding: utf-8 -*-
"""事業計画_Ver1.4.xlsx を実際に再計算し、plan_v14.py と突き合わせる

openpyxl は数式を書くだけでキャッシュ値を持たないので、
formulas でワークブックを解いて、セル参照のミスを検出する。
"""
import formulas, openpyxl, sys

FN = "事業計画_Ver1.4.xlsx"
xl = formulas.ExcelModel().loads(FN).finish()
sol = xl.calculate()

KEY = {}
for k, v in sol.items():
    KEY[k.upper()] = v


def cell(sheet, ref):
    k = "'[%s]%s'!%s" % (FN.upper(), sheet.upper(), ref.upper())
    v = KEY.get(k)
    try:
        return float(v.value[0, 0])
    except Exception:
        return v


wb = openpyxl.load_workbook(FN)


def find(sheet, label, col=1):
    ws = wb[sheet]
    for row in ws.iter_rows(min_col=col, max_col=col):
        if row[0].value == label:
            return row[0].row
    raise KeyError(label)


COLS = ["C", "D", "E", "F", "G"]
OK = [True]


def check(sheet, label, expect, tol=1.0, fmt="%9.1f"):
    r = find(sheet, label)
    got = [cell(sheet, "%s%d" % (c, r)) for c in COLS]
    bad = []
    for i, (g, e) in enumerate(zip(got, expect)):
        if g is None or not isinstance(g, float) or abs(g - e) > tol:
            bad.append(i)
    mark = "OK  " if not bad else "NG  "
    if bad:
        OK[0] = False
    print("%s%-26s" % (mark, label) + "".join(fmt % g if isinstance(g, float) else "%9s" % "?" for g in got))
    if bad:
        print("    %-26s" % "  期待値" + "".join(fmt % e for e in expect))
    return got


print("=" * 96)
print("損益計算書 — plan_v14.py と突き合わせ")
print("=" * 96)
check("損益計算書", "① 映像制作", [27, 192.5, 720, 1680, 3356.4])
check("損益計算書", "② ツール外販", [0, 37.5, 520, 1920, 3960])
check("損益計算書", "③ C2C手数料", [9, 72, 288, 810, 1494])
check("損益計算書", "売上高", [36, 302, 1528, 4410, 8810], tol=2)
check("損益計算書", "売上総利益", [15, 183, 1086, 3284, 6648], tol=2)
check("損益計算書", "人件費（社員）", [53, 114, 260, 417, 556], tol=2)
check("損益計算書", "獲得費", [8, 57, 211, 539, 995], tol=2)
check("損益計算書", "営業利益", [-76, -130, -17, 702, 2144], tol=3)
check("損益計算書", "社員数", [6, 13, 29, 46, 61], tol=0.5, fmt="%9.0f")
check("損益計算書", "売上 / 社員（万円）", [600, 2327, 5269, 9587, 14443], tol=20, fmt="%9.0f")
check("損益計算書", "人手に比例しない収益", [9, 174, 1200, 3850, 7971], tol=5)

print()
print("=" * 96)
print("資金計画")
print("=" * 96)
for lab in ["営業利益", "法人税等", "運転資本 残高 計", "運転資本の増減（△は流出）",
            "営業キャッシュフロー", "財務キャッシュフロー", "期末キャッシュ残高",
            "（感応度）前受金ゼロなら期末残高"]:
    r = find("資金計画", lab)
    got = [cell("資金計画", "%s%d" % (c, r)) for c in COLS]
    print("    %-30s" % lab + "".join("%10.0f" % g if isinstance(g, float) else "%10s" % "?" for g in got))

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
print("=" * 96)
print("資本構成の推移 — CAP_TABLE.md 第5章と突き合わせ")
print("=" * 96)
WALK = [
    ("設立（資本金800万）",      [100.0, 0.0,  0.0,  0.0,  0.0]),
    ("ESOP枠を設計",            [90.0, 10.0,  0.0,  0.0,  0.0]),
    ("J-KISS 発行（未転換）",    [90.0, 10.0,  0.0,  0.0,  0.0]),
    ("シリーズA ＋ J-KISS転換",  [54.9,  6.1, 18.9, 20.0,  0.0]),
    ("ESOP補充",                [52.7,  9.9, 18.1, 19.2,  0.0]),
    ("IPO 公募",                [42.2,  7.9, 14.5, 15.4, 20.0]),
]
print("    %-24s %8s %7s %7s %8s %7s %8s" % ("イベント", "創業者", "ESOP", "シード", "シリーズA", "公募", "合計"))
for label, exp in WALK:
    r = find("資本構成の推移", label, col=2)
    got = [cell("資本構成の推移", "%s%d" % (c, r)) for c in ["D", "E", "F", "G", "H", "I"]]
    pct = [g * 100 for g in got]
    bad = any(abs(pct[i] - exp[i]) > 0.15 for i in range(5)) or abs(pct[5] - 100) > 0.1
    if bad:
        OK[0] = False
    print("%s%-24s" % ("NG  " if bad else "OK  ", label)
          + "%8.1f%%%6.1f%%%6.1f%%%7.1f%%%6.1f%%%7.1f%%" % tuple(pct))
    if bad:
        print("    %-24s" % "  CAP_TABLE" + "".join("%8.1f%%" % e for e in exp))
print()
print("    転換時のシード持分  %.1f%%   （＝1.42億÷6億。ポストマネー・キャップ）"
      % (cell("資本構成の推移", "C13") * 100))
print("    流通株式比率        %.1f%%   基準25%%に対して %+.1fポイント"
      % (cell("資本構成の推移", "H%d" % find("資本構成の推移", "IPO 公募", col=2)) * 100,
         (cell("資本構成の推移", "H%d" % find("資本構成の推移", "IPO 公募", col=2)) - 0.25) * 100))

print()
print("判定:", "全て一致" if OK[0] else "不一致あり")
sys.exit(0 if OK[0] else 1)
