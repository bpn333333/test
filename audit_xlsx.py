# -*- coding: utf-8 -*-
"""事業計画_Ver0.8.xlsx の整合性を通しで検査する

verify_xlsx.py が「plan_v15.py と同じ値か」を見るのに対し、
こちらは **ワークブック内部が矛盾していないか** を見る。

  A 恒等式      合計＝内訳の和、売上＝①＋②＋③、営業利益＝粗利−販管費 …
  B シート間     サマリー＝損益＝商品マスタ が一致しているか
  C 異常検知     5期とも同じ値の行（置換バグの兆候）、空セル、エラー値、負のキャッシュ
  D 符号・範囲   比率が0〜100%か、件数・人数が負でないか

  pip install formulas
  python audit_xlsx.py
"""
import sys
import formulas
import openpyxl

FN = "事業計画_Ver0.8.xlsx"
C5 = ["C", "D", "E", "F", "G"]
I5 = ["I", "J", "K", "L", "M"]
NG = []

xl = formulas.ExcelModel().loads(FN).finish()
sol = xl.calculate()
K = {k.upper(): v for k, v in sol.items()}
wb = openpyxl.load_workbook(FN)


def val(sheet, ref):
    v = K.get("'[%s]%s'!%s" % (FN.upper(), sheet.upper(), ref.upper()))
    try:
        return float(v.value[0, 0])
    except Exception:
        try:
            return v.value[0, 0]
        except Exception:
            return None


def row_of(sheet, label, col=1):
    for row in wb[sheet].iter_rows(min_col=col, max_col=col):
        if row[0].value == label:
            return row[0].row
    return None


def series(sheet, label, cols=None, col=1):
    r = row_of(sheet, label, col)
    if r is None:
        NG.append("行が見つからない: %s / %s" % (sheet, label))
        return None
    return [val(sheet, "%s%d" % (c, r)) for c in (cols or C5)]


def eq(name, a, b, tol=1.0):
    if a is None or b is None:
        NG.append("%s: 値が取れない" % name)
        print("  NG  %-46s 値が取れない" % name)
        return
    bad = [i for i in range(len(a))
           if not isinstance(a[i], float) or not isinstance(b[i], float)
           or abs(a[i] - b[i]) > tol]
    if bad:
        NG.append(name)
        print("  NG  %-46s %s期で不一致" % (name, ",".join(str(i + 1) for i in bad)))
        print("      左 " + "".join("%12.1f" % x if isinstance(x, float) else "%12s" % "?" for x in a))
        print("      右 " + "".join("%12.1f" % x if isinstance(x, float) else "%12s" % "?" for x in b))
    else:
        print("  OK  %s" % name)


def add(*ss):
    return [sum(s[i] for s in ss) for i in range(5)]


print("=" * 98)
print("A 恒等式（同じシートの中で辻褄が合っているか）")
print("=" * 98)
p1 = series("損益計算書", "① 映像制作")
p2 = series("損益計算書", "② ツール外販")
p3 = series("損益計算書", "③ C2C手数料")
rev = series("損益計算書", "売上高")
eq("損益: 売上高 ＝ ①＋②＋③", rev, add(p1, p2, p3))

g1 = series("損益計算書", "① 売上総利益")
g2 = series("損益計算書", "② 売上総利益")
g3 = series("損益計算書", "③ 売上総利益")
gp = series("損益計算書", "売上総利益")
eq("損益: 売上総利益 ＝ ①＋②＋③", gp, add(g1, g2, g3))

c1 = series("損益計算書", "① 売上原価")
eq("損益: ①粗利 ＝ ①売上 − ①原価", g1, [p1[i] - c1[i] for i in range(5)])

parts = [series("損益計算書", x) for x in
         ["人件費（社員）", "開発委託費（オフショア）", "研究開発費（GPU・基盤）",
          "BPO（CS・運用）", "獲得費", "代理店手数料", "知財関連費", "その他販管費"]]
