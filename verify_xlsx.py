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
print("判定:", "全て一致" if OK[0] else "不一致あり")
sys.exit(0 if OK[0] else 1)
