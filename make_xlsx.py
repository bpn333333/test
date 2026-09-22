# -*- coding: utf-8 -*-
"""事業計画（Ver1.4）と資金計画を Excel モデルとして書き出す

数字を直打ちせず、「前提」シートの入力セルを参照する数式で組んでいる。
本数・単価・AX倍率・契約数・GMV・入金サイトを書き換えると、
損益からキャッシュ残高、シードの倍率まで連動して動く。

  python make_xlsx.py   ->  事業計画_Ver1.4.xlsx

⚠ 値の出所と［仮置き］の区別は「出所と仮置き」シートに全件載せること。
"""

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

OUT = "事業計画_Ver1.4.xlsx"
Y = ["1期", "2期", "3期", "4期", "5期"]
COLS = ["C", "D", "E", "F", "G"]

INK = "16161A"; VERM = "B3121B"; NAVY = "2A3563"; MUTED = "6E6E76"
HEADBG = "2A3563"; INBG = "FFF6DC"; CALCBG = "F4F4F6"; KEYBG = "FCE5CD"; LINE = "DCD9D4"

F_H = Font(name="Yu Gothic", size=10, bold=True, color="FFFFFF")
F_B = Font(name="Yu Gothic", size=10, bold=True, color=INK)
F_N = Font(name="Yu Gothic", size=10, color=INK)
F_S = Font(name="Yu Gothic", size=9, color=MUTED)
F_T = Font(name="Yu Gothic", size=14, bold=True, color=NAVY)
F_R = Font(name="Yu Gothic", size=10, bold=True, color=VERM)
THIN = Side(style="thin", color=LINE)
BOX = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)

MULT = '0.0"倍"'

wb = openpyxl.Workbook()


def sheet(name, widths):
    ws = wb.create_sheet(name)
    for i, w in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.sheet_view.showGridLines = False
    return ws


def title(ws, text, note=""):
    ws["A1"] = text
    ws["A1"].font = F_T
    if note:
        ws["A2"] = note
        ws["A2"].font = F_S


def header(ws, row, labels, start=1):
    for i, t in enumerate(labels):
        c = ws.cell(row=row, column=start + i, value=t)
        c.font = F_H
        c.fill = PatternFill("solid", fgColor=HEADBG)
        c.alignment = Alignment(horizontal="center", vertical="center")
        c.border = BOX
    ws.row_dimensions[row].height = 20


def put(ws, row, col, val, fmt=None, font=None, fill=None, align=None, border=True):
    c = ws.cell(row=row, column=col, value=val)
    c.font = font or F_N
    if fmt:
        c.number_format = fmt
    if fill:
        c.fill = PatternFill("solid", fgColor=fill)
    if align:
        c.alignment = Alignment(horizontal=align)
    if border:
        c.border = BOX
    return c


# ══════════════════════════════════════════════════════════════
# 前提（入力）
# ══════════════════════════════════════════════════════════════
P = sheet("前提", [16, 30, 12, 12, 12, 12, 12, 11, 12, 48])
title(P, "前提（ここだけを書き換える）",
      "黄色のセルが入力。他のシートはすべてここを参照する数式なので、書き換えれば損益・資金繰り・リターンまで動く。"
      "区分が［仮置き］のものは未実証。")
header(P, 3, ["大分類", "項目"] + Y + ["単位", "区分", "備考・出所"])

ROWS = [
    ("① 映像制作", "受注本数", [54, 350, 1200, 2800, 5594], "本", "［仮置き］",
     "5期はSAMの1.5%。B案（Ver1.3の11,189本を半減）"),
    ("", "平均単価", [50, 55, 60, 60, 60], "万円/本", "相場準拠",
     "動画幹事・ムビサクの制作費相場帯に基づく想定"),
    ("", "AX倍率", [1.0, 1.5, 2.2, 3.0, 4.0], "倍", "［仮置き］",
     "1人あたり制作本数の倍率。計画の最重要前提"),
    ("1本あたり原価", "中国クリエイターへの支払", [12, 12, 12, 12, 12], "万円/本", "［仮置き］",
     "CHINA_SOURCING.md"),
    ("", "制作ディレクション（AX前）", [20, 20, 20, 20, 20], "万円/本", "［仮置き］",
     "業務委託。成果物単位の支払なのでAX倍率で除される（8時間相当）"),
    ("", "AIツール・素材・レンダリング", [2, 2, 2, 2, 2], "万円/本", "［仮置き］",
     "クラウドGPU・ライセンス・素材"),
    ("", "品質バッファ（作り直し）", [1.5, 1.5, 1.5, 1.5, 1.5], "万円/本", "［仮置き］",
     "検収落ち分の引当"),
    ("② ツール外販", "法人契約数", [0, 15, 100, 320, 600], "社", "［仮置き］",
     "3期以降は海外が前提。国内の制作会社だけでは届かない"),
    ("", "法人ACV", [0, 250, 280, 300, 320], "万円/年", "［仮置き］",
     "チェックポイント・LoRA・工程ツール"),
    ("", "個人契約数", [0, 0, 2000, 8000, 17000], "人", "［仮置き］", "同上"),
    ("", "個人ACV", [12, 12, 12, 12, 12], "万円/年", "［仮置き］", "月1万円相当"),
    ("", "粗利率", [0.80, 0.80, 0.80, 0.80, 0.80], "%", "［仮置き］",
     "ソフトウェア外販の一般水準"),
    ("③ 越境C2C", "GMV（流通総額）", [50, 400, 1600, 4500, 8300], "百万円", "［仮置き］",
     "5期83億。ココナラの流通高に迫る規模"),
    ("", "手数料率", [0.18, 0.18, 0.18, 0.18, 0.18], "%", "［仮置き］",
     "収納代行型。当社は資金を保持しない"),
    ("", "粗利率", [0.85, 0.85, 0.85, 0.85, 0.85], "%", "［仮置き］", "決済手数料控除後"),
    ("費用", "研究開発費", [30, 120, 450, 1000, 1600], "百万円", "［仮置き］",
     "クラウドGPU・ライセンス・データ基盤。AX倍率を上げ続けるための投資"),
    ("", "BPO（CS・運用）", [0, 10, 120, 450, 1000], "百万円", "［仮置き］", "社員ではなく外部委託"),
    ("", "獲得費（固定分）", [6, 40, 90, 150, 200], "百万円", "［仮置き］", "C2C発注者の獲得ほか"),
    ("", "獲得費率（制作売上比）", [0.06, 0.06, 0.06, 0.06, 0.06], "%", "［仮置き］", "SALES_COST.md"),
    ("", "獲得費率（ツール売上比）", [0.15, 0.15, 0.15, 0.15, 0.15], "%", "［仮置き］", "営業・CS"),
    ("", "その他販管費率（売上比）", [0.04, 0.04, 0.04, 0.04, 0.04], "%", "［仮置き］",
     "オフィス・SaaS・法務・インフラ"),
    ("", "法定福利費等の負担率", [1.16, 1.16, 1.16, 1.16, 1.16], "倍", "［仮置き］",
     "年収に対する会社負担（社会保険・採用教育の按分）"),
    ("資金", "実効税率", [0.30, 0.30, 0.30, 0.30, 0.30], "%", "［仮置き］",
     "繰越欠損金の控除後に適用"),
    ("", "売上債権 回転日数（制作）", [60, 60, 60, 60, 60], "日", "［仮置き］", "検収後の入金サイト"),
    ("", "仕入債務 回転日数（制作原価）", [30, 30, 30, 30, 30], "日", "［仮置き］",
     "中国の制作パートナーへの支払サイト"),
    ("", "ツール外販の前受期間", [180, 180, 180, 180, 180], "日", "［仮置き］",
     "年額一括前受の平均残高。月額課金にすると0日になり資金繰りは厳しくなる"),
    ("", "設備投資", [0, 0, 0, 0, 0], "百万円", "方針",
     "クラウドGPU前提のため自社設備を持たない。GPU費用は研究開発費に計上"),
    ("", "調達：シード", [150, 0, 0, 0, 0], "百万円", "確定",
     "J-KISS 1.42億 ＋ 代表個人の直接出資 0.08億"),
    ("", "調達：シリーズA", [0, 300, 0, 0, 0], "百万円", "計画",
     "2期。これが無いと2期末に資金ショートする"),
    ("", "調達：借入", [0, 0, 0, 0, 0], "百万円", "方針", "借入はしない"),
]
r = 4
for big, item, vals, unit, kind, note in ROWS:
    put(P, r, 1, big, font=F_B)
    put(P, r, 2, item)
    for i, v in enumerate(vals):
        if unit == "%":
            fmt = "0.0%"
        elif unit == "倍" and item.startswith("法定"):
            fmt = "0.00"
        elif isinstance(v, float):
            fmt = "0.0"
        else:
            fmt = "#,##0"
        put(P, r, 3 + i, v, fmt=fmt, fill=INBG, align="right")
    put(P, r, 8, unit, align="center")
    put(P, r, 9, kind, font=F_R if kind == "［仮置き］" else F_N, align="center")
    put(P, r, 10, note, font=F_S)
    r += 1