opex = series("損益計算書", "販売費・一般管理費 計")
eq("損益: 販管費計 ＝ 8費目の和", opex, add(*parts))

op = series("損益計算書", "営業利益")
eq("損益: 営業利益 ＝ 粗利 − 販管費", op, [gp[i] - opex[i] for i in range(5)])

mix = series("商品マスタ①", "構成比 合計", I5)
eq("商品マスタ①: 構成比合計 ＝ 100%", mix, [1.0] * 5, tol=0.001)

units = series("商品マスタ①", "受注本数（営業体制シート）", I5)
price = series("商品マスタ①", "平均単価（万円）", I5)
m1rev = series("商品マスタ①", "① 売上（百万円）", I5)
eq("商品マスタ①: 売上 ＝ 本数 × 平均単価/100", m1rev,
   [units[i] * price[i] / 100 for i in range(5)])

corp = series("商品マスタ②", "法人売上（百万円）")
indi = series("商品マスタ②", "個人売上（百万円）")
self_ = series("商品マスタ②", "②-C 売上（百万円）")
m2rev = series("商品マスタ②", "② 売上 合計（百万円）")
eq("商品マスタ②: 合計 ＝ 法人＋個人＋セルフサーブ", m2rev, add(corp, indi, self_))

ga = series("商品マスタ③", "③-A GMV（百万円）")
gb = series("商品マスタ③", "③-B GMV（百万円）")
gc = series("商品マスタ③", "③-C GMV（百万円）")
gmv = series("商品マスタ③", "GMV 合計")
eq("商品マスタ③: GMV計 ＝ A＋B＋C", gmv, add(ga, gb, gc))

take = val("商品マスタ③", "B28")
m3rev = series("商品マスタ③", "③ 売上（手数料30%）")
eq("商品マスタ③: 売上 ＝ GMV × 手数料率", m3rev, [gmv[i] * take for i in range(5)])

cogs3 = series("商品マスタ③", "　− 決済・送金・システム")
gp3 = series("商品マスタ③", "売上総利益")
eq("商品マスタ③: 粗利 ＝ 売上 − 原価", gp3, [m3rev[i] - cogs3[i] for i in range(5)])

ws = wb["商品マスタ③"]
sumJ = sum(val("商品マスタ③", "J%d" % r) for r in range(5, 19))
totJ = val("商品マスタ③", "J23")
eq("商品マスタ③: 合計GMV ＝ 14商品の和", [totJ], [sumJ], tol=1.0)
adjJ = val("商品マスタ③", "J25")
eq("商品マスタ③: 共食い後の5期GMV ＝ 期別GMVの5期", [adjJ], [val("商品マスタ③", "G39")], tol=1.0)
for r in range(5, 19):
    f, h, j = val("商品マスタ③", "F%d" % r), val("商品マスタ③", "H%d" % r), val("商品マスタ③", "J%d" % r)
    if abs(f * h / 1e6 - j) > 0.5:
        NG.append("③ %d行: GMV ≠ 上限×件数" % r)
        print("  NG  ③ %d行 %s: 上限%.0f×件数%.0f/1e6=%.1f だが J=%.1f"
              % (r, ws.cell(r, 1).value, f, h, f * h / 1e6, j))
print("  OK  商品マスタ③: 14商品すべて GMV ＝ 上限 × 件数")

hp = wb["人員と人件費"]
heads = series("人員と人件費", "社員数 合計")
roles = [[val("人員と人件費", "%s%d" % (c, r)) for c in C5] for r in range(4, 10)]
eq("人員: 社員数 ＝ 6職種の和", heads, [sum(x[i] for x in roles) for i in range(5)])