R_UNITS, R_PRICE, R_AX = 4, 5, 6
R_CRE, R_DIR, R_TOOLC, R_BUF = 7, 8, 9, 10
R_CORP, R_CACV, R_INDI, R_IACV, R_TGM = 11, 12, 13, 14, 15
R_GMV, R_TAKE, R_CGM = 16, 17, 18
R_RND, R_BPO, R_ACQF, R_ACQ1, R_ACQ2, R_SGA, R_BURD = 19, 20, 21, 22, 23, 24, 25
R_TAX, R_AR, R_AP, R_DEF, R_CAPEX, R_SEED, R_SERA, R_LOAN = 26, 27, 28, 29, 30, 31, 32, 33


def p(row, i):
    return "前提!$%s$%d" % (COLS[i], row)


# ══════════════════════════════════════════════════════════════
# 人員と人件費
# ══════════════════════════════════════════════════════════════
H = sheet("人員と人件費", [28, 12, 11, 11, 11, 11, 11, 52])
title(H, "人員と人件費（社員は極小）",
      "制作ディレクション・CS・オペレーションは社員ではなく業務委託／BPO。"
      "社員は経営・モデル開発・各機能の統括・管理のみ。")
header(H, 3, ["職種", "年収(万円)"] + Y + ["考え方"])
ROLES = [
    ("経営・CxO", 900, [1, 1, 2, 3, 3], "代表＋CFO／CTO級"),
    ("モデル開発エンジニア", 850, [2, 6, 16, 28, 40], "AX倍率を上げ続ける中核。ここだけ厚くする"),
    ("制作統括", 650, [1, 2, 3, 3, 3], "業務委託ディレクターの束ね役。本数に比例させない"),
    ("事業開発・アライアンス", 700, [1, 2, 4, 5, 6], "法人開拓・海外展開"),
    ("クリエイターネットワーク統括", 600, [1, 1, 2, 3, 3], "中国パートナー・登録クリエイター管理"),
    ("管理・コーポレート", 550, [0, 1, 2, 4, 6], "経理・法務・上場準備"),
]
r = 4
for name, pay, heads, note in ROLES:
    put(H, r, 1, name)
    put(H, r, 2, pay, fmt="#,##0", fill=INBG, align="right")
    for i, h in enumerate(heads):
        put(H, r, 3 + i, h, fmt="#,##0", fill=INBG, align="right")
    put(H, r, 8, note, font=F_S)
    r += 1
R_ROLE0, R_ROLE1 = 4, r - 1
R_HEADS, R_PAY, R_AVG = r, r + 1, r + 2
put(H, R_HEADS, 1, "社員数 合計", font=F_B)
put(H, R_PAY, 1, "人件費（百万円）", font=F_B)
put(H, R_AVG, 1, "1人あたり人件費（万円）", font=F_B)
for i, c in enumerate(COLS):
    put(H, R_HEADS, 3 + i, "=SUM(%s%d:%s%d)" % (c, R_ROLE0, c, R_ROLE1),
        fmt="#,##0", fill=KEYBG, align="right", font=F_B)
    put(H, R_PAY, 3 + i, "=SUMPRODUCT($B$%d:$B$%d,%s%d:%s%d)*%s/100"
        % (R_ROLE0, R_ROLE1, c, R_ROLE0, c, R_ROLE1, p(R_BURD, i)),
        fmt="#,##0", fill=CALCBG, align="right", font=F_B)
    put(H, R_AVG, 3 + i, "=IF(%s%d=0,0,%s%d*100/%s%d)" % (c, R_HEADS, c, R_PAY, c, R_HEADS),
        fmt="#,##0", fill=CALCBG, align="right")
put(H, R_HEADS, 8, "ここが「社員は極小」の実数", font=F_S)
put(H, R_AVG, 8, "安い職種が社外に出るので平均単価は上がる。総額は抑えられる", font=F_S)

r = R_AVG + 2
put(H, r, 1, "参考：社員ではない人たち", font=F_B, border=False)
r += 1
header(H, r, ["区分", ""] + Y + ["考え方"])
R_GIG, R_CRE2 = r + 1, r + 2
put(H, R_GIG, 1, "業務委託ディレクション（人）")
put(H, R_CRE2, 1, "中国クリエイター 稼働（人）")
for i, c in enumerate(COLS):
    put(H, R_GIG, 3 + i, "=%s*(1/120+1/90)/%s" % (p(R_UNITS, i), p(R_AX, i)),
        fmt="#,##0", align="right")
    put(H, R_CRE2, 3 + i, "=%s/(36*%s)" % (p(R_UNITS, i), p(R_AX, i)), fmt="#,##0", align="right")
put(H, R_GIG, 8, "従来の1本あたり人年（1/120＋1/90）をAX倍率で除す", font=F_S)
put(H, R_CRE2, 8, "1人あたり年36本を前提［仮置き］", font=F_S)

# ══════════════════════════════════════════════════════════════
# 損益計算書
# ══════════════════════════════════════════════════════════════
L = sheet("損益計算書", [30, 3, 13, 13, 13, 13, 13, 54])
title(L, "5年損益計算書（単位：百万円）",
      "すべて数式。「前提」シートと「人員と人件費」シートを参照している。")
header(L, 3, ["項目", ""] + Y + ["備考"])

RL = {}
_row = [4]


def line(key, label, formulas, fmt="#,##0", bold=False, fill=None, note=""):
    r = _row[0]
    put(L, r, 1, label, font=F_B if bold else F_N)
    put(L, r, 2, "")
    for i, c in enumerate(COLS):
        put(L, r, 3 + i, formulas(i, c), fmt=fmt, align="right",
            font=F_B if bold else F_N, fill=fill)
    if note:
        put(L, r, 8, note, font=F_S)
    RL[key] = r
    _row[0] = r + 1


line("p1", "① 映像制作", lambda i, c: "=%s*%s/100" % (p(R_UNITS, i), p(R_PRICE, i)),
     note="受注本数 × 平均単価")
line("units", "　　受注本数（本）", lambda i, c: "=%s" % p(R_UNITS, i))
line("ax", "　　AX倍率", lambda i, c: "=%s" % p(R_AX, i), fmt="0.0")
line("p2", "② ツール外販",
     lambda i, c: "=%s*%s/100+%s*%s/100" % (p(R_CORP, i), p(R_CACV, i), p(R_INDI, i), p(R_IACV, i)),
     note="法人契約数×ACV ＋ 個人契約数×ACV")
line("p3", "③ C2C手数料", lambda i, c: "=%s*%s" % (p(R_GMV, i), p(R_TAKE, i)), note="GMV × 手数料率")
line("rev", "売上高", lambda i, c: "=%s%d+%s%d+%s%d" % (c, RL["p1"], c, RL["p2"], c, RL["p3"]),
     bold=True, fill=KEYBG)
_row[0] += 1
line("cu", "1本あたり原価（万円）",
     lambda i, c: "=%s+%s/%s+%s+%s" % (p(R_CRE, i), p(R_DIR, i), p(R_AX, i), p(R_TOOLC, i), p(R_BUF, i)),
     fmt="0.0", note="ディレクション費はAX倍率で除される。ここがAXの効き所")
line("g1", "① 売上総利益", lambda i, c: "=%s%d*(1-%s%d/%s)" % (c, RL["p1"], c, RL["cu"], p(R_PRICE, i)))
line("g2", "② 売上総利益", lambda i, c: "=%s%d*%s" % (c, RL["p2"], p(R_TGM, i)))
line("g3", "③ 売上総利益", lambda i, c: "=%s%d*%s" % (c, RL["p3"], p(R_CGM, i)))
line("gp", "売上総利益", lambda i, c: "=%s%d+%s%d+%s%d" % (c, RL["g1"], c, RL["g2"], c, RL["g3"]),
     bold=True, fill=KEYBG)
line("cogs", "（参考）売上原価", lambda i, c: "=%s%d-%s%d" % (c, RL["rev"], c, RL["gp"]))
line("gpr", "　　粗利率", lambda i, c: "=IF(%s%d=0,0,%s%d/%s%d)" % (c, RL["rev"], c, RL["gp"], c, RL["rev"]),
     fmt="0.0%")
_row[0] += 1
line("pay", "人件費（社員）", lambda i, c: "='人員と人件費'!%s%d" % (c, R_PAY),
     note="社員のみ。業務委託・BPOは含まない")
line("rnd", "研究開発費", lambda i, c: "=%s" % p(R_RND, i),
     note="AX倍率を上げ続けるための投資。ここを削ると計画が崩れる")
line("bpo", "BPO（CS・運用）", lambda i, c: "=%s" % p(R_BPO, i))
line("acq", "獲得費",
     lambda i, c: "=%s%d*%s+%s%d*%s+%s" % (c, RL["p1"], p(R_ACQ1, i), c, RL["p2"], p(R_ACQ2, i), p(R_ACQF, i)))
line("sga", "その他販管費", lambda i, c: "=%s%d*%s" % (c, RL["rev"], p(R_SGA, i)))
line("opex", "販売費・一般管理費 計", lambda i, c: "=SUM(%s%d:%s%d)" % (c, RL["pay"], c, RL["sga"]), bold=True)
line("op", "営業利益", lambda i, c: "=%s%d-%s%d" % (c, RL["gp"], c, RL["opex"]), bold=True, fill=KEYBG)
line("opr", "　　営業利益率",
     lambda i, c: "=IF(%s%d=0,0,%s%d/%s%d)" % (c, RL["rev"], c, RL["op"], c, RL["rev"]),
     fmt="0.0%", bold=True)
_row[0] += 1
put(L, _row[0], 1, "投資家が見る指標", font=F_B, border=False)
_row[0] += 1
line("heads", "社員数", lambda i, c: "='人員と人件費'!%s%d" % (c, R_HEADS))
line("rph", "売上 / 社員（万円）",
     lambda i, c: "=IF(%s%d=0,0,%s%d*100/%s%d)" % (c, RL["heads"], c, RL["rev"], c, RL["heads"]),
     fill=KEYBG, bold=True, note="国内SaaSの平均2,000〜4,000万との比較に使う")
line("rndr", "研究開発費 ÷ 売上",
     lambda i, c: "=IF(%s%d=0,0,%s%d/%s%d)" % (c, RL["rev"], c, RL["rnd"], c, RL["rev"]), fmt="0.0%")
line("ns", "人手に比例しない収益",
     lambda i, c: "=%s%d+%s%d+%s%d*(1-1/%s)" % (c, RL["p2"], c, RL["p3"], c, RL["p1"], p(R_AX, i)),
     note="②＋③＋①のうちAXで人手から切れた分")
line("nsr", "　　同 比率",
     lambda i, c: "=IF(%s%d=0,0,%s%d/%s%d)" % (c, RL["rev"], c, RL["ns"], c, RL["rev"]),
     fmt="0.0%", bold=True, fill=KEYBG, note="受託と読まれないための中心指標。5期で90%")

# ══════════════════════════════════════════════════════════════
# 資金計画
# ══════════════════════════════════════════════════════════════
K = sheet("資金計画", [30, 3, 13, 13, 13, 13, 13, 54])
title(K, "資金計画・キャッシュフロー（単位：百万円）",
      "営業利益からキャッシュ残高まで。運転資本と法人税を引いた後の、実際に手元に残る現金。")
header(K, 3, ["項目", ""] + Y + ["備考"])

RK = {}
_k = [4]


def kline(key, label, formulas, fmt="#,##0", bold=False, fill=None, note=""):
    r = _k[0]
    RK[key] = r          # 前期を参照する行（繰越欠損金・残高）があるので先に確定させる
    put(K, r, 1, label, font=F_B if bold else F_N)
    put(K, r, 2, "")
    for i, c in enumerate(COLS):
        put(K, r, 3 + i, formulas(i, c), fmt=fmt, align="right",
            font=F_B if bold else F_N, fill=fill)
    if note:
        put(K, r, 8, note, font=F_S)
    _k[0] = r + 1


def prev(i):
    return COLS[i - 1] if i > 0 else None


kline("op", "営業利益", lambda i, c: "=損益計算書!%s%d" % (c, RL["op"]), bold=True)
kline("nol", "　繰越欠損金（期首）",
      lambda i, c: "=0" if i == 0 else "=MAX(0,%s%d-%s%d)" % (prev(i), RK["nol"], prev(i), RK["op"]),
      note="前期までの累積赤字。黒字化後の税負担を軽くする")
kline("tax_base", "　課税所得", lambda i, c: "=MAX(0,%s%d-%s%d)" % (c, RK["op"], c, RK["nol"]))
kline("tax", "法人税等", lambda i, c: "=%s%d*%s" % (c, RK["tax_base"], p(R_TAX, i)),
      note="実効税率30%［仮置き］。繰越欠損金の控除後")