print()
print("=" * 98)
print("B シート間（サマリー＝損益＝商品マスタ）")
print("=" * 98)
eq("サマリー 売上高 ＝ 損益 売上高", series("サマリー", "売上高"), rev)
eq("サマリー 営業利益 ＝ 損益 営業利益", series("サマリー", "営業利益"), op)
eq("サマリー ① ＝ 損益 ①", series("サマリー", "　① 映像制作"), p1)
eq("サマリー ② ＝ 損益 ②", series("サマリー", "　② ツール外販"), p2)
eq("サマリー ③ ＝ 損益 ③", series("サマリー", "　③ 越境C2C手数料"), p3)
eq("損益 ① ＝ 商品マスタ①", p1, m1rev)
eq("損益 ② ＝ 商品マスタ②", p2, m2rev)
eq("損益 ③ ＝ 商品マスタ③", p3, m3rev)
eq("損益 ③粗利 ＝ 商品マスタ③ 粗利", g3, gp3)
eq("損益 人件費 ＝ 人員シート", series("損益計算書", "人件費（社員）"),
   series("人員と人件費", "人件費（百万円）"))
eq("損益 開発委託費 ＝ 人員シート", series("損益計算書", "開発委託費（オフショア）"),
   series("人員と人件費", "開発委託費（百万円）"))
eq("資金計画 営業利益 ＝ 損益 営業利益", series("資金計画", "営業利益"), op)
eq("サマリー 期末キャッシュ ＝ 資金計画", series("サマリー", "期末キャッシュ残高"),
   series("資金計画", "期末キャッシュ残高"))
eq("サマリー ②ARR ＝ 商品マスタ②", series("サマリー", "② ツール外販 ARR"),
   series("商品マスタ②", "② ARR 合計（百万円）"))
eq("サマリー 全社ARR ＝ ①＋②＋③", series("サマリー", "全社 ARR"),
   add(series("サマリー", "① 映像制作 ARR"), series("サマリー", "② ツール外販 ARR"),
       series("サマリー", "③ 越境C2C ARR")))

ocf = series("資金計画", "営業キャッシュフロー")
tax = series("資金計画", "法人税等")
dwc = series("資金計画", "運転資本の増減（△は流出）")
eq("資金: 営業CF ＝ 営業利益 − 税 ＋ 運転資本増減", ocf,
   [op[i] - tax[i] + dwc[i] for i in range(5)])
net = series("資金計画", "当期キャッシュ増減")
fcf = series("資金計画", "財務キャッシュフロー")
icf = series("資金計画", "投資キャッシュフロー")
eq("資金: 当期増減 ＝ 営業＋投資＋財務", net, add(ocf, icf, fcf))
cash_s = series("資金計画", "期末キャッシュ残高")
cum = []
acc = 0.0
for i in range(5):
    acc += net[i]
    cum.append(acc)
eq("資金: 期末残高 ＝ 当期増減の累計", cash_s, cum)

ch = [series("営業体制", x) for x in ["　小計（本）"]]
sl = wb["営業体制"]
subs = [r for r in range(4, 20) if sl.cell(r, 1).value == "　小計（本）"]
tot_units = series("営業体制", "受注本数 合計")
inb = series("営業体制", "4 インバウンド（本）")
parts_u = [[val("営業体制", "%s%d" % (c, r)) for c in C5] for r in subs]
eq("営業体制: 受注本数 ＝ 3チャネル小計 ＋ インバウンド", tot_units,
   add(*(parts_u + [inb])))
eq("商品マスタ①: 受注本数 ＝ 営業体制 合計", units, tot_units)

sc = wb["システム原価"]
rows_sc = [r for r in range(15, 30) if isinstance(sc.cell(r, 9).value, (int, float))]
num = sum(val("システム原価", "H%d" % r) * val("システム原価", "I%d" % r) for r in rows_sc)
den = sum(val("システム原価", "I%d" % r) for r in rows_sc)
eq("システム原価: 加重平均 ＝ Σ(単価×件数)/Σ件数",
   [val("システム原価", "H%d" % (max(rows_sc) + 1))], [num / den], tol=0.2)