_k[0] += 1
kline("wc1", "運転資本：制作（売掛−買掛）",
      lambda i, c: "=損益計算書!%s%d*%s/365-(損益計算書!%s%d-損益計算書!%s%d)*%s/365"
      % (c, RL["p1"], p(R_AR, i), c, RL["p1"], c, RL["g1"], p(R_AP, i)),
      note="制作は入金60日・支払30日なので、伸びるほど現金が先に出る")
kline("wc2", "運転資本：ツール前受金（△）",
      lambda i, c: "=-損益計算書!%s%d*%s/365" % (c, RL["p2"], p(R_DEF, i)),
      note="年額一括前受なので資金の source になる。月額課金にすると消える")
kline("wc", "運転資本 残高 計", lambda i, c: "=%s%d+%s%d" % (c, RK["wc1"], c, RK["wc2"]), bold=True)
kline("dwc", "運転資本の増減（△は流出）",
      lambda i, c: "=-%s%d" % (c, RK["wc"]) if i == 0 else "=-(%s%d-%s%d)" % (c, RK["wc"], prev(i), RK["wc"]))
_k[0] += 1
kline("ocf", "営業キャッシュフロー",
      lambda i, c: "=%s%d-%s%d+%s%d" % (c, RK["op"], c, RK["tax"], c, RK["dwc"]),
      bold=True, fill=KEYBG)
kline("icf", "投資キャッシュフロー", lambda i, c: "=-%s" % p(R_CAPEX, i),
      note="クラウドGPU前提のため自社設備を持たない")
kline("seed", "　調達：シード", lambda i, c: "=%s" % p(R_SEED, i))
kline("sera", "　調達：シリーズA", lambda i, c: "=%s" % p(R_SERA, i))
kline("loan", "　調達：借入", lambda i, c: "=%s" % p(R_LOAN, i), note="借入はしない")
kline("fcf", "財務キャッシュフロー",
      lambda i, c: "=%s%d+%s%d+%s%d" % (c, RK["seed"], c, RK["sera"], c, RK["loan"]), bold=True)
_k[0] += 1
kline("net", "当期キャッシュ増減",
      lambda i, c: "=%s%d+%s%d+%s%d" % (c, RK["ocf"], c, RK["icf"], c, RK["fcf"]), bold=True)
kline("cash", "期末キャッシュ残高",
      lambda i, c: "=%s%d" % (c, RK["net"]) if i == 0 else "=%s%d+%s%d" % (prev(i), RK["cash"], c, RK["net"]),
      bold=True, fill=KEYBG, note="ここがマイナスになる期があってはいけない")
_k[0] += 1
kline("burn", "月次バーン（平均）",
      lambda i, c: "=IF(%s%d>=0,0,-%s%d/12)" % (c, RK["ocf"], c, RK["ocf"]))
kline("runway", "ランウェイ（ヶ月）",
      lambda i, c: '=IF(%s%d=0,"—",%s%d/%s%d)' % (c, RK["burn"], c, RK["cash"], c, RK["burn"]),
      fmt="0.0", note="期末残高 ÷ 月次バーン。黒字化後は「—」")
kline("cash0", "（感応度）前受金ゼロなら期末残高",
      lambda i, c: "=%s%d+%s%d" % (c, RK["cash"], c, RK["wc2"]),
      note="ツールを月額課金にした場合。ここもプラスなら資金繰りは前受に依存していない")

r = _k[0] + 1
put(K, r, 1, "シード1.5億は何に使うか（1期の支出）", font=F_B, border=False)
r += 1
header(K, r, ["用途", "", "金額", "", "", "", "", "内容"])
r += 1
USE = [
    ("研究開発費", "=損益計算書!C%d" % RL["rnd"], "モデル開発・クラウドGPU・データ基盤。ここが事業の本体"),
    ("人件費（社員6名）", "=損益計算書!C%d" % RL["pay"], "経営1・モデル開発2・制作統括1・事業開発1・クリエイター統括1"),
    ("制作原価", "=損益計算書!C%d-損益計算書!C%d" % (RL["p1"], RL["g1"]), "中国クリエイターへの支払・業務委託ディレクション"),
    ("獲得費", "=損益計算書!C%d" % RL["acq"], "初期案件の獲得・C2C発注者の獲得"),
    ("その他販管費", "=損益計算書!C%d" % RL["sga"], "オフィス・SaaS・法務"),
]
R_USE0 = r
for name, f, note in USE:
    put(K, r, 1, name)
    put(K, r, 2, "")
    put(K, r, 3, f, fmt="#,##0", align="right")
    put(K, r, 8, note, font=F_S)
    r += 1
put(K, r, 1, "1期の支出 計", font=F_B)
put(K, r, 2, "")
put(K, r, 3, "=SUM(C%d:C%d)" % (R_USE0, r - 1), fmt="#,##0", align="right", font=F_B)
r += 1
put(K, r, 1, "△ 1期の売上入金", font=F_N)
put(K, r, 2, "")
put(K, r, 3, "=-損益計算書!C%d" % RL["rev"], fmt="#,##0", align="right")
put(K, r, 8, "制作・C2Cの入金。売掛のずれは上の運転資本で調整", font=F_S)
r += 1
put(K, r, 1, "1期の正味所要資金", font=F_B)
put(K, r, 2, "")
put(K, r, 3, "=C%d+C%d" % (r - 2, r - 1), fmt="#,##0", align="right", font=F_B, fill=KEYBG)
r += 1
put(K, r, 1, "2期の正味所要資金", font=F_B)
put(K, r, 2, "")
put(K, r, 3, "=-D%d" % RK["ocf"], fmt="#,##0", align="right", font=F_B)
put(K, r, 8, "シードだけでは2期を通せない。シリーズA3億は2期に必須", font=F_R)
r += 2
put(K, r, 1, "⚠ 3期は営業赤字だが、ツールの前受金が増えるため営業キャッシュフローは黒字になる。"
             "前受が無い（月額課金の）前提でも残高はプラスを保つ設計。",
    font=F_S, border=False)

# ══════════════════════════════════════════════════════════════
# 原価とAX感応度
# ══════════════════════════════════════════════════════════════
A = sheet("原価とAX感応度", [26, 18, 16, 16, 20, 16, 48])
title(A, "AX倍率を変えると、5期の利益はどう動くか",
      "AXは人数ではなく「1本あたりのディレクション時間」に効く。"
      "業務委託は成果物単位の支払なので、時間が1/4になれば単価も1/4になる。")
header(A, 3, ["AX倍率", "ディレクション費/本", "1本あたり原価", "制作の粗利率",
              "5期 営業利益(百万)", "営業利益率", "判定"])
r = 4
NOTES = {1.0: "AXなし。それでも黒字だが、投資家が払う倍率は付かない",
         2.0: "",
         3.0: "◀ ここでも計画は成立する（本数を半減させた効果）",
         4.0: "◀ 計画値",
         5.0: "上振れ"}
for k in [1.0, 2.0, 3.0, 4.0, 5.0]:
    put(A, r, 1, k, fmt="0.0", fill=INBG, align="center", font=F_B)
    put(A, r, 2, "=前提!$G$%d/A%d" % (R_DIR, r), fmt="0.0", align="right")
    put(A, r, 3, "=前提!$G$%d+B%d+前提!$G$%d+前提!$G$%d" % (R_CRE, r, R_TOOLC, R_BUF),
        fmt="0.0", align="right")
    put(A, r, 4, "=1-C%d/前提!$G$%d" % (r, R_PRICE), fmt="0.0%", align="right")
    put(A, r, 5, "=損益計算書!$G$%d*D%d+損益計算書!$G$%d+損益計算書!$G$%d-損益計算書!$G$%d"
        % (RL["p1"], r, RL["g2"], RL["g3"], RL["opex"]), fmt="#,##0", align="right", font=F_B)
    put(A, r, 6, "=E%d/損益計算書!$G$%d" % (r, RL["rev"]), fmt="0.0%", align="right", font=F_B)
    put(A, r, 7, NOTES[k], font=F_R if k in (3.0, 4.0) else F_S)
    r += 1
r += 1
put(A, r, 1, "AXは原価を下げる装置であり、利益率そのものを作る。"
             "浮いた分は研究開発に戻してAX倍率をさらに上げる。この循環が、競合に同じ年数を要求する。",
    font=F_S, border=False)

# ══════════════════════════════════════════════════════════════
# 資本構成の推移
# ══════════════════════════════════════════════════════════════
W = sheet("資本構成の推移", [14, 26, 10, 11, 10, 10, 12, 10, 10, 30])
title(W, "株式シェアの推移（設立 → 上場）",
      "出所は CAP_TABLE.md 第5章。J-KISS はポストマネー・キャップなので、"
      "転換時のシード持分は 調達額 ÷ キャップ。")
header(W, 3, ["項目", "", "値", "単位", "区分", "", "", "", "", "備考"])
CW = [
    ("資本金", 800, "万円", "確定", "代表個人が全額出資"),
    ("ESOP枠（設立時）", 0.10, "%", "計画", "後から作ると既存株主全員の希薄化になるので設立時に設計する"),
    ("J-KISS キャップ（ポストマネー）", 6.0, "億円", "確定", "交渉帯は6〜10億。低すぎるとシリーズAで一気に薄まる"),
    ("シード調達額", 1.42, "億円", "確定", "目標1.5億のうち0.08億は代表個人の直接出資"),
    ("ディスカウント", 0.20, "%", "確定", "キャップとの有利な方が適用される"),
    ("シリーズA ポストマネー評価", 15.0, "億円", "計画", "2028年（2期）"),
    ("シリーズA 調達額", 3.0, "億円", "計画", "これが無いと2期末に資金ショートする"),
    ("ESOP補充後の ESOP比率", 0.099, "%", "計画", "シリーズAで薄まった枠を戻す"),
    ("IPO 公募比率", 0.20, "%", "計画", "2031年。新株発行なので全員が薄まる"),
    ("IPO 売出し（シードから）", 0.055, "%", "計画",
     "既存株主が売る。新株ではないので創業者は薄まらない。シードを10%未満に落とすのが目的"),
    ("IPO 売出し（シリーズAから）", 0.0, "%", "計画",
     "シード分だけで基準を満たすため0。交渉次第で振り替えてよい"),
]
r = 4
for name, v, unit, kind, note in CW:
    put(W, r, 1, name if r == 4 else "")
    put(W, r, 2, name)
    put(W, r, 3, v, fmt="0.0%" if unit == "%" else ("#,##0" if unit == "万円" else "0.00"),
        fill=INBG, align="right")
    put(W, r, 4, unit, align="center")
    put(W, r, 5, kind, align="center")
    put(W, r, 10, note, font=F_S)
    r += 1
W_ESOP, W_CAP, W_RAISE, W_A_POST, W_A_RAISE, W_ESOP2, W_PUB = 5, 6, 7, 9, 10, 11, 12
W_SELL_S, W_SELL_A, W_CONV, W_ASH = 13, 14, 15, 16
for name, f, note in [("転換時のシード持分（シリーズA前）", "=C%d/C%d" % (W_RAISE, W_CAP),
                       "ポストマネー・キャップなので 1.42億 ÷ 6億"),
                      ("シリーズA の持分", "=C%d/C%d" % (W_A_RAISE, W_A_POST), "3億 ÷ post 15億")]:
    put(W, r, 2, name, font=F_B)
    put(W, r, 3, f, fmt="0.0%", fill=CALCBG, align="right", font=F_B)
    put(W, r, 10, note, font=F_S)
    r += 1

r += 1
put(W, r, 1, "持分の推移", font=F_B, border=False)
r += 1
header(W, r, ["時期", "イベント", "金額", "創業者", "ESOP", "シード", "シリーズA", "公募", "合計", "経営権の判定"])
r += 1
W0 = r
WALK = [
    ("2026/10", "設立（資本金800万）", "—", ["=1", "=0", "=0", "=0", "=0"]),
    ("2026/10", "ESOP枠を設計", "—",
     ["=D{p}*(1-$C${e})", "=$C${e}", "=0", "=0", "=0"]),
    ("2026/10", "J-KISS 発行（未転換）", "1.42億",
     ["=D{p}", "=E{p}", "=0", "=0", "=0"]),
    ("2028", "シリーズA ＋ J-KISS転換", "3億",
     ["=D{p}*(1-$C${c})*(1-$C${a})", "=E{p}*(1-$C${c})*(1-$C${a})",
      "=$C${c}*(1-$C${a})", "=$C${a}", "=0"]),
    ("2028", "ESOP補充", "—",
     ["=D{p}*(1-$C${e2})/(1-E{p})", "=$C${e2}", "=F{p}*(1-$C${e2})/(1-E{p})",
      "=G{p}*(1-$C${e2})/(1-E{p})", "=0"]),
    ("2031", "IPO 公募", "—",
     ["=D{p}*(1-$C${pb})", "=E{p}*(1-$C${pb})", "=F{p}*(1-$C${pb})",
      "=G{p}*(1-$C${pb})", "=$C${pb}"]),
    ("2031", "売出し（既存株主が売る）", "—",
     ["=D{p}", "=E{p}", "=F{p}-$C${ss}", "=G{p}-$C${sa}", "=H{p}+$C${ss}+$C${sa}"]),
]
for when, ev, amt, fs in WALK:
    put(W, r, 1, when)
    put(W, r, 2, ev, font=F_B)
    put(W, r, 3, amt, align="right")
    for j, f in enumerate(fs):
        put(W, r, 4 + j, f.format(p=r - 1, e=W_ESOP, c=W_CONV, a=W_ASH, e2=W_ESOP2,
                                  pb=W_PUB, ss=W_SELL_S, sa=W_SELL_A),
            fmt="0.0%", align="right",
            font=F_B if j == 0 else F_N, fill=KEYBG if j == 0 else None)
    put(W, r, 9, "=SUM(D%d:H%d)" % (r, r), fmt="0.0%", align="right", font=F_S)
    put(W, r, 10, '=IF(D%d>0.5,"経営権あり（50%%超）",IF(D%d>0.334,"拒否権あり（1/3超）","1/3割れ"))' % (r, r))
    r += 1
W_FINAL = r - 1          # 売出し後（＝上場後に実際に保有している持分）
W_IPO = r - 2            # 公募直後（＝売出し分を含む経済持分。リターンの計算はこちら）
put(W, r, 2, "売出しは新株発行ではないので、創業者もESOPも薄まらない。"
             "シードの持分が動くだけで、売却代金はシードが受け取る。", font=F_S, border=False)