print()
print("=" * 98)
print("C 異常検知")
print("=" * 98)
flat = []
for sh in wb.sheetnames:
    w = wb[sh]
    cols = I5 if sh == "商品マスタ①" else C5
    lcol = 2 if sh == "前提" else 1     # 前提シートは項目名がB列
    for r in range(4, w.max_row + 1):
        lab = w.cell(r, lcol).value
        if not lab or not isinstance(lab, str):
            continue
        vs = [val(sh, "%s%d" % (c, r)) for c in cols]
        if any(v is None for v in vs) or not all(isinstance(v, float) for v in vs):
            continue
        if max(vs) == min(vs) and max(vs) != 0:
            flat.append((sh, r, lab, vs[0]))
KNOWN_FLAT = ["個人ACV", "ARPPU", "必要開発工数", "構成比 合計", "率", "負担率",
              "回転日数", "前受期間", "AIツール", "品質バッファ", "中国クリエイターへの支払",
              "制作ディレクション", "設備投資", "借入"]
for sh, r, lab, v in flat:
    ok = any(k in lab for k in KNOWN_FLAT)
    print("  %s  %-14s %3d行 %-28s 全期 %.1f" % ("--" if ok else "??", sh, r, lab[:28], v))
    if not ok:
        NG.append("5期とも同値: %s/%s" % (sh, lab))
if not flat:
    print("  OK  5期とも同じ値の行なし")

errs = []
for sh in wb.sheetnames:
    w = wb[sh]
    for row in w.iter_rows():
        for cell in row:
            if isinstance(cell.value, str) and cell.value.startswith("="):
                v = val(sh, cell.coordinate)
                if isinstance(v, str) and v.startswith("#"):
                    errs.append((sh, cell.coordinate, v))
print("  %s  数式のエラー値 %d件" % ("OK" if not errs else "NG", len(errs)))
for sh, co, v in errs[:10]:
    print("      %s!%s = %s" % (sh, co, v))
    NG.append("エラー値 %s!%s" % (sh, co))

cash = series("資金計画", "期末キャッシュ残高")
if any(x < 0 for x in cash):
    NG.append("期末キャッシュがマイナス")
    print("  NG  期末キャッシュにマイナスの期あり")
else:
    print("  OK  期末キャッシュは全期プラス（最小 %.0f百万）" % min(cash))

print()
print("=" * 98)
print("D 範囲チェック")
print("=" * 98)
for sheet, lab, lo, hi, cols in [
        ("損益計算書", "　粗利率", 0, 1, C5),
        ("損益計算書", "　営業利益率", -5, 1, C5),
        ("損益計算書", "　同 比率", 0, 1, C5),
        ("商品マスタ③", "　実効手数料率(%)", 0, 1, C5) if row_of("商品マスタ③", "　実効手数料率(%)") else ("損益計算書", "　粗利率", 0, 1, C5),
        ("人員と人件費", "　稼働率", 0, 1, C5)]:
    s = series(sheet, lab, cols)
    if s is None:
        continue
    bad = [i for i, v in enumerate(s) if not isinstance(v, float) or v < lo or v > hi]
    print("  %s  %-14s %-16s 範囲 %.0f〜%.0f" % ("NG" if bad else "OK", sheet, lab, lo, hi))
    if bad:
        NG.append("範囲外 %s/%s" % (sheet, lab))

walk = [("設立（資本金800万）", 20), ("IPO 公募", 25), ("売出し（既存株主が売る）", 26)]
for lab, _ in walk:
    r = row_of("資本構成の推移", lab, col=2)
    if r is None:
        continue
    tot = val("資本構成の推移", "I%d" % r)
    okc = abs(tot - 1.0) < 0.001
    print("  %s  資本構成 %-22s 合計 %.2f%%" % ("OK" if okc else "NG", lab, tot * 100))
    if not okc:
        NG.append("資本構成 %s の合計が100%%でない" % lab)

print()
print("=" * 98)
print("判定:", "整合性OK" if not NG else "問題 %d件" % len(NG))
for n in NG:
    print("  -", n)
sys.exit(0 if not NG else 1)