r += 2
put(W, r, 1, "上場時の評価額（売出しの代金を含む経済持分）", font=F_B, border=False)
r += 1
header(W, r, ["株主", "経済持分", "うち売出し", "保守 348億", "中庸 419億", "強気 490億",
              "", "", "", "備考"])
r += 1
for label, col, sell, note in [
        ("創業者", "D", None, "経営権は上場時に50%を割る。シリーズA後も52.7%を維持できる"),
        ("シード投資家", "F", W_SELL_S, "売却代金 ＋ 保有株の合計。売出しをしても取り分は変わらない"),
        ("シリーズA", "G", W_SELL_A, ""),
        ("ESOP", "E", None, "役員・従業員への配分枠"),
        ("公募", "H", None, "新株発行分")]:
    put(W, r, 1, label, font=F_B)
    put(W, r, 2, "=%s%d" % (col, W_IPO), fmt="0.0%", align="right", font=F_B)
    put(W, r, 3, "=$C$%d" % sell if sell else "—", fmt="0.0%" if sell else None, align="right")
    for k, v in enumerate([348, 419, 490]):
        put(W, r, 4 + k, "=B%d*%d" % (r, v), fmt="#,##0.0", align="right",
            fill=KEYBG if label in ("創業者", "シード投資家") else None)
    put(W, r, 10, note, font=F_S)
    r += 1
put(W, r, 1, "単位は億円。売出しは新株発行ではないので、売った側の経済持分は減らない（代金で受け取る）。",
    font=F_S, border=False)

r += 2
put(W, r, 1, "流通株式比率 — 基準25%を満たす設計", font=F_B, border=False)
r += 1
header(W, r, ["株主", "上場後の保有持分", "10%の判定", "流通株式への算入", "算入される持分",
              "", "", "", "", "理由"])
r += 1
R_FLOAT0 = r
for label, col, fixed, why in [
        ("創業者（役員）", "D", False, "役員の保有分は除外される"),
        ("ESOP枠", "E", False, "役員・従業員分は除外される"),
        ("シード投資家 保有分", "F", None, "10%未満なら全株が算入される。売出しでここを越える"),
        ("シリーズA 保有分", "G", None, "10%以上なので除外。シードだけで基準を満たすため売出しは0"),
        ("公募・売出し", "H", True, "市場に出た分。全額が算入される")]:
    put(W, r, 1, label)
    put(W, r, 2, "=%s%d" % (col, W_FINAL), fmt="0.0%", align="right", font=F_B)
    if fixed is None:
        put(W, r, 3, '=IF(B%d<0.1,"10%%未満","10%%以上")' % r, align="center")
        put(W, r, 4, '=IF(B%d<0.1,"○ 算入","× 除外")' % r, align="center")
        put(W, r, 5, "=IF(B%d<0.1,B%d,0)" % (r, r), fmt="0.0%", align="right", font=F_B)
    else:
        put(W, r, 3, "—", align="center")
        put(W, r, 4, "○ 算入" if fixed else "× 除外", align="center", font=F_N if fixed else F_R)
        put(W, r, 5, "=B%d" % r if fixed else 0, fmt="0.0%", align="right", font=F_B)
    put(W, r, 10, why, font=F_S)
    r += 1
put(W, r, 1, "流通株式比率", font=F_B)
put(W, r, 2, "")
put(W, r, 3, "")
put(W, r, 4, "")
put(W, r, 5, "=SUM(E%d:E%d)" % (R_FLOAT0, r - 1), fmt="0.0%", align="right", font=F_B, fill=KEYBG)
R_FLOATSUM = r
r += 1
put(W, r, 1, "基準25%に対する過不足", font=F_B)
put(W, r, 2, "")
put(W, r, 3, "")
put(W, r, 4, '=IF(E%d>=0.25,"○ 満たす","× 不足")' % R_FLOATSUM, align="center", font=F_B)
put(W, r, 5, "=E%d-0.25" % R_FLOATSUM, fmt='+0.0%;-0.0%;0.0%', align="right", font=F_B)
put(W, r, 10, "東証グロースの上場維持基準", font=F_S)
r += 2
put(W, r, 1, "仕組み: シードが5.5%を売出すと保有が10%未満になり、"
             "残りの保有株も一括で流通株式に算入される。公募20%だけなら20%、"
             "売出しを足すと34.5%まで跳ね上がるのはこのため。"
             "公募を25%に上げる案より、創業者持分が2.6ポイント厚く残る（42.2% vs 39.5%）。",
    font=F_S, border=False)
r += 1
put(W, r, 1, "⚠ 残る論点: 時価総額348億で25.5%を売り出すと、公開規模は約89億になる。"
             "グロース市場としては大きく、機関投資家の需要が要る。主幹事が決まる4期に規模を再設計すること。"
             "シードのタームシートには「上場時の売出しに協力する」条項を入れておく。",
    font=F_R, border=False)

# ══════════════════════════════════════════════════════════════
# 資本政策とリターン
# ══════════════════════════════════════════════════════════════
C = sheet("資本政策とリターン", [30, 16, 10, 12, 16, 14, 12, 12, 46])
title(C, "資本政策とシード投資家のリターン",
      "⚠ 事業計画からの逆算であって、投資の推奨でも利回りの保証でもない。計画が達成された場合の数字。")
header(C, 3, ["項目", "値", "単位", "区分", "", "", "", "", "備考"])
CAP = [
    ("J-KISS キャップ（ポストマネー）", "='資本構成の推移'!C%d" % W_CAP, "億円", "確定",
     "「資本構成の推移」シートの入力を参照"),
    ("シード調達額", "='資本構成の推移'!C%d" % W_RAISE, "億円", "確定",
     "目標1.5億のうち0.08億は代表個人が直接出資"),
    ("転換時のシード持分", "='資本構成の推移'!C%d" % W_CONV, "%", "計算",
     "ポストマネー・キャップなので ＝ 調達額 ÷ キャップ"),
    ("転換後の希薄化", "=B8/B6", "倍", "計算",
     "シリーズA20% → ESOP補充 → IPO公募20% の積。推移シートから逆算"),
    ("上場後のシード持分", "='資本構成の推移'!F%d" % W_IPO, "%", "計算", "CAP_TABLE.md 第5章"),
    ("出資 → 上場", 4.9, "年", "計画", "2026年10月出資 → 2031年9月 東証グロース"),
]
r = 4
for name, v, unit, kind, note in CAP:
    put(C, r, 1, name)
    fmt = "0.0%" if unit == "%" else ("0.000" if unit == "倍" else "0.00")
    is_calc = isinstance(v, str)
    put(C, r, 2, v, fmt=fmt, fill=CALCBG if is_calc else INBG, align="right",
        font=F_B if kind == "計算" else F_N)
    put(C, r, 3, unit, align="center")
    put(C, r, 4, kind, align="center")
    put(C, r, 9, note, font=F_S)
    r += 1
R_SHARE = 8

r += 1
put(C, r, 1, "① ライン別に倍率を分けた場合（証券会社が実際にやる見方）", font=F_B, border=False)
r += 1
header(C, r, ["ケース", "ツール倍率", "C2C倍率", "制作倍率", "時価総額(億)", "取り分(億)", "倍率", "IRR", "考え方"])
r += 1
R_LINE0 = r
for name, a, b, cc, note in [("保守", 6, 4, 1.5, "人手に比例しない90%を根拠に、ツールへSaaS寄りの倍率を当てる"),
                             ("中庸", 7, 5, 2.0, ""),
                             ("強気", 8, 6, 2.5, "Synthesia・HeyGenと同じ土俵に立てた場合")]:
    put(C, r, 1, name, font=F_B)
    put(C, r, 2, a, fmt="0.0", fill=INBG, align="right")
    put(C, r, 3, b, fmt="0.0", fill=INBG, align="right")
    put(C, r, 4, cc, fmt="0.0", fill=INBG, align="right")
    put(C, r, 5, "=(損益計算書!$G$%d*B%d+損益計算書!$G$%d*C%d+損益計算書!$G$%d*D%d)/100"
        % (RL["p2"], r, RL["p3"], r, RL["p1"], r), fmt="#,##0", align="right", font=F_B, fill=CALCBG)
    put(C, r, 6, "=E%d*$B$%d" % (r, R_SHARE), fmt="0.00", align="right")
    put(C, r, 7, "=F%d/$B$5" % r, fmt=MULT, align="right", font=F_R)
    put(C, r, 8, "=G%d^(1/$B$9)-1" % r, fmt="0.0%", align="right")
    put(C, r, 9, note, font=F_S)
    r += 1

r += 1
put(C, r, 1, "② 全社に PSR を当てた場合", font=F_B, border=False)
r += 1
header(C, r, ["ケース", "PSR", "", "", "時価総額(億)", "取り分(億)", "倍率", "IRR", "考え方"])
r += 1
R_PSR0 = r
for name, ps, note in [("PSR 4倍", 4, "人手に比例しない収益が90%であることを根拠にする"), ("PSR 5倍", 5, "")]:
    put(C, r, 1, name, font=F_B)
    put(C, r, 2, ps, fmt="0.0", fill=INBG, align="right")
    put(C, r, 3, "")
    put(C, r, 4, "")
    put(C, r, 5, "=損益計算書!$G$%d*B%d/100" % (RL["rev"], r), fmt="#,##0", align="right",
        font=F_B, fill=CALCBG)
    put(C, r, 6, "=E%d*$B$%d" % (r, R_SHARE), fmt="0.00", align="right")
    put(C, r, 7, "=F%d/$B$5" % r, fmt=MULT, align="right", font=F_R)
    put(C, r, 8, "=G%d^(1/$B$9)-1" % r, fmt="0.0%", align="right")
    put(C, r, 9, note, font=F_S)
    r += 1
r += 1
put(C, r, 1, "⚠ 東証グロースの維持基準「上場5年経過後に時価総額100億円」に対し、保守ケースでも3倍以上のバッファ。"
             "ただし計画が達成された場合に限る。", font=F_S, border=False)

# ══════════════════════════════════════════════════════════════
# 業界ベンチマーク
# ══════════════════════════════════════════════════════════════
B = sheet("業界ベンチマーク", [30, 14, 26, 30, 54])
title(B, "実在企業と並べる（5期の当社）",
      "⚠ 世界の「映像制作会社ランキング」は存在しない。大手広告グループは制作事業を分離開示しないため、"
      "比較できるのは開示のある会社に限られる。")
header(B, 3, ["会社", "売上(億円)", "区分", "決算期・出所", "備考"])
BENCH = [
    ("東映", 1853, "映画・映像製作", "2026/3期", "国内最大。劇場・テレビ・版権"),
    ("IMAGICA GROUP", 1000, "ポスプロ・映像技術", "2026/3期（Q1 222億からの推計）", "推計値"),
    ("東映アニメーション", 937, "アニメ製作", "2026/3期", ""),
    ("AOI TYO Holdings", 511, "広告・企業映像", "2020/12期", "その後 非公開化"),
    ("東北新社", 477, "広告・企業映像", "2026/3期", "当社①制作33.6億の比較対象"),
    ("HeyGen", 300, "AI動画・ARR", "$200M（1ドル150円換算）", "$100M→$200M を8ヶ月"),
    ("Synthesia", 210, "AI動画・ARR", "$140M（1ドル150円換算）", "当社②ツール39.6億の比較対象"),
    ("IG Port", 141, "アニメ製作", "2026/5期", ""),
    ("Runway", None, "AI動画", "非開示", "売上を公表していない"),
    ("Technicolor", None, "VFX・ポスプロ", "2026年 経営破綻", "上場していた制作会社は消えつつある"),
]
r = 4
for name, v, kind, src, note in BENCH:
    put(B, r, 1, name)
    put(B, r, 2, v if v is not None else "非開示", fmt="#,##0" if v else None, align="right")
    put(B, r, 3, kind)
    put(B, r, 4, src, font=F_S)
    put(B, r, 5, note, font=F_S)
    r += 1
put(B, r, 1, "【当社 5期（2031年）】", font=F_R)
put(B, r, 2, "=損益計算書!$G$%d/100" % RL["rev"], fmt="#,##0", align="right", font=F_R, fill=KEYBG)
put(B, r, 3, "①制作＋②ツール＋③C2C", font=F_R)
put(B, r, 4, "本計画", font=F_S)
put(B, r, 5, "東北新社477億の約18%。うち①制作は33.6億（同7%）", font=F_S)
r += 2
put(B, r, 1, "① 制作 ÷ 東北新社", font=F_B, border=False)
put(B, r, 2, "=損益計算書!$G$%d/100/477" % RL["p1"], fmt="0.0%", align="right")
r += 1
put(B, r, 1, "② ツール ÷ Synthesia", font=F_B, border=False)
put(B, r, 2, "=損益計算書!$G$%d/100/210" % RL["p2"], fmt="0.0%", align="right")

# ══════════════════════════════════════════════════════════════
# 出所と仮置き
# ══════════════════════════════════════════════════════════════
O = sheet("出所と仮置き", [36, 22, 14, 64])
title(O, "数字の出所と、［仮置き］の一覧",
      "投資家に聞かれて最初に困るのがここ。実測値と仮置きを混ぜないこと。")
header(O, 3, ["項目", "値", "区分", "出所・根拠"])
SRC = [
    ("国内 映像制作市場", "4,580億円", "実測",
     "矢野経済研究所（BtoB映像制作）。動画コンテンツ市場6,300億とは別枠"),
    ("制作費の相場帯", "10〜500万円/本", "実測", "動画幹事・ムビサク（用途別の制作費相場）"),
    ("AI導入による削減率", "▲50〜90%", "当社試算",
     "工程別削減率（企画▲50・撮影▲80・機材▲80・出演▲90・編集▲50・諸経費▲30）を費用構成に当てたもの"),
    ("東証グロース 上場維持基準", "5年経過後 時価総額100億円", "実測",
     "日本取引所グループ。上場基準は改定が続くため準備期に再確認する"),
    ("ベンチマーク各社の売上", "「業界ベンチマーク」シート", "実測",
     "各社の有価証券報告書・決算短信。ARRは各社公表値、1ドル150円換算"),
    ("スキルシェア市場の映像比率", "非公表", "確認不能",
     "ココナラ決算・矢野経済のいずれも映像分野を分離開示していない"),
    ("──────────", "", "", ""),
    ("AX倍率", "1.0 → 4.0倍", "［仮置き］",
     "未実証。計画の最重要前提。3倍でも営業利益率23.3%で成立することを確認済み"),
    ("受注本数カーブ", "54 → 5,594本", "［仮置き］",
     "5期でSAMの1.5%。市場が制約ではなく、作る人が制約"),
    ("1本あたり原価の内訳", "20.5万円（AX4倍時）", "［仮置き］",
     "中国クリエイター12＋ディレクション5＋ツール2＋バッファ1.5"),
    ("ツール外販の契約数", "法人600社／個人17,000人", "［仮置き］",
     "国内の制作会社だけでは届かない。海外展開が前提"),
    ("C2C の GMV", "83億円", "［仮置き］",
     "ココナラの流通高に迫る規模。自動化が効いていることが前提"),
    ("手数料率", "18%", "［仮置き］", "収納代行型。資金決済法の該当性は弁護士に確認中"),
    ("研究開発費", "5期 16億", "［仮置き］", "クラウドGPU・ライセンス・データ基盤"),
    ("実効税率", "30%", "［仮置き］", "繰越欠損金の控除後に適用。税理士に確認する"),
    ("入金・支払サイト", "売掛60日／買掛30日", "［仮置き］", "契約前。ここが延びると資金繰りに直撃する"),
    ("ツール外販の前受期間", "180日", "［仮置き］",
     "年額一括前受の平均残高。月額課金にすると0日になり、資金計画が変わる"),
    ("J-KISS キャップ", "6億円（ポストマネー）", "確定",
     "CAP_TABLE.md 第4章。交渉帯6〜10億。転換時のシード持分は 1.42÷6＝23.7%"),
    ("シリーズA の評価", "post 15億・調達3億", "計画",
     "CAP_TABLE.md 第5章。未交渉。ここが下がると創業者持分も薄まる"),
    ("ESOP枠", "設立時10% → 補充後9.9%", "計画", "税制適格SOの要件は設立時に確認する"),
    ("IPO 公募比率", "20%", "計画",
     "このままでは流通株式比率が20%で、基準25%に5ポイント不足。4期に主幹事と確定させる"),
    ("中国の映像制作パートナー", "社名 ［記入予定］", "未確定", "契約前。権利は日本側に帰属する設計"),
    ("業務委託の契約設計", "─", "未着手", "偽装請負と読まれない設計が必要。1年目に弁護士と作成する"),
]
r = 4
for name, v, kind, note in SRC:
    put(O, r, 1, name, font=F_B if kind == "" else F_N)
    put(O, r, 2, v, align="right")
    put(O, r, 3, kind,
        font=F_R if kind in ("［仮置き］", "未確定", "未着手", "確認不能") else F_N, align="center")
    put(O, r, 4, note, font=F_S)
    r += 1

# ══════════════════════════════════════════════════════════════
# サマリー
# ══════════════════════════════════════════════════════════════
S = wb["Sheet"]
S.title = "サマリー"
for i, w in enumerate([30, 3, 14, 14, 14, 14, 14, 46], start=1):
    S.column_dimensions[get_column_letter(i)].width = w
S.sheet_view.showGridLines = False
title(S, "AI映像制作事業　5年計画サマリー（Ver1.4）",
      "単位：百万円。すべて数式で、「前提」シートを書き換えると連動する。"
      "⚠［仮置き］の前提に乗った計画であり、実績ではない。")
header(S, 3, ["項目", ""] + Y + ["備考"])
r = 4
SUM = [
    ("売上高", "L", "rev", "#,##0", True, "5期 88.1億"),
    ("　① 映像制作", "L", "p1", "#,##0", False, "5,594本 × 60万円。SAMの1.5%"),
    ("　② ツール外販", "L", "p2", "#,##0", False, "法人600社＋個人17,000人。海外展開が前提"),
    ("　③ 越境C2C手数料", "L", "p3", "#,##0", False, "GMV 83億 × 18%"),
    ("売上総利益", "L", "gp", "#,##0", False, ""),
    ("営業利益", "L", "op", "#,##0", True, "3期に損益分岐、4期に通期黒字"),
    ("　営業利益率", "L", "opr", "0.0%", True, ""),
    ("営業キャッシュフロー", "K", "ocf", "#,##0", False, "税・運転資本の後"),
    ("期末キャッシュ残高", "K", "cash", "#,##0", True, "一度もマイナスにならないこと"),
    ("社員数", "L", "heads", "#,##0", False, "業務委託・BPOは含まない"),
    ("売上 / 社員（万円）", "L", "rph", "#,##0", True, "5期 1.44億"),
    ("人手に比例しない収益 比率", "L", "nsr", "0.0%", True, "5期 90%。受託と読まれないための中心指標"),
    ("研究開発費 ÷ 売上", "L", "rndr", "0.0%", False, "5期 18.2%"),
    ("AX倍率", "L", "ax", "0.0", False, "計画の最重要前提［仮置き］。3倍でも成立する"),
]
for label, src, key, fmt, bold, note in SUM:
    put(S, r, 1, label, font=F_B if bold else F_N)
    put(S, r, 2, "")
    for i, c in enumerate(COLS):
        ref = "損益計算書!%s%d" % (c, RL[key]) if src == "L" else "資金計画!%s%d" % (c, RK[key])
        put(S, r, 3 + i, "=" + ref, fmt=fmt, align="right",
            font=F_B if bold else F_N, fill=KEYBG if bold else None)
    put(S, r, 8, note, font=F_S)
    r += 1

r += 1
put(S, r, 1, "シード投資家（1.42億）のリターン", font=F_B, border=False)
r += 1
header(S, r, ["ケース", "", "時価総額(億)", "取り分(億)", "倍率", "IRR", "", "根拠"])
r += 1
for label, src, note in [("ライン別・保守", R_LINE0, "ツール6倍＋C2C4倍＋制作1.5倍"),
                         ("ライン別・中庸", R_LINE0 + 1, "ツール7倍＋C2C5倍＋制作2.0倍"),
                         ("ライン別・強気", R_LINE0 + 2, "ツール8倍＋C2C6倍＋制作2.5倍"),
                         ("全社 PSR 4倍", R_PSR0, "人手に比例しない収益90%を根拠にする"),
                         ("全社 PSR 5倍", R_PSR0 + 1, "")]:
    put(S, r, 1, label, font=F_B)
    put(S, r, 2, "")
    put(S, r, 3, "='資本政策とリターン'!E%d" % src, fmt="#,##0", align="right")
    put(S, r, 4, "='資本政策とリターン'!F%d" % src, fmt="0.00", align="right")
    put(S, r, 5, "='資本政策とリターン'!G%d" % src, fmt=MULT, align="right", font=F_R, fill=KEYBG)
    put(S, r, 6, "='資本政策とリターン'!H%d" % src, fmt="0.0%", align="right")
    put(S, r, 7, "")
    put(S, r, 8, note, font=F_S)
    r += 1
r += 1
put(S, r, 1, "⚠ 上の倍率は事業計画からの逆算であって、投資の推奨でも利回りの保証でもない。"
             "前提の多くは未実証（「出所と仮置き」シート参照）。", font=F_S, border=False)

for ws in wb.worksheets:
    ws.freeze_panes = "A4"
wb.active = 0
wb.save(OUT)
print("書き出し: %s（%d シート）" % (OUT, len(wb.worksheets)))
for ws in wb.worksheets:
    print("  - %s" % ws.title)
