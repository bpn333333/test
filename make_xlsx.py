# -*- coding: utf-8 -*-
"""事業計画を Excel モデルとして書き出す（現行 Ver0.7）

⚠ 版番号は 2026-09-23 に繰り下げた。**1.0 を提出版に充てるため**。
  旧1.4→0.4 / 旧1.5→0.5 / 旧1.6→0.6 / 今回 0.7。
  PPTX「投資家向け企画書 Ver0.8.pptx」は deck/build.js から同じ数値で再生成する。

Ver1.4 との違いは構造。一本値を全部やめ、事業×商品まで割って積み上げている。
  ① 映像制作    4商品（現行支払×値引率）／本数は営業体制から
  ② ツール外販   5SKU・法人は Enterprise / Standard の2階建て＋個人セルフサーブ
  ③ 越境C2C     14商品。下限はクリエイターの留保価格、上限は発注者の支払意思

入力は「前提」と各「商品マスタ」の黄色セルだけ。他は全部そこを参照する数式。

  python make_xlsx.py    ->  事業計画_Ver0.8.xlsx
  python verify_xlsx.py  で plan_v15.py と突き合わせる

  バージョンを上げるときは VERSION を書き換え、「改訂履歴」シートに1行足す。
"""

import re
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

VERSION = "0.8"
OUT = "事業計画_Ver%s.xlsx" % VERSION
Y = ["1期", "2期", "3期", "4期", "5期"]
C5 = ["C", "D", "E", "F", "G"]

INK, VERM, NAVY, MUTED = "16161A", "B3121B", "2A3563", "6E6E76"
HEADBG, INBG, CALCBG, KEYBG, LINE = "2A3563", "FFF6DC", "F4F4F6", "FCE5CD", "DCD9D4"
F_H = Font(name="Yu Gothic", size=10, bold=True, color="FFFFFF")
F_B = Font(name="Yu Gothic", size=10, bold=True, color=INK)
F_N = Font(name="Yu Gothic", size=10, color=INK)
F_S = Font(name="Yu Gothic", size=9, color=MUTED)
F_T = Font(name="Yu Gothic", size=14, bold=True, color=NAVY)
F_R = Font(name="Yu Gothic", size=10, bold=True, color=VERM)
THIN = Side(style="thin", color=LINE)
BOX = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
wb = openpyxl.Workbook()


def sheet(name, widths):
    ws = wb.create_sheet(name)
    for i, w in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.sheet_view.showGridLines = False
    ws.freeze_panes = "A4"
    return ws


def title(ws, t, note=""):
    ws["A1"] = t
    ws["A1"].font = F_T
    if note:
        ws["A2"] = note
        ws["A2"].font = F_S


def header(ws, row, labels, start=1):
    for i, t in enumerate(labels):
        c = ws.cell(row=row, column=start + i, value=t)
        c.font, c.border = F_H, BOX
        c.fill = PatternFill("solid", fgColor=HEADBG)
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws.row_dimensions[row].height = 24


SHEETNAMES = ["前提", "クリエイター経済", "システム原価", "商品マスタ①", "営業体制",
              "商品マスタ②", "商品マスタ③", "人員と人件費", "損益計算書", "資金計画",
              "資本構成の推移", "資本政策とリターン", "業界ベンチマーク", "出所と仮置き",
              "知財・法規制・リスク", "改訂履歴", "サマリー"]


def qref(f):
    """シート参照を必ずクォートする。日本語シート名は引用しないと解釈されない"""
    if not isinstance(f, str) or not f.startswith("="):
        return f
    for nm in SHEETNAMES:
        f = re.sub(r"'?" + re.escape(nm) + r"'?!", "'" + nm + "'!", f)
    return f


def put(ws, r, c, v, fmt=None, font=None, fill=None, align=None, border=True):
    cell = ws.cell(row=r, column=c, value=qref(v))
    cell.font = font or F_N
    if fmt:
        cell.number_format = fmt
    if fill:
        cell.fill = PatternFill("solid", fgColor=fill)
    if align:
        cell.alignment = Alignment(horizontal=align)
    if border:
        cell.border = BOX
    return cell


def band(ws, r, text, font=None):
    put(ws, r, 1, text, font=font or F_B, border=False)


N, M, P = "#,##0", "#,##0.0", "0.0%"
SL_ACC_ROW = 22   # 営業体制シートの「取引アカウント数」行

# ══════════════════════════════════════════════════════════════
# 前提
# ══════════════════════════════════════════════════════════════
PR = sheet("前提", [16, 30, 12, 12, 12, 12, 12, 11, 11, 48])
title(PR, "前提（全社共通の入力）",
      "黄色が入力。商品ごとの単価・件数は各「商品マスタ」シートにある。区分［仮置き］は未実証。")
header(PR, 3, ["大分類", "項目"] + Y + ["単位", "区分", "備考・出所"])
ROWS = [
    ("制作", "AX倍率", [1.0, 1.5, 2.2, 3.0, 4.0], "倍", "［仮置き］",
     "1人あたり制作本数の倍率。計画の最重要前提"),
    ("", "中国クリエイターへの支払", [12, 12, 12, 12, 12], "万円/本", "［仮置き］",
     "難度1.0のとき。実効時給3,000〜6,000円で、③より厚く払う（松田さん決定）"),
    ("", "制作ディレクション（AX前）", [20, 20, 20, 20, 20], "万円/本", "［仮置き］",
     "業務委託。成果物単位なのでAX倍率で除される"),
    ("", "AIツール・素材・レンダリング", [2, 2, 2, 2, 2], "万円/本", "［仮置き］", "クラウドGPU・素材"),
    ("", "品質バッファ（作り直し）", [1.5, 1.5, 1.5, 1.5, 1.5], "万円/本", "［仮置き］", "検収落ちの引当"),
    ("費用", "研究開発費", [30, 120, 450, 1000, 1600], "百万円", "［仮置き］",
     "AX倍率を上げ続けるための投資"),
    ("", "BPO（CS・運用）", [0, 10, 120, 450, 1000], "百万円", "［仮置き］", "社員ではなく外部委託"),
    ("", "獲得費（固定分）", [6, 40, 90, 150, 200], "百万円", "［仮置き］", "C2C発注者の獲得ほか"),
    ("", "獲得費率（①売上比）", [0.06, 0.06, 0.06, 0.06, 0.06], "%", "［仮置き］", "SALES_COST.md"),
    ("", "獲得費率（②売上比）", [0.15, 0.15, 0.15, 0.15, 0.15], "%", "［仮置き］", "営業・CS"),
    ("", "代理店経由の比率（①）", [0.0, 0.053, 0.099, 0.147, 0.159], "%", "計算値",
     "営業体制シートの代理店チャネル ÷ 総本数"),
    ("", "代理店手数料率", [0.15, 0.15, 0.15, 0.15, 0.15], "%", "［仮置き］", "①の代理店チャネルに対して"),
    ("", "その他販管費率（売上比）", [0.04, 0.04, 0.04, 0.04, 0.04], "%", "［仮置き］",
     "オフィス・SaaS・法務"),
    ("", "法定福利費等の負担率", [1.16, 1.16, 1.16, 1.16, 1.16], "倍", "［仮置き］", "年収に対する会社負担"),
    ("資金", "実効税率", [0.30, 0.30, 0.30, 0.30, 0.30], "%", "［仮置き］", "繰越欠損金の控除後"),
    ("", "売上債権 回転日数（①）", [60, 60, 60, 60, 60], "日", "［仮置き］", "検収後の入金サイト"),
    ("", "仕入債務 回転日数（①原価）", [30, 30, 30, 30, 30], "日", "［仮置き］", "制作パートナーへの支払"),
    ("", "ツール外販の前受期間", [180, 180, 180, 180, 180], "日", "［仮置き］", "年額一括前受の平均残高"),
    ("", "設備投資", [0, 0, 0, 0, 0], "百万円", "方針", "クラウド前提。自社設備を持たない"),
    ("", "調達：シード", [150, 0, 0, 0, 0], "百万円", "確定", "J-KISS 1.42億＋代表個人0.08億"),
    ("", "調達：シリーズA", [0, 300, 0, 0, 0], "百万円", "計画", "2期。無いと2期末に資金ショート"),
    ("", "調達：借入", [0, 0, 0, 0, 0], "百万円", "方針", "借入はしない"),
    ("知財", "知財関連費（1期・固定）", [3, 0, 0, 0, 0], "百万円", "★",
     "特許出願（ビジネスモデル特許）＋商標3か国（日・中・台）の初期費用 300万"),
    ("", "知財関連費率（2期以降・売上比）", [0.0, 0.005, 0.005, 0.005, 0.005], "%", "★",
     "出願維持・年金・監視・権利処理。売上の0.5%"),
    ("費用", "貸倒引当率（売上比）", [0.005, 0.005, 0.005, 0.005, 0.005], "%", "★",
     "★0.5〜1%のうち下限を採る。③は収納代行で当社が与信を負わず、②は年額前受。"
     "貸倒が立つのは①の掛売（60日）だけで、①は売上の3割。全社0.5%＝①売上の約1.7%相当"),
    ("", "監査法人費用", [0, 0, 20, 20, 20], "百万円", "★",
     "★上場2年前（3期）から年2,000万。その他販管費の見積からは監査報酬を外してある"),
    ("", "上場関連費用", [0, 0, 0, 0, 100], "百万円", "★",
     "★上場期に1億（主幹事引受手数料・取引所上場料・印刷・株式事務の立ち上げ）"),
]
r = 4
for big, item, vals, unit, kind, note in ROWS:
    put(PR, r, 1, big, font=F_B)
    put(PR, r, 2, item)
    for i, v in enumerate(vals):
        fmt = P if unit == "%" else ("0.00" if unit == "倍" and item.startswith("法定")
                                     else (M if isinstance(v, float) else N))
        put(PR, r, 3 + i, v, fmt=fmt, fill=INBG, align="right")
    put(PR, r, 8, unit, align="center")
    put(PR, r, 9, kind, font=F_R if kind == "［仮置き］" else F_N, align="center")
    put(PR, r, 10, note, font=F_S)
    r += 1
(pAX, pCRE, pDIR, pTOOL, pBUF, pRND, pBPO, pACQF, pACQ1, pACQ2,
 pAGSH, pAGFE, pSGA, pBURD, pTAX, pAR, pAP, pDEF, pCAPEX, pSEED, pSERA, pLOAN,
 pIPFIX, pIPRATE, pBAD, pAUDIT, pIPO) = range(4, 31)


def pf(row, i):
    return "前提!$%s$%d" % (C5[i], row)


# ══════════════════════════════════════════════════════════════
# クリエイター経済
# ══════════════════════════════════════════════════════════════
CR = sheet("クリエイター経済", [32, 16, 12, 14, 52])
title(CR, "クリエイターがいくらなら受けるか — ③の価格下限はここから出る",
      "マーケットプレイスは供給側が受けなければ成立しない。拘束条件はクリエイター側にある。")
header(CR, 3, ["項目", "値", "単位", "区分", "出所・考え方"])
CRV = [
    ("中国 剪辑師 平均月給", 8935, "元/月", "実測", "Indeed 中国（剪辑師の平均薪資）"),
    ("為替", 21, "円/元", "［仮置き］", "2026年の水準"),
    ("月あたり労働時間", 168, "時間", "前提", "21日 × 8時間"),
    ("時給（雇用ベース）", None, "円", "計算", "＝ 月給 × 為替 ÷ 労働時間"),
    ("フリーランス割増", 1.4, "倍", "［仮置き］", "社保なし・不安定・営業時間が無給の補償"),
    ("受注の判断ライン", None, "円/時", "計算", "これを下回ると誰も受けない"),
    ("設計に使う時給（下限）", 1600, "円/時", "★", "判断ラインに余裕を見た額。③の価格下限に使う"),
    ("設計に使う時給（上限）", 3500, "円/時", "★", "熟練クリエイター。月20,000元相当×割増"),
]
r = 4
for name, v, unit, kind, note in CRV:
    put(CR, r, 1, name, font=F_B if kind == "計算" else F_N)
    if name.startswith("時給（雇用"):
        put(CR, r, 2, "=B4*B5/B6", fmt=N, fill=CALCBG, align="right", font=F_B)
    elif name.startswith("受注の判断"):
        put(CR, r, 2, "=B7*B8", fmt=N, fill=CALCBG, align="right", font=F_R)
    else:
        put(CR, r, 2, v, fmt=N if isinstance(v, int) else "0.00", fill=INBG, align="right")
    put(CR, r, 3, unit, align="center")
    put(CR, r, 4, kind, font=F_R if kind in ("［仮置き］", "★") else F_N, align="center")
    put(CR, r, 5, note, font=F_S)
    r += 1
CR_LINE, CR_LO, CR_HI = 9, 10, 11

r += 1
band(CR, r, "必要なクリエイター数 — ここが「なぜ中国か」の答え")
r += 1
header(CR, r, ["項目", "値", "単位", "", "考え方"])
r += 1
CR_H3, CR_H1, CR_FTE, CR_REG = r, r + 1, r + 2, r + 3
put(CR, CR_H3, 1, "③ に必要な年間工数")
put(CR, CR_H3, 2, "='商品マスタ③'!$K$23", fmt=N, fill=CALCBG, align="right")
put(CR, CR_H3, 3, "時間", align="center")
put(CR, CR_H3, 5, "商品別の平均工数 × 件数", font=F_S)
put(CR, CR_H1, 1, "① に必要な年間工数")
put(CR, CR_H1, 2, "='商品マスタ①'!$M$15*1000000/4000", fmt=N, fill=CALCBG, align="right")
put(CR, CR_H1, 3, "時間", align="center")
put(CR, CR_H1, 5, "クリエイター支払総額 ÷ 実効時給4,000円★", font=F_S)
put(CR, CR_FTE, 1, "フル稼働換算", font=F_B)
put(CR, CR_FTE, 2, "=(B%d+B%d)/1800" % (CR_H3, CR_H1), fmt=N, fill=KEYBG, align="right", font=F_B)
put(CR, CR_FTE, 3, "人", align="center")
put(CR, CR_FTE, 5, "1人あたり年1,800時間★", font=F_S)
put(CR, CR_REG, 1, "登録ベース（2〜3倍）", font=F_B)
put(CR, CR_REG, 2, "=B%d*2.5" % CR_FTE, fmt=N, fill=KEYBG, align="right", font=F_B)
put(CR, CR_REG, 3, "人", align="center")
put(CR, CR_REG, 5, "全員が常時稼働はしない★", font=F_S)
r = CR_REG + 1
put(CR, r, 1, "中国の母数（微短劇産業の直接就業者）", font=F_B)
put(CR, r, 2, 690000, fmt=N, fill=INBG, align="right")
put(CR, r, 3, "人", align="center")
put(CR, r, 5, "中国網絡視聴協会 2024。上下流を含めた波及は203万人", font=F_S)
CR_POOL = r
r += 1
put(CR, r, 1, "必要人数 ÷ 母数", font=F_B)
put(CR, r, 2, "=B%d/B%d" % (CR_REG, CR_POOL), fmt="0.00%", fill=KEYBG, align="right", font=F_R)
r += 2
put(CR, r, 1, "同じ人数を日本で、時給1,600〜3,500円で受ける映像クリエイターとして千人規模集めるのは成立しない。"
             "「人が集まるか」が問題にならない場所を選んだ、という設計。これは制約ではなく中国とやる理由。",
    font=F_S, border=False)

# ══════════════════════════════════════════════════════════════
# システム原価
# ══════════════════════════════════════════════════════════════
SC = sheet("システム原価", [26, 10, 10, 11, 11, 11, 11, 11, 10, 34])
title(SC, "③ のシステム原価を商品別に積む",
      "以前ここは「120円/件」と置いていたが根拠がなかった。公表単価から積み直したもの。")
header(SC, 3, ["項目", "値", "単位", "", "", "", "", "", "", "出所"])
SCV = [
    ("ストレージ", 3.66, "円/GB/月", "S3 Standard 東京（1TB/月 ≈ $25）"),
    ("転送", 12.75, "円/GB", "CloudFront 東京（$0.085/GB・1ドル150円）"),
    ("容量", 60, "MB/分", "★1080p H.264 約8Mbps"),
    ("保管期間", 3, "ヶ月", "★検収後"),
    ("版数", 3, "版", "★成果物＋中間版2本"),
    ("転送倍率", 4, "倍", "★プレビュー＋ダウンロード"),
    ("AI-bot", 40.5, "円/件", "★入力30,000＋出力12,000トークン。③-Cのみ"),
    ("アプリ基盤", 31.9, "円/件", "★月30万円 ÷ 年113,000件"),
]
r = 4
for name, v, unit, note in SCV:
    put(SC, r, 1, name)
    put(SC, r, 2, v, fmt="0.00", fill=INBG, align="right")
    put(SC, r, 3, unit, align="center")
    put(SC, r, 10, note, font=F_S)
    r += 1
sSTO, sCDN, sMB, sKEEP, sVER, sTX, sBOT, sAPP = 4, 5, 6, 7, 8, 9, 10, 11

r += 1
band(SC, r, "商品別")
r += 1
header(SC, r, ["商品", "尺(分)", "容量MB", "ストレージ", "転送", "AI-bot", "基盤", "合計", "5期件数", ""])
r += 1
SC0 = r
SCITEMS = [
    ("SNS用ショート", 0.5, 25000, 0), ("誕生日ムービー", 2.0, 12000, 0),
    ("記念日ムービー", 2.5, 8000, 0), ("イベント・余興ムービー", 4.0, 10000, 0),
    ("WEBサイト用", 1.5, 6000, 0), ("ウェディングムービー", 12.0, 9000, 0),
    ("会社紹介ショート", 2.0, 4000, 0), ("採用（小規模・1職種）", 3.0, 2500, 0),
    ("商品・サービス紹介", 2.0, 5000, 0), ("店舗・施設紹介", 1.5, 3500, 0),
    ("展示会・イベント告知", 2.0, 2000, 0), ("SNS広告用（縦型3本）", 1.5, 6000, 0),
    ("個人オーダーメイド", 3.0, 8000, 1), ("企業オーダーメイド", 4.0, 12000, 1),
]
for name, mins, cnt, bot in SCITEMS:
    put(SC, r, 1, name)
    put(SC, r, 2, mins, fmt="0.0", fill=INBG, align="right")
    put(SC, r, 3, "=B%d*$B$%d" % (r, sMB), fmt=N, align="right")
    put(SC, r, 4, "=C%d/1024*$B$%d*$B$%d*$B$%d" % (r, sVER, sKEEP, sSTO), fmt="0.0", align="right")
    put(SC, r, 5, "=C%d/1024*$B$%d*$B$%d" % (r, sTX, sCDN), fmt="0.0", align="right")
    put(SC, r, 6, "=$B$%d" % sBOT if bot else 0, fmt="0.0", align="right")
    put(SC, r, 7, "=$B$%d" % sAPP, fmt="0.0", align="right")
    put(SC, r, 8, "=SUM(D%d:G%d)" % (r, r), fmt="0.0", align="right", font=F_B)
    put(SC, r, 9, cnt, fmt=N, align="right")
    r += 1
SC1 = r - 1
put(SC, r, 1, "加重平均（円/件）", font=F_B)
put(SC, r, 8, "=SUMPRODUCT(H%d:H%d,I%d:I%d)/SUM(I%d:I%d)" % (SC0, SC1, SC0, SC1, SC0, SC1),
    fmt="0.0", fill=KEYBG, align="right", font=F_B)
SC_AVG = r
r += 2
put(SC, r, 1, "尺が長いものほど重く、AI-botは③-Cだけに乗る。安い商品ほど手数料に占める割合が大きい。",
    font=F_S, border=False)

# ══════════════════════════════════════════════════════════════
# 商品マスタ①
# ══════════════════════════════════════════════════════════════
M1 = sheet("商品マスタ①", [26, 12, 10, 12, 12, 9, 12, 9, 9, 9, 9, 9, 9, 13, 24])
title(M1, "① 映像制作 — 商品別",
      "当社価格は「企業の現行支払 × (1−値引率)」。顧客が浮かせる額がそのまま提案の中身になる。"
      "平均単価と平均難度は構成比から導出される。")
header(M1, 3, ["商品", "現行支払", "値引率", "当社単価", "顧客削減", "難度", "原価@AX4", "粗利率"]
       + ["構成比 " + y for y in Y] + ["主な販路"])
S1 = [
    ("ブランドムービー・Web CM", 500, 0.50, 3.00, [0.04, 0.08, 0.12, 0.13, 0.15], "直販"),
    ("企業VP・採用（ブランド型）", 200, 0.50, 1.80, [0.25, 0.28, 0.31, 0.34, 0.35], "直販・代理店"),
    ("企業VP・会社紹介（標準）", 100, 0.50, 1.00, [0.46, 0.42, 0.38, 0.36, 0.35], "代理店・インバウンド"),
    ("展示会・社内イベント映像", 60, 0.50, 0.80, [0.25, 0.22, 0.19, 0.17, 0.15], "制作会社経由"),
]
r = 4
M1_0 = r
for name, cur, disc, k, mix, ch in S1:
    put(M1, r, 1, name)
    put(M1, r, 2, cur, fmt=N, fill=INBG, align="right")
    put(M1, r, 3, disc, fmt=P, fill=INBG, align="right")
    put(M1, r, 4, "=B%d*(1-C%d)" % (r, r), fmt=M, fill=CALCBG, align="right", font=F_B)
    put(M1, r, 5, "=B%d-D%d" % (r, r), fmt=M, align="right")
    put(M1, r, 6, k, fmt="0.00", fill=INBG, align="right")
    put(M1, r, 7, "=F%d*(前提!$G$%d+前提!$G$%d/前提!$G$%d+前提!$G$%d+前提!$G$%d)"
        % (r, pCRE, pDIR, pAX, pTOOL, pBUF), fmt=M, align="right")
    put(M1, r, 8, "=1-G%d/D%d" % (r, r), fmt=P, align="right")
    for i, m in enumerate(mix):
        put(M1, r, 9 + i, m, fmt=P, fill=INBG, align="right")
    put(M1, r, 14, ch, font=F_S)
    r += 1
M1_1 = r - 1
LBL = ["構成比 合計", "平均単価（万円）", "平均難度係数", "1本あたり原価（万円）",
       "受注本数（営業体制シート）", "① 売上（百万円）", "顧客が浮かせる額（百万円）",
       "クリエイター支払総額（百万円）"]
for j, lab in enumerate(LBL):
    rr = r + j
    put(M1, rr, 1, lab, font=F_B)
    for i, c in enumerate(C5):
        col = get_column_letter(9 + i)
        if j == 0:
            f = "=SUM(%s%d:%s%d)" % (col, M1_0, col, M1_1)
            fmt = P
        elif j == 1:
            f = "=SUMPRODUCT($D$%d:$D$%d,%s%d:%s%d)" % (M1_0, M1_1, col, M1_0, col, M1_1)
            fmt = M
        elif j == 2:
            f = "=SUMPRODUCT($F$%d:$F$%d,%s%d:%s%d)" % (M1_0, M1_1, col, M1_0, col, M1_1)
            fmt = "0.00"
        elif j == 3:
            f = "=%s%d*(前提!$%s$%d+前提!$%s$%d/前提!$%s$%d+前提!$%s$%d+前提!$%s$%d)" % (
                col, r + 2, c, pCRE, c, pDIR, c, pAX, c, pTOOL, c, pBUF)
            fmt = M
        elif j == 4:
            f = "=営業体制!%s$19" % c
            fmt = N
        elif j == 5:
            f = "=%s%d*%s%d/100" % (col, r + 4, col, r + 1)
            fmt = N
        elif j == 6:
            f = "=%s%d*SUMPRODUCT($E$%d:$E$%d,%s%d:%s%d)/100" % (
                col, r + 4, M1_0, M1_1, col, M1_0, col, M1_1)
            fmt = N
        else:
            f = "=%s%d*%s%d*前提!$%s$%d/100" % (col, r + 4, col, r + 2, c, pCRE)
            fmt = N
        put(M1, rr, 9 + i, f, fmt=fmt, align="right",
            fill=KEYBG if j in (1, 5) else CALCBG, font=F_B if j in (1, 5) else F_N)
M1_PRICE, M1_DIFF, M1_CU, M1_UNITS, M1_REV, M1_SAVE, M1_CREPAY = r + 1, r + 2, r + 3, r + 4, r + 5, r + 6, r + 7

band(M1, 17, "ACV / ARR — ①は案件ベースなので、そのままではARRにならない")
header(M1, 18, ["項目", "", "", "", "", "", "", "", "1期", "2期", "3期", "4期", "5期", "考え方"])
put(M1, 22, 1, "年間リテイナー契約の比率", font=F_B)
put(M1, 22, 2, 0.00, fmt=P, fill=INBG, align="right")
put(M1, 22, 14, "★「年◯本でいくら」の包括契約にした分だけARRに入る。いまは0", font=F_S)
M1_RET = 22
A1 = [
    (19, "取引アカウント数", "=営業体制!C{acc}", "営業体制シート"),
    (20, "アカウントあたり年間取引額（万円）", "=IF(I19=0,0,I13*100/I19)",
     "ACV相当。ただし契約ではなく案件の集まり"),
    (21, "① ARR（百万円）", "=I13*$B$22", "リテイナー契約分のみ。スポット受注はARRではない"),
    (23, "① 非継続（百万円）", "=I13-I21", "案件ごとの発注。毎年の継続は保証されない"),
]
for rr, name, f, note in A1:
    put(M1, rr, 1, name, font=F_B if "ARR" in name else F_N)
    for i, c in enumerate(C5):
        col = get_column_letter(9 + i)
        ff = f.replace("{acc}", str(SL_ACC_ROW)).replace("C{", c + "{")
        ff = ff.replace("営業体制!C", "営業体制!" + c).replace("I1", col + "1").replace("I2", col + "2")
        put(M1, rr, 9 + i, ff, fmt=N, align="right",
            fill=KEYBG if "ARR" in name else CALCBG,
            font=F_B if "ARR" in name else F_N)
    put(M1, rr, 14, note, font=F_S)
put(M1, 25, 1, "①は1本ごとの発注で、翌年も同じ社が同じ本数を出す義務はない。"
             "だから「1社あたり年567万」はACV相当ではあってもARRではない。"
             "年間包括（リテイナー）契約を商品として作れば、その分はARRに算入できる。★要判断",
    font=F_S, border=False)

# ══════════════════════════════════════════════════════════════
# 営業体制
# ══════════════════════════════════════════════════════════════
SL = sheet("営業体制", [30, 3, 12, 12, 12, 12, 12, 46])
title(SL, "① の受注本数を、営業体制から積む",
      "市場シェアは結果であって計画の根拠にはならない。単位は「本」ではなく「アカウント」。"
      "企業は年に何本も出すので、取引社数 × 1社あたり本数で積む。")
header(SL, 3, ["項目", ""] + Y + ["考え方"])
SLD = [
    ("1 直販", None, None),
    ("　事業開発（名）", [1, 2, 4, 5, 6], "人員計画シートと同じ"),
    ("　1名あたり担当社数", [15, 25, 35, 40, 40], "★エンタープライズ営業の標準的な担当数"),
    ("　1社あたり年間本数", [4, 5, 6, 6, 6], "★採用・展示会・製品・IRで年6本"),
    ("　小計（本）", "=C5*C6*C7", None),
    ("2 制作会社経由", None, None),
    ("　②の法人契約数", "=商品マスタ②!C21", "②を売ることが①の営業になっている"),
    ("　うち発注もする割合", [0.0, 0.20, 0.25, 0.30, 0.30], "★手に余る案件を当社に流す"),
    ("　1社あたり年間本数", [0, 6, 7, 8, 8], "★"),
    ("　小計（本）", "=ROUND(C10*C11*C12,0)", None),
    ("3 代理店経由", None, None),
    ("　提携代理店数", [0, 2, 10, 25, 40], "★広告代理店・人材会社"),
    ("　1社あたり年間本数", [0, 8, 12, 15, 15], "★"),
    ("　小計（本）", "=C15*C16", None),
    ("4 インバウンド（本）", [0, 20, 80, 200, 300], "★事例と検索から"),
]
r = 4
for name, vals, note in SLD:
    put(SL, r, 1, name, font=F_B if vals is None or isinstance(vals, str) else F_N)
    put(SL, r, 2, "")
    if vals is None:
        pass
    elif isinstance(vals, str):
        for i, c in enumerate(C5):
            put(SL, r, 3 + i, vals.replace("C", c), fmt=N, align="right", font=F_B, fill=CALCBG)
    else:
        for i, v in enumerate(vals):
            put(SL, r, 3 + i, v, fmt=P if isinstance(v, float) else N, fill=INBG, align="right")
    if note:
        put(SL, r, 8, note, font=F_S)
    r += 1
SL_TOT = r
put(SL, SL_TOT, 1, "受注本数 合計", font=F_B)
put(SL, SL_TOT, 2, "")
for i, c in enumerate(C5):
    put(SL, SL_TOT, 3 + i, "=%s8+%s13+%s17+%s18" % (c, c, c, c), fmt=N,
        fill=KEYBG, align="right", font=F_B)
r = SL_TOT + 2
band(SL, r, "取引社数と1社あたり")
r += 1
SL_ACC = r
put(SL, r, 1, "取引アカウント数", font=F_B)
put(SL, r, 2, "")
for i, c in enumerate(C5):
    put(SL, r, 3 + i, "=%s5*%s6+ROUND(%s10*%s11,0)+%s15" % (c, c, c, c, c),
        fmt=N, align="right", fill=CALCBG)
put(SL, r, 8, "直販で持つのは一部だけ。残りはチャネル経由", font=F_S)
r += 1
put(SL, r, 1, "1社あたり年間取引額（万円）", font=F_B)
put(SL, r, 2, "")
for i, c in enumerate(C5):
    col = get_column_letter(9 + i)
    put(SL, r, 3 + i, "=IF(%s%d=0,0,商品マスタ①!%s%d*100/%s%d)" % (c, SL_ACC, col, M1_REV, c, SL_ACC),
        fmt=N, align="right", fill=CALCBG)
r += 1
put(SL, r, 1, "直販が①売上に占める比率", font=F_B)
put(SL, r, 2, "")
for i, c in enumerate(C5):
    col = get_column_letter(9 + i)
    put(SL, r, 3 + i, "=IF(商品マスタ①!%s%d=0,0,%s8*商品マスタ①!%s%d/100/商品マスタ①!%s%d)"
        % (col, M1_REV, c, col, M1_PRICE, col, M1_REV), fmt=P, align="right", fill=CALCBG)
put(SL, r, 8, "営業人数に比例しない売り方になっているか", font=F_S)


# ══════════════════════════════════════════════════════════════
# 商品マスタ②
# ══════════════════════════════════════════════════════════════
M2 = sheet("商品マスタ②", [30, 16, 12, 12, 12, 12, 12, 10, 10, 40])
title(M2, "② 制作ツール外販 — 商品別",
      "チェックポイントと工程ツールは別売り。LoRA個別構築は②の売上。法人は Enterprise / Standard の2階建て。"
      "★単価・席数・構成比は提案値。")
header(M2, 3, ["商品", "課金形態", "単価(万円)", "継続/一過性", "", "", "", "", "", "中身"])
SKU2 = [
    ("チェックポイント Enterprise", "年額", 300, "継続", "全業種・商用利用"),
    ("チェックポイント Standard", "年額", 100, "継続", "1業種"),
    ("工程ツール（要件定義・自動チェック）", "月額2万/席", 24, "継続", "1席あたり年額"),
    ("LoRA 年間保守", "年額", 24, "継続", "追加学習モデルの更新・再学習"),
    ("LoRA 個別構築", "初期・都度", 80, "一過性", "毎年は発生しない。ARRには入らない"),
]
r = 4
for name, kind, price, rec, note in SKU2:
    put(M2, r, 1, name)
    put(M2, r, 2, kind, align="center")
    put(M2, r, 3, price, fmt=N, fill=INBG, align="right")
    put(M2, r, 4, rec, align="center", font=F_R if rec == "一過性" else F_N)
    put(M2, r, 10, note, font=F_S)
    r += 1
m2CPE, m2CPS, m2TOOL, m2LORAM, m2LORAB = 4, 5, 6, 7, 8

band(M2, 10, "プラン構成")
header(M2, 11, ["プラン", "チェックポイント", "工程ツール", "LoRA保守", "年額計", "席数", "", "", "", ""])
for i, (nm, cp, seats) in enumerate([("Enterprise", m2CPE, 10), ("Standard", m2CPS, 3)]):
    rr = 12 + i
    put(M2, rr, 1, nm, font=F_B)
    put(M2, rr, 2, "=C%d" % cp, fmt=N, align="right")
    put(M2, rr, 3, "=C%d*F%d" % (m2TOOL, rr), fmt=N, align="right")
    put(M2, rr, 4, "=C%d" % m2LORAM, fmt=N, align="right")
    put(M2, rr, 5, "=SUM(B%d:D%d)" % (rr, rr), fmt=N, fill=KEYBG, align="right", font=F_B)
    put(M2, rr, 6, seats, fmt=N, fill=INBG, align="right")
m2ENT, m2STD = 12, 13
put(M2, 15, 1, "LoRA個別構築の付帯率", font=F_B)
put(M2, 15, 2, 0.25, fmt=P, fill=INBG, align="right")
put(M2, 15, 3, "=C%d*B15" % m2LORAB, fmt=N, fill=CALCBG, align="right", font=F_B)
put(M2, 15, 10, "新規契約の25%が初年度に発注★", font=F_S)

band(M2, 17, "期別")
header(M2, 18, ["項目", ""] + Y + ["", "", "考え方"])
M2D = [
    (19, "新規獲得 法人（社）", [0, 15, 85, 220, 280], None, "★海外展開が前提"),
    (20, "★ 法人の年次解約率", [0.0, 0.05, 0.05, 0.05, 0.05], None,
     "★年5%（松田さん指示）。B2B SaaSの一般水準（5〜15%）の下限"),
    (21, "法人契約数（期末）", None, "=ROUND({p}21*(1-{c}20)+{c}19,0)", "前期末×(1−解約率)＋新規"),
    (22, "Enterprise比率", [0.0, 0.13, 0.20, 0.25, 0.30], None, "★事例が増えるほど上位プランが取れる"),
    (23, "　Enterprise 社数", None, "=ROUND({c}21*{c}22,0)", ""),
    (24, "　Standard 社数", None, "={c}21-{c}23", ""),
    (25, "積み上げACV（万円）", None, "=IF({c}21=0,0,({c}23*$E$12+{c}24*$E$13)/{c}21+$C$15)", "一本値ではなく積み上げ"),
    (26, "法人売上（百万円）", None, "={c}21*{c}25/100", ""),
    (27, "新規獲得 個人（人）", [0, 0, 2000, 6000, 9000], None, "★プロクリエイター"),
    (28, "★ 個人の年次解約率", [0.0, 0.30, 0.30, 0.30, 0.30], None,
     "★年30%（松田さん指示）。個人向けSaaSの一般水準（月3〜5%＝年30〜45%）の下限側"),
    (29, "個人契約数（期末）", None, "=ROUND({p}29*(1-{c}28)+{c}27,0)", "前期末×(1−解約率)＋新規"),
    (30, "個人ACV（万円）", [12, 12, 12, 12, 12], None, "月1万円（チェックポイント6千＋工程ツール4千）"),
    (31, "個人売上（百万円）", None, "={c}29*{c}30/100", ""),
]
for rr, name, vals, f, note in M2D:
    put(M2, rr, 1, name, font=F_R if name.startswith("★") else (F_B if f else F_N))
    put(M2, rr, 2, "")
    for i2, c in enumerate(C5):
        if vals is not None:
            put(M2, rr, 3 + i2, vals[i2], fmt=P if isinstance(vals[i2], float) else N,
                fill=INBG, align="right")
        else:
            prev = C5[i2 - 1] if i2 else None
            if rr == 21 and i2 == 0:
                ff = "=%s19" % c
            elif rr == 29 and i2 == 0:
                ff = "=%s27" % c
            else:
                ff = f.format(c=c, p=prev)
            put(M2, rr, 3 + i2, ff, fmt=N, align="right", fill=CALCBG,
                font=F_B if "売上" in name else F_N)
    put(M2, rr, 10, note, font=F_S)
m2CORPREV, m2INDREV = 26, 31

band(M2, 33, "②-C 個人セルフサーブ（用途特化・フリーミアム）")
header(M2, 34, ["項目", ""] + Y + ["", "", "考え方"])
M2S = [
    (35, "登録ユーザー（累計）", [0, 30000, 120000, 280000, 500000], None, "★テンプレートは③-Aの6商品に固定"),
    (36, "有料転換率", [0.0, 0.05, 0.06, 0.07, 0.08], None, "★"),
    (37, "　有料ユーザー", None, "=ROUND({c}35*{c}36,0)", ""),
    (38, "ARPPU（円/年）", [0, 4000, 4000, 4000, 4000], None, "★都度1,500円/本と月額980円の混合"),
    (39, "②-C 売上（百万円）", None, "={c}37*{c}38/1000000", ""),
    (40, "年間出力本数（データ）", None, "=ROUND({c}37*2.5,0)", "却下された中間生成物も学習に回る"),
]
for rr, name, vals, f, note in M2S:
    put(M2, rr, 1, name)
    put(M2, rr, 2, "")
    for i2, c in enumerate(C5):
        if vals is not None:
            put(M2, rr, 3 + i2, vals[i2], fmt=P if isinstance(vals[i2], float) else N,
                fill=INBG, align="right")
        else:
            put(M2, rr, 3 + i2, f.format(c=c), fmt=N, align="right", fill=CALCBG,
                font=F_B if "売上" in name else F_N)
    put(M2, rr, 10, note, font=F_S)
m2SELF = 39

put(M2, 42, 1, "② 売上 合計（百万円）", font=F_B)
put(M2, 42, 2, "")
for i2, c in enumerate(C5):
    put(M2, 42, 3 + i2, "=%s%d+%s%d+%s%d" % (c, m2CORPREV, c, m2INDREV, c, m2SELF),
        fmt=N, fill=KEYBG, align="right", font=F_B)
m2REV = 42
put(M2, 43, 1, "② 粗利率", font=F_B)
put(M2, 43, 2, 0.80, fmt=P, fill=INBG, align="right")
put(M2, 43, 10, "★ソフトウェア外販の一般水準", font=F_S)
m2GPR = 43

band(M2, 45, "ARRベース（継続課金のみ）— Synthesia・HeyGenと同じ土俵で比べるための行")
header(M2, 46, ["項目", ""] + Y + ["", "", "考え方"])
put(M2, 51, 1, "②-C のうち継続課金の比率", font=F_B)
put(M2, 51, 2, 0.50, fmt=P, fill=INBG, align="right")
put(M2, 51, 10, "★月額980円と都度1,500円/本の混合。都度分はARRに入らない", font=F_S)
m2SUBSH = 51
ARRD = [
    (47, "法人ARR / 社（万円）", "=IF({c}21=0,0,{c}25-$C$15)", "積み上げACVから LoRA個別構築の20万を除く"),
    (48, "法人ARR（百万円）", "={c}21*{c}47/100", ""),
    (49, "② ARR 合計（百万円）", "={c}48+{c}31+{c}39*$B$51", "法人ARR ＋ 個人 ＋ セルフサーブの継続分"),
    (50, "一過性収入（百万円）", "={c}42-{c}49", "LoRA個別構築とセルフサーブの都度課金"),
]
for rr, name, f, note in ARRD:
    put(M2, rr, 1, name, font=F_B if "合計" in name else F_N)
    put(M2, rr, 2, "")
    for i2, c in enumerate(C5):
        put(M2, rr, 3 + i2, f.format(c=c), fmt=N, align="right",
            fill=KEYBG if "ARR 合計" in name else CALCBG,
            font=F_B if "ARR 合計" in name else F_N)
    if note:
        put(M2, rr, 10, note, font=F_S)
m2ARR = 49
put(M2, 53, 1, "★ 解約率を入れたので、契約数は「新規獲得 − 解約」の純増になる。"
             "累計獲得は法人600社・個人17,000人だが、解約を引いた5期末は法人578社・個人14,180人。"
             "差の22社・2,820人は、維持するなら解約分を上乗せして獲得し続ける必要がある。",
    font=F_R, border=False)
put(M2, 55, 1, "②-C はここに置く（③ではなく）。ツール事業の倍率が当たる側で、会社の形も3事業のまま保てる。",
    font=F_S, border=False)

# ══════════════════════════════════════════════════════════════
# 商品マスタ③
# ══════════════════════════════════════════════════════════════
M3 = sheet("商品マスタ③", [26, 7, 7, 9, 9, 12, 12, 12, 13, 11, 12, 13, 32])
title(M3, "③ 越境C2C — 商品別",
      "ToC・ToBとも**上限＝需要側の支払意思**で成約。区分は買い手の違いを示すためだけに残している。"
      "下限はクリエイターの留保価格で、下回ると供給が付かないという床。".replace("**", ""))
header(M3, 3, ["商品", "分類", "区分", "参考 軽い場合", "標準工数", "下限（供給）", "上限（需要）",
               "中点", "採用価格", "5期件数", "年間工数", "5期GMV(百万)", "上限の根拠"])
S3 = [
    ("SNS用ショート", "A", "ToC", 0.5, 1.5, 10000, 25000, "個人の動画編集外注 5千〜3万の下側"),
    ("誕生日ムービー", "A", "ToC", 1.0, 2.5, 15000, 12000, "サプライズ動画 数千〜2万"),
    ("記念日ムービー", "A", "ToC", 1.0, 3.0, 18000, 8000, "還暦・退職。誕生日より重い"),
    ("イベント・余興ムービー", "A", "ToC", 2.0, 5.0, 30000, 10000, "二次会・余興 1〜5万"),
    ("WEBサイト用", "A", "ToC", 3.0, 8.0, 50000, 6000, "個人事業主のサイト用 3〜10万"),
    ("ウェディングムービー", "A", "ToC", 5.0, 15.0, 80000, 9000, "結婚式ムービー外注 3〜10万"),
    ("会社紹介ショート", "B", "ToB", 6.0, 12.0, 120000, 4000, "①の当社価格50万の1/4"),
    ("採用（小規模・1職種）", "B", "ToB", 8.0, 16.0, 180000, 2500, "①の当社価格100万の1/5〜1/6"),
    ("商品・サービス紹介", "B", "ToB", 6.0, 14.0, 150000, 5000, "機能数で振れる"),
    ("店舗・施設紹介", "B", "ToB", 5.0, 10.0, 100000, 3500, "撮影なし・生成のみ"),
    ("展示会・イベント告知", "B", "ToB", 4.0, 9.0, 80000, 2000, "①の当社価格30万の1/4"),
    ("SNS広告用（縦型3本）", "B", "ToB", 6.0, 12.0, 120000, 6000, "3本セット"),
    ("個人オーダーメイド", "C", "ToC", 3.0, 10.0, 150000, 5900, "パッケージに収まらない個別要望"),
    ("企業オーダーメイド", "C", "ToB", 10.0, 50.0, 1000000, 8900, "上限100万。交渉が入る"),
]
r = 5
for name, grp, seg, hmin, hmax, pmax, cnt, why in S3:
    put(M3, r, 1, name)
    put(M3, r, 2, grp, align="center", font=F_B)
    put(M3, r, 3, seg, align="center", font=F_R if seg == "ToC" else F_N, fill=INBG)
    put(M3, r, 4, hmin, fmt="0.0", fill=INBG, align="right")
    put(M3, r, 5, hmax, fmt="0.0", fill=INBG, align="right")
    put(M3, r, 6, "=ROUNDUP(クリエイター経済!$B$10*E%d/(1-$B$28)/500,0)*500" % r,
        fmt=N, fill=CALCBG, align="right")
    put(M3, r, 7, pmax, fmt=N, fill=INBG, align="right")
    put(M3, r, 8, "=(F%d+G%d)/2" % (r, r), fmt=N, align="right", font=F_S)
    put(M3, r, 9, "=G%d" % r, fmt=N, fill=KEYBG, align="right", font=F_B)
    put(M3, r, 10, cnt, fmt=N, fill=INBG, align="right")
    put(M3, r, 11, "=E%d*J%d" % (r, r), fmt=N, align="right")
    put(M3, r, 12, "=I%d*J%d/1000000" % (r, r), fmt=M, align="right")
    put(M3, r, 13, why, font=F_S)
    r += 1
for i2, (g, lab) in enumerate([("A", "小計 ③-A 個人パッケージ"), ("B", "小計 ③-B 中小企業"),
                               ("C", "小計 ③-C オーダーメイド")]):
    rr = 20 + i2
    put(M3, rr, 1, lab, font=F_B)
    put(M3, rr, 2, g, align="center", font=F_B)
    for col, ch in [(10, "J"), (11, "K"), (12, "L")]:
        put(M3, rr, col, '=SUMIF($B$5:$B$18,"%s",%s$5:%s$18)' % (g, ch, ch),
            fmt=M if col == 12 else N, align="right", font=F_B, fill=CALCBG)
put(M3, 23, 1, "合計（②-Cの共食い前）", font=F_B)
for col, ch in [(10, "J"), (11, "K"), (12, "L")]:
    put(M3, 23, col, "=SUM(%s20:%s22)" % (ch, ch), fmt=M if col == 12 else N,
        align="right", font=F_B, fill=KEYBG)
m3A, m3B, m3C, m3TOT = 20, 21, 22, 23
put(M3, 24, 1, "　− ②-Cセルフサーブによる共食い（③-A）", font=F_N)
put(M3, 24, 12, "=-L20*G35", fmt=M, align="right", font=F_R)
put(M3, 24, 13, "③-Aの安い帯が②-Cに流れる分。下の期別GMVはこれを引いた後", font=F_S)
put(M3, 25, 1, "5期GMV（共食い後）＝下の期別G列と一致", font=F_B)
put(M3, 25, 12, "=L23+L24", fmt=M, align="right", font=F_B, fill=KEYBG)

band(M3, 27, "手数料と原価率")
for i, (lab, v, note) in enumerate([
        ("手数料率", 0.30, "一律30%。70%をクリエイターに渡す（松田さん決定）"),
        ("決済手数料率", 0.0318, "Stripe 国内カード3.6%／銀行振込1.5% を 80:20 で加重"),
        ("送金・為替", 0.03, "中国の制作パートナー経由（松田さん指示）")]):
    rr = 28 + i
    put(M3, rr, 1, lab, font=F_B)
    put(M3, rr, 2, v, fmt="0.00%", fill=INBG, align="right")
    put(M3, rr, 11, note, font=F_S)
m3TAKE, m3PAY, m3REMIT = 28, 29, 30

band(M3, 30, "期別")
header(M3, 31, ["項目", ""] + Y + ["", "", "考え方"])
M3D = [
    ("ランプ ③-A", [0.01, 0.07, 0.28, 0.62, 1.00], "1期から。仲介が要らない"),
    ("ランプ ③-B", [0.00, 0.04, 0.22, 0.58, 1.00], "2期から"),
    ("ランプ ③-C", [0.00, 0.00, 0.15, 0.55, 1.00], "3期から。AI-botの開発後"),
    ("②-Cセルフサーブの共食い係数", [0.000, 0.007, 0.032, 0.088, 0.180], "③-Aの件数に対して"),
]
r = 32
for name, vals, note in M3D:
    put(M3, r, 1, name)
    put(M3, r, 2, "")
    for i, c in enumerate(C5):
        put(M3, r, 3 + i, vals[i], fmt=P, fill=INBG, align="right")
    put(M3, r, 11, note, font=F_S)
    r += 1
m3RA, m3RB, m3RC, m3CAN = 32, 33, 34, 35

ROWS3 = [
    ("③-A GMV（百万円）", "=$L$20*C32*(1-C35)"),
    ("③-B GMV（百万円）", "=$L$21*C33"),
    ("③-C GMV（百万円）", "=$L$22*C34"),
    ("GMV 合計", "=C36+C37+C38"),
    ("取引件数", "=$J$20*C32*(1-C35)+$J$21*C33+$J$22*C34"),
    ("③ 売上（手数料30%）", "=C39*$B$28"),
    ("　− 決済・送金・システム", "=C39*($B$29+$B$30)+C40*システム原価!$H$%d/1000000" % SC_AVG),
    ("売上総利益", "=C41-C42"),
    ("年間工数（時間）", "=$K$20*C32*(1-C35)+$K$21*C33+$K$22*C34"),
]
r = 36
for name, f in ROWS3:
    put(M3, r, 1, name, font=F_B if "合計" in name or "売上" in name else F_N)
    put(M3, r, 2, "")
    for i, c in enumerate(C5):
        ff = f
        for src, dst in [("C3", c + "3"), ("C4", c + "4")]:
            ff = ff.replace(src, dst)
        put(M3, r, 3 + i, ff, fmt=N, align="right",
            fill=KEYBG if name.startswith("③ 売上") or name.startswith("売上総") else CALCBG,
            font=F_B if name.startswith("③ 売上") or name.startswith("売上総") else F_N)
    r += 1
m3GMV, m3CNT, m3REV, m3COGS, m3GP, m3HRS = 39, 40, 41, 42, 43, 44
put(M3, 46, 1, "⚠ 全商品が上限で成約する前提。下限（クリエイターの留保価格）との差がそのまま利幅になる。"
             "供給が厚いほど競争で下限側に寄るのが市場の常なので、ここは最も強気の置き方。"
             "中点なら③のGMVは上限の約59%、全部が下限なら約18%になる。", font=F_R, border=False)


band(M3, 47, "ACV / ARR — ③は取引ベースなのでARRはゼロ")
header(M3, 48, ["項目", ""] + Y + ["", "", "考え方"])
for rr, name, f, note in [
        (49, "③ ARR（百万円）", "=0", "取引手数料。契約ではないのでARRに算入できない"),
        (50, "③ 非継続（百万円）", "=C41", "全額が取引ベース")]:
    put(M3, rr, 1, name, font=F_B)
    put(M3, rr, 2, "")
    for i, c in enumerate(C5):
        put(M3, rr, 3 + i, f.replace("C4", c + "4"), fmt=N, align="right", fill=CALCBG)
    put(M3, rr, 11, note, font=F_S)
put(M3, 52, 1, "マーケットプレイスはARRでは評価されない。見るのは GMV・取引件数・手数料率・"
             "そして発注者のリピート率。リピート率はまだモデルに入っていない。★次に詰めるならここ",
    font=F_S, border=False)

# ══════════════════════════════════════════════════════════════
# 人員と人件費
# ══════════════════════════════════════════════════════════════
H = sheet("人員と人件費", [28, 12, 11, 11, 11, 11, 11, 52])
title(H, "人員と人件費（社員はPM中心）",
      "開発は中国・ベトナム・東欧への業務委託。社員として抱えるのはPM。"
      "制作ディレクション・CS・オペレーションも業務委託／BPO。管理はAX化で極小。")
header(H, 3, ["職種", "年収(万円)"] + Y + ["考え方"])
ROLES = [
    ("経営・CxO", 900, [1, 1, 2, 3, 3], "代表＋CFO／CTO級"),
    ("モデル開発PM", 950, None, "オフショアチームを率いる。人数はAX後のエンジニア数から逆算"),
    ("制作統括", 650, [1, 2, 3, 3, 3], "業務委託ディレクターの束ね役"),
    ("事業開発・アライアンス", 700, [1, 2, 4, 5, 6], "営業体制シートの直販人員と同じ"),
    ("クリエイターネットワーク統括", 600, [1, 1, 2, 3, 3], "中国パートナー・登録クリエイター管理"),
    ("管理・コーポレート", 550, [0, 1, 1, 2, 3], "AX化で極小。取引処理はBPO、専門領域は社外の顧問"),
]
r = 4
for name, pay, heads, note in ROLES:
    put(H, r, 1, name)
    put(H, r, 2, pay, fmt=N, fill=INBG, align="right")
    for i, c in enumerate(C5):
        if heads is None:
            put(H, r, 3 + i, "=%s41" % c, fmt=N, fill=CALCBG, align="right", font=F_B)
        else:
            put(H, r, 3 + i, heads[i], fmt=N, fill=INBG, align="right")
    put(H, r, 8, note, font=F_S)
    r += 1
HR0, HR1 = 4, r - 1
HHEADS, HPAY, HAVG = r, r + 1, r + 2
for rr, lab in [(HHEADS, "社員数 合計"), (HPAY, "人件費（百万円）"), (HAVG, "1人あたり人件費（万円）")]:
    put(H, rr, 1, lab, font=F_B)
for i, c in enumerate(C5):
    put(H, HHEADS, 3 + i, "=SUM(%s%d:%s%d)" % (c, HR0, c, HR1), fmt=N, fill=KEYBG,
        align="right", font=F_B)
    put(H, HPAY, 3 + i, "=SUMPRODUCT($B$%d:$B$%d,%s%d:%s%d)*%s/100"
        % (HR0, HR1, c, HR0, c, HR1, pf(pBURD, i)), fmt=N, fill=CALCBG, align="right", font=F_B)
    put(H, HAVG, 3 + i, "=IF(%s%d=0,0,%s%d*100/%s%d)" % (c, HHEADS, c, HPAY, c, HHEADS),
        fmt=N, fill=CALCBG, align="right")
r = HAVG + 2
band(H, r, "参考：社員ではない人たち")
r += 1
header(H, r, ["区分", ""] + Y + ["考え方"])
HGIG = r + 1
put(H, HGIG, 1, "業務委託ディレクション（人）")
put(H, HGIG, 8, "本数 ×（1/120＋1/90）× 難度 ÷ AX倍率", font=F_S)
for i, c in enumerate(C5):
    col = get_column_letter(9 + i)
    put(H, HGIG, 3 + i, "=商品マスタ①!%s%d*(1/120+1/90)*商品マスタ①!%s%d/%s"
        % (col, M1_UNITS, col, M1_DIFF, pf(pAX, i)), fmt=M, align="right")
put(H, HGIG + 1, 1, "中国クリエイター 必要稼働（人）")
put(H, HGIG + 2, 1, "中国クリエイター 登録（人）", font=F_B)
put(H, HGIG + 3, 1, "　稼働率")
put(H, HGIG + 1, 8, "（③の年間工数 ＋ ①のクリエイター支払÷実効時給4,000円）÷ 年1,800時間", font=F_S)
put(H, HGIG + 2, 8, "★採用計画。1期30名は松田さんの指示。工数から導出される数ではない", font=F_S)
put(H, HGIG + 3, 8, "必要稼働 ÷ 登録。立ち上げ期は低く、市場が育つと上がる", font=F_S)
REG = [30, 120, 500, 1200, 2000]
for i2, c in enumerate(C5):
    col = get_column_letter(9 + i2)
    fte = "(商品マスタ③!%s%d+商品マスタ①!%s%d*1000000/4000)/1800" % (c, m3HRS, col, M1_CREPAY)
    put(H, HGIG + 1, 3 + i2, "=" + fte, fmt=N, align="right")
    put(H, HGIG + 2, 3 + i2, REG[i2], fmt=N, fill=INBG, align="right", font=F_B)
    put(H, HGIG + 3, 3 + i2, "=IF(%s%d=0,0,%s%d/%s%d)" % (c, HGIG + 2, c, HGIG + 1, c, HGIG + 2),
        fmt=P, align="right")
put(H, HGIG + 5, 1, "⚠ 登録数は工数から出る数字ではなく採用計画。先に人を集めないと受注できないので、"
                    "立ち上げ期は必要稼働より多く抱える。5年で約2,000名（中国の微短劇就業者69万人の0.3%）。"
                    "年400〜800名を新規登録させる採用オペレーションが要る。", font=F_S, border=False)

band(H, 23, "オフショア開発（業務委託）— ベトナム内のピラミッド")
header(H, 24, ["国・職位", "月額(万)", "構成比", "", "", "", "", "出所・考え方"])
OFF = [
    ("ベトナム ブリッジSE", 59.0, 0.20, "オフショア開発.com 2026。レビューと設計を担う上位層"),
    ("ベトナム プログラマー", 40.1, 0.80, "同上。実装を担う"),
    ("インド ブリッジSE", 60.0, 0.00, "参考。上位層で入れる場合"),
    ("インド プログラマー", 37.5, 0.00, "参考。ミドルを別国にすると継ぎ目が増える"),
    ("中国 シニア", 71.7, 0.00, "参考。ベトナムBSEより21%高い"),
    ("東欧 シニア", 104.0, 0.00, "参考。最も高い"),
]
for i2, (nm, rate, w, note) in enumerate(OFF):
    rr = 25 + i2
    put(H, rr, 1, nm)
    put(H, rr, 2, rate, fmt="0.0", fill=INBG, align="right")
    put(H, rr, 3, w, fmt=P, fill=INBG, align="right")
    put(H, rr, 8, note, font=F_S)
put(H, 31, 1, "構成比 合計", font=F_B)
put(H, 31, 3, "=SUM(C25:C30)", fmt=P, fill=CALCBG, align="right", font=F_B)
put(H, 32, 1, "加重単価（万円/年）", font=F_B)
put(H, 32, 2, "=SUMPRODUCT(B25:B30,C25:C30)*12", fmt=N, fill=KEYBG, align="right", font=F_B)
put(H, 32, 8, "ブリッジSE 20% ＋ プログラマー 80%", font=F_S)
HOFF_RATE = 32
put(H, 33, 1, "⚠ ピラミッドはベトナム内で組む。シニアがミドルをレビューする接点は最も"
             "コミュニケーション量が多いので、そこに国・言語・ベンダーの継ぎ目を置かない。"
             "社員PMの下が2層で収まる。", font=F_S, border=False)
put(H, 34, 1, "⚠ 安い順は ミャンマー(40)＜インド(45)＜フィリピン(47.5)＜ベトナム(50)＜中国(71.7)＜東欧(104)。"
             "ロシア・ベラルーシは外為法の役務取引規制（2022/3/18〜）で対象外。単価の問題ではない。",
    font=F_R, border=False)

band(H, 36, "エンジニアのAX化 — 人数を減らして単価の高い層に寄せる")
header(H, 37, ["項目", ""] + Y + ["考え方"])
OFFD = [
    (38, "必要開発工数（AXなし換算・人年）", [5, 10, 20, 30, 40], None, "★プロダクト規模から"),
    (39, "★ エンジニアのAX倍率", [1.0, 1.2, 1.5, 1.9, 2.2], None,
     "★ミドル中心なのでレビューがボトルネックになる。制作(4.0)より低く置く"),
    (40, "実エンジニア数（委託）", None, "=ROUNDUP({c}38/{c}39,0)", "必要工数 ÷ AX倍率"),
    (41, "PM（社員）", None, "=ROUNDUP({c}40/5,0)", "1名で5名を見る。上の人件費表はここを参照"),
    (42, "開発委託費（百万円）", None, "={c}40*$B$32/100", "実人数 × 加重単価"),
]
for rr, name, vals, f, note in OFFD:
    put(H, rr, 1, name, font=F_B if "委託費" in name else F_N)
    put(H, rr, 2, "")
    for i2, c in enumerate(C5):
        if vals is not None:
            put(H, rr, 3 + i2, vals[i2], fmt="0.0" if isinstance(vals[i2], float) else N,
                fill=INBG, align="right")
        else:
            put(H, rr, 3 + i2, f.format(c=c), fmt=N, align="right",
                fill=KEYBG if "委託費" in name else CALCBG,
                font=F_B if "委託費" in name else F_N)
    put(H, rr, 8, note, font=F_S)
HOFF_COST = 42
put(H, 44, 1, "旧構成は社員40名。PM4名＋委託19名になる。加重単価は年527万で、"
             "中国シニア20%＋ベトナムミドル80%（557万）より安く、継ぎ目もない。", font=F_S, border=False)
put(H, 45, 1, "⚠ 管理・コーポレート3名は、5期に上場会社として内部統制報告制度の対象になる規模には薄い。"
             "取引処理はBPOに出す前提だが、内部統制の設計・運用・評価は社員の仕事。"
             "監査法人と主幹事に早期に当てること。★確認事項", font=F_R, border=False)

band(H, 47, "社外の専門家を前提にするなら、その費用が見えている必要がある")
put(H, 48, 1, "管理3名で回るのは顧問弁護士・監査法人・社労士が外にいるから。"
             "その費用は「その他販管費（売上の4%）」に入っている。5期で足りるかの検算。",
    font=F_S, border=False)
header(H, 49, ["費目", "下限", "上限", "", "", "", "", "備考"])
SGAI = [
    ("監査報酬（上場後）", 40, 70, "上場会社・売上108億規模"),
    ("株式事務代行・IR", 20, 40, "信託銀行・開示書類・説明会"),
    ("顧問弁護士", 12, 30, "契約審査・中国パートナー・業務委託設計"),
    ("税理士・社会保険労務士", 6, 12, ""),
    ("オフィス（社員22名）", 30, 50, ""),
    ("SaaS・通信・インフラ（非開発）", 20, 40, ""),
    ("採用・教育", 30, 60, "PM・統括級の採用は単価が高い"),
    ("旅費交通", 30, 60, "ベトナム・インド往復"),
    ("保険・その他", 20, 40, ""),
]
for i2, (nm, a2, b2, note) in enumerate(SGAI):
    rr = 50 + i2
    put(H, rr, 1, nm)
    put(H, rr, 2, a2, fmt=N, fill=INBG, align="right")
    put(H, rr, 3, b2, fmt=N, fill=INBG, align="right")
    put(H, rr, 8, note, font=F_S)
put(H, 59, 1, "合計（百万円）", font=F_B)
put(H, 59, 2, "=SUM(B50:B58)", fmt=N, align="right", font=F_B, fill=CALCBG)
put(H, 59, 3, "=SUM(C50:C58)", fmt=N, align="right", font=F_B, fill=CALCBG)
put(H, 60, 1, "その他販管費（5期・売上の4%）", font=F_B)
H_SGA_CELL = (60, 3)
put(H, 61, 1, "判定", font=F_B)
put(H, 61, 3, '=IF(C60>=C59,"○ 上限まで賄える","× 足りない")', align="center", font=F_B)
put(H, 61, 8, "★費目はすべて私の見積もり。実際の見積を取ったものではない。"
             "監査報酬は別線（前提シート）に出したので、この表からは外してある", font=F_S)

band(H, 63, "採用費 — 4人目から計上する")
header(H, 64, ["項目", ""] + Y + ["考え方"])
REC = [
    (65, "社員数（期末）", None, "='人員と人件費'!{c}10", ""),
    (66, "増員（人）", None, "={c}65-{p}65", "1期は期末人数そのもの"),
    (67, "★ 免除（既に確保済み・リファラル）", [3, 0, 0, 0, 0], None, "最初の3名は計上しない"),
    (68, "計上人数", None, "=MAX(0,{c}66-{c}67)", ""),
    (69, "平均年収（万円）", None, "=IF({c}65=0,0,'人員と人件費'!{c}11/1.16*100/{c}65)", "人件費 ÷ 負担率 ÷ 人数"),
    (70, "★ 採用費率（想定年収比）", [0.30, 0.30, 0.30, 0.30, 0.30], None, "★エージェント手数料の一般水準"),
    (71, "採用費（百万円）", None, "={c}68*{c}69*{c}70/100", ""),
]
for rr, name, vals, f, note in REC:
    put(H, rr, 1, name, font=F_R if name.startswith("★") else (F_B if rr == 71 else F_N))
    put(H, rr, 2, "")
    for i2, c in enumerate(C5):
        if vals is not None:
            put(H, rr, 3 + i2, vals[i2], fmt=P if isinstance(vals[i2], float) else N,
                fill=INBG, align="right")
        else:
            prev = C5[i2 - 1] if i2 else None
            ff = "={c}65".format(c=c) if (rr == 66 and i2 == 0) else f.format(c=c, p=prev)
            put(H, rr, 3 + i2, ff, fmt=N, align="right",
                fill=KEYBG if rr == 71 else CALCBG, font=F_B if rr == 71 else F_N)
    put(H, rr, 8, note, font=F_S)
H_REC = 71

# ══════════════════════════════════════════════════════════════
# 損益計算書
# ══════════════════════════════════════════════════════════════
L = sheet("損益計算書", [30, 3, 13, 13, 13, 13, 13, 54])
title(L, "5年損益計算書（単位：百万円）",
      "全て数式。商品マスタ①②③・営業体制・人員・システム原価を参照している。")
header(L, 3, ["項目", ""] + Y + ["備考"])
RL, _r = {}, [4]


def line(key, label, f, fmt=N, bold=False, fill=None, note=""):
    r = _r[0]
    RL[key] = r
    put(L, r, 1, label, font=F_B if bold else F_N)
    put(L, r, 2, "")
    for i, c in enumerate(C5):
        col = get_column_letter(9 + i)
        put(L, r, 3 + i, f(i, c, col), fmt=fmt, align="right",
            font=F_B if bold else F_N, fill=fill)
    if note:
        put(L, r, 8, note, font=F_S)
    _r[0] = r + 1


line("p1", "① 映像制作", lambda i, c, col: "=商品マスタ①!%s%d" % (col, M1_REV),
     note="4商品の積み上げ（商品マスタ①）")
line("units", "　受注本数（本）", lambda i, c, col: "=商品マスタ①!%s%d" % (col, M1_UNITS),
     note="営業体制からの積み上げ")
line("price", "　平均単価（万円）", lambda i, c, col: "=商品マスタ①!%s%d" % (col, M1_PRICE), fmt=M)
line("diff", "　平均難度係数", lambda i, c, col: "=商品マスタ①!%s%d" % (col, M1_DIFF), fmt="0.00")
line("cu", "　1本あたり原価（万円）", lambda i, c, col: "=商品マスタ①!%s%d" % (col, M1_CU), fmt=M)
line("ax", "　AX倍率", lambda i, c, col: "=%s" % pf(pAX, i), fmt="0.0")
line("p2", "② ツール外販", lambda i, c, col: "=商品マスタ②!%s%d" % (c, m2REV),
     note="法人2階建て＋個人＋セルフサーブ")
line("p3", "③ C2C手数料", lambda i, c, col: "=商品マスタ③!%s%d" % (c, m3REV),
     note="14商品。GMV × 手数料30%")
line("rev", "売上高", lambda i, c, col: "=%s%d+%s%d+%s%d" % (c, RL["p1"], c, RL["p2"], c, RL["p3"]),
     bold=True, fill=KEYBG)
_r[0] += 1
line("c1", "① 売上原価", lambda i, c, col: "=%s%d*%s%d/100" % (c, RL["units"], c, RL["cu"]))
line("g1", "① 売上総利益", lambda i, c, col: "=%s%d-%s%d" % (c, RL["p1"], c, RL["c1"]))
line("g2", "② 売上総利益", lambda i, c, col: "=%s%d*商品マスタ②!$B$%d" % (c, RL["p2"], m2GPR))
line("g3", "③ 売上総利益", lambda i, c, col: "=商品マスタ③!%s%d" % (c, m3GP),
     note="30%から決済・送金・システム原価を引いた後")
line("gp", "売上総利益", lambda i, c, col: "=%s%d+%s%d+%s%d" % (c, RL["g1"], c, RL["g2"], c, RL["g3"]),
     bold=True, fill=KEYBG)
line("gpr", "　粗利率", lambda i, c, col: "=IF(%s%d=0,0,%s%d/%s%d)" % (c, RL["rev"], c, RL["gp"], c, RL["rev"]),
     fmt=P)
_r[0] += 1
line("pay", "人件費（社員）", lambda i, c, col: "='人員と人件費'!%s%d" % (c, HPAY))
line("off", "開発委託費（オフショア）", lambda i, c, col: "='人員と人件費'!%s%d" % (c, HOFF_COST),
     note="中国・ベトナム・東欧。PM1名あたり5名")
line("rnd", "研究開発費（GPU・基盤）", lambda i, c, col: "=%s" % pf(pRND, i),
     note="クラウドGPU・ライセンス・データ基盤")
line("bpo", "BPO（CS・運用）", lambda i, c, col: "=%s" % pf(pBPO, i))
line("acq", "獲得費", lambda i, c, col: "=%s%d*%s+%s%d*%s+%s"
     % (c, RL["p1"], pf(pACQ1, i), c, RL["p2"], pf(pACQ2, i), pf(pACQF, i)))
line("agf", "代理店手数料", lambda i, c, col: "=%s%d*%s*%s" % (c, RL["p1"], pf(pAGSH, i), pf(pAGFE, i)),
     note="①の代理店チャネル分のみ")
line("bad", "貸倒引当", lambda i, c, col: "=%s%d*%s" % (c, RL["rev"], pf(pBAD, i)),
     note="★売上の0.5%。貸倒が立つのは①の掛売のみ（③は収納代行・②は前受）")
line("rec", "採用費", lambda i, c, col: "='人員と人件費'!%s%d" % (c, H_REC),
     note="★4人目から。1人あたり想定年収の30%")
line("audit", "監査法人費用", lambda i, c, col: "=%s" % pf(pAUDIT, i),
     note="★上場2年前（3期）から年2,000万")
line("ipo", "上場関連費用", lambda i, c, col: "=%s" % pf(pIPO, i),
     note="★上場期に1億（主幹事・取引所・印刷・株式事務）")
line("ip", "知財関連費", lambda i, c, col: "=%s+%s%d*%s" % (pf(pIPFIX, i), c, RL["rev"], pf(pIPRATE, i)),
     note="1期は出願・商標の初期費用★、2期以降は売上の0.5%★")
line("sga", "その他販管費", lambda i, c, col: "=%s%d*%s" % (c, RL["rev"], pf(pSGA, i)))
put(H, H_SGA_CELL[0], H_SGA_CELL[1], "=損益計算書!G%d" % RL["sga"], fmt=N, align="right",
    font=F_B, fill=KEYBG)
line("opex", "販売費・一般管理費 計", lambda i, c, col: "=SUM(%s%d:%s%d)" % (c, RL["pay"], c, RL["sga"]),
     bold=True)
line("op", "営業利益", lambda i, c, col: "=%s%d-%s%d" % (c, RL["gp"], c, RL["opex"]), bold=True, fill=KEYBG)
line("opr", "　営業利益率", lambda i, c, col: "=IF(%s%d=0,0,%s%d/%s%d)" % (c, RL["rev"], c, RL["op"], c, RL["rev"]),
     fmt=P, bold=True)
_r[0] += 1
band(L, _r[0], "投資家が見る指標")
_r[0] += 1
line("heads", "社員数", lambda i, c, col: "='人員と人件費'!%s%d" % (c, HHEADS))
line("rph", "売上 / 社員（万円）",
     lambda i, c, col: "=IF(%s%d=0,0,%s%d*100/%s%d)" % (c, RL["heads"], c, RL["rev"], c, RL["heads"]),
     bold=True, fill=KEYBG, note="国内SaaSの平均2,000〜4,000万との比較")
line("rndr", "研究開発費 ÷ 売上",
     lambda i, c, col: "=IF(%s%d=0,0,%s%d/%s%d)" % (c, RL["rev"], c, RL["rnd"], c, RL["rev"]), fmt=P)
line("ns", "人手に比例しない収益",
     lambda i, c, col: "=%s%d+%s%d+%s%d*(1-1/%s)" % (c, RL["p2"], c, RL["p3"], c, RL["p1"], pf(pAX, i)),
     note="②＋③＋①のうちAXで人手から切れた分")
line("nsr", "　同 比率",
     lambda i, c, col: "=IF(%s%d=0,0,%s%d/%s%d)" % (c, RL["rev"], c, RL["ns"], c, RL["rev"]),
     fmt=P, bold=True, fill=KEYBG, note="受託と読まれないための中心指標")
line("save", "顧客が浮かせる額", lambda i, c, col: "=商品マスタ①!%s%d" % (col, M1_SAVE),
     note="①の提案の中身。値引き額の総額")

# ══════════════════════════════════════════════════════════════
# 資金計画
# ══════════════════════════════════════════════════════════════
K = sheet("資金計画", [30, 3, 13, 13, 13, 13, 13, 54])
title(K, "資金計画・キャッシュフロー（単位：百万円）",
      "営業利益からキャッシュ残高まで。運転資本と法人税を引いた後の、実際に手元に残る現金。")
header(K, 3, ["項目", ""] + Y + ["備考"])
RK, _k = {}, [4]


def kline(key, label, f, fmt=N, bold=False, fill=None, note=""):
    r = _k[0]
    RK[key] = r
    put(K, r, 1, label, font=F_B if bold else F_N)
    put(K, r, 2, "")
    for i, c in enumerate(C5):
        put(K, r, 3 + i, f(i, c, C5[i - 1] if i else None), fmt=fmt, align="right",
            font=F_B if bold else F_N, fill=fill)
    if note:
        put(K, r, 8, note, font=F_S)
    _k[0] = r + 1


kline("op", "営業利益", lambda i, c, pc: "=損益計算書!%s%d" % (c, RL["op"]), bold=True)
kline("nol", "　繰越欠損金（期首）",
      lambda i, c, pc: "=0" if i == 0 else "=MAX(0,%s%d-%s%d)" % (pc, RK["nol"], pc, RK["op"]),
      note="前期までの累積赤字")
kline("tb", "　課税所得", lambda i, c, pc: "=MAX(0,%s%d-%s%d)" % (c, RK["op"], c, RK["nol"]))
kline("tax", "法人税等", lambda i, c, pc: "=%s%d*%s" % (c, RK["tb"], pf(pTAX, i)),
      note="実効税率30%。繰越欠損金の控除後")
_k[0] += 1
kline("wc1", "運転資本：①制作（売掛−買掛）",
      lambda i, c, pc: "=損益計算書!%s%d*%s/365-損益計算書!%s%d*%s/365"
      % (c, RL["p1"], pf(pAR, i), c, RL["c1"], pf(pAP, i)),
      note="入金60日・支払30日。伸びるほど現金が先に出る")
kline("wc2", "運転資本：②前受金（△）",
      lambda i, c, pc: "=-損益計算書!%s%d*%s/365" % (c, RL["p2"], pf(pDEF, i)),
      note="年額一括前受。資金の source になる")
kline("wc", "運転資本 残高 計", lambda i, c, pc: "=%s%d+%s%d" % (c, RK["wc1"], c, RK["wc2"]), bold=True)
kline("dwc", "運転資本の増減（△は流出）",
      lambda i, c, pc: "=-%s%d" % (c, RK["wc"]) if i == 0
      else "=-(%s%d-%s%d)" % (c, RK["wc"], pc, RK["wc"]))
_k[0] += 1
kline("ocf", "営業キャッシュフロー",
      lambda i, c, pc: "=%s%d-%s%d+%s%d" % (c, RK["op"], c, RK["tax"], c, RK["dwc"]),
      bold=True, fill=KEYBG)
kline("icf", "投資キャッシュフロー", lambda i, c, pc: "=-%s" % pf(pCAPEX, i),
      note="クラウド前提。自社設備を持たない")
kline("seed", "　調達：シード", lambda i, c, pc: "=%s" % pf(pSEED, i))
kline("sera", "　調達：シリーズA", lambda i, c, pc: "=%s" % pf(pSERA, i))
kline("loan", "　調達：借入", lambda i, c, pc: "=%s" % pf(pLOAN, i))
kline("fcf", "財務キャッシュフロー",
      lambda i, c, pc: "=%s%d+%s%d+%s%d" % (c, RK["seed"], c, RK["sera"], c, RK["loan"]), bold=True)
_k[0] += 1
kline("net", "当期キャッシュ増減",
      lambda i, c, pc: "=%s%d+%s%d+%s%d" % (c, RK["ocf"], c, RK["icf"], c, RK["fcf"]), bold=True)
kline("cash", "期末キャッシュ残高",
      lambda i, c, pc: "=%s%d" % (c, RK["net"]) if i == 0
      else "=%s%d+%s%d" % (pc, RK["cash"], c, RK["net"]),
      bold=True, fill=KEYBG, note="マイナスになる期があってはいけない")
kline("burn", "月次バーン（平均）",
      lambda i, c, pc: "=IF(%s%d>=0,0,-%s%d/12)" % (c, RK["ocf"], c, RK["ocf"]))
kline("cash0", "（感応度）前受金ゼロなら期末残高",
      lambda i, c, pc: "=%s%d+%s%d" % (c, RK["cash"], c, RK["wc2"]),
      note="ツールを月額課金にした場合")

FX0 = _k[0] + 1
band(K, FX0, "為替感応度 — 原価は中国・ベトナムに出る")
header(K, FX0 + 1, ["項目", ""] + Y + ["備考"])
FXD = [
    (FX0 + 2, "① 中国クリエイターへの支払", "=商品マスタ①!{I}15", "本数 × 難度 × 12万"),
    (FX0 + 3, "③ 送金・為替（GMV×3%）", "=商品マスタ③!{c}39*商品マスタ③!$B$30", "中国の制作パートナー経由"),
    (FX0 + 4, "開発委託（ベトナム）", "='人員と人件費'!{c}42", "リード級 × 実人数"),
    (FX0 + 5, "外貨建ての支払 計", "={c}%d+{c}%d+{c}%d" % (FX0 + 2, FX0 + 3, FX0 + 4), ""),
    (FX0 + 6, "★ 10%の円安で増えるコスト", "={c}%d*0.1" % (FX0 + 5), "そのまま営業利益を押し下げる"),
    (FX0 + 7, "　売上に対する比率", "=IF(損益計算書!{c}%d=0,0,{c}%d/損益計算書!{c}%d)"
     % (RL["rev"], FX0 + 6, RL["rev"]), "10%円高なら同額が利益に乗る。赤字期は利益比が使えないので売上比で示す"),
]
for rr, name, f, note in FXD:
    put(K, rr, 1, name, font=F_B if "計" in name or "★" in name else F_N)
    put(K, rr, 2, "")
    for i2, c in enumerate(C5):
        col = get_column_letter(9 + i2)
        put(K, rr, 3 + i2, f.format(c=c, I=col),
            fmt=P if "影響" in name else N, align="right",
            fill=KEYBG if "★" in name else CALCBG, font=F_B if "★" in name else F_N)
    put(K, rr, 8, note, font=F_S)
put(K, FX0 + 9, 1, "ヘッジ方針: 年間の外貨支払見込みの50%★を為替予約（3〜6ヶ月）でカバーし、"
                   "残りは①の単価改定と③の手数料率で吸収する。予約はキャッシュを拘束するので、"
                   "残高が薄い1〜2期は付保率を下げる。", font=F_R, border=False)

# ══════════════════════════════════════════════════════════════
# 資本構成の推移
# ══════════════════════════════════════════════════════════════
W = sheet("資本構成の推移", [16, 26, 10, 11, 10, 10, 12, 11, 10, 30])
title(W, "株式シェアの推移（設立 → 上場）",
      "出所は CAP_TABLE.md 第5章。J-KISS はポストマネー・キャップなので、"
      "転換時のシード持分は 調達額 ÷ キャップ。")
header(W, 3, ["項目", "", "値", "単位", "区分", "", "", "", "", "備考"])
CW = [
    ("資本金", 800, "万円", "確定", "代表個人が全額出資"),
    ("ESOP枠（設立時）", 0.10, "%", "計画", "後から作ると全員の希薄化になるので設立時に設計"),
    ("J-KISS キャップ（ポストマネー）", 6.0, "億円", "確定", "交渉帯6〜10億"),
    ("シード調達額", 1.42, "億円", "確定", "目標1.5億のうち0.08億は代表個人"),
    ("ディスカウント", 0.20, "%", "確定", "キャップとの有利な方"),
    ("シリーズA ポストマネー評価", 15.0, "億円", "計画", "2028年（2期）"),
    ("シリーズA 調達額", 3.0, "億円", "計画", "無いと2期末に資金ショート"),
    ("ESOP補充後の ESOP比率", 0.099, "%", "計画", "シリーズAで薄まった枠を戻す"),
    ("IPO 公募比率", 0.20, "%", "計画", "新株発行なので全員が薄まる"),
    ("IPO 売出し（シードから）", 0.055, "%", "計画", "既存株主が売る。創業者は薄まらない"),
    ("IPO 売出し（シリーズAから）", 0.0, "%", "計画", "シード分だけで基準を満たす"),
]
r = 4
for name, v, unit, kind, note in CW:
    put(W, r, 2, name)
    put(W, r, 3, v, fmt=P if unit == "%" else (N if unit == "万円" else "0.00"),
        fill=INBG, align="right")
    put(W, r, 4, unit, align="center")
    put(W, r, 5, kind, align="center")
    put(W, r, 10, note, font=F_S)
    r += 1
wESOP, wCAP, wRAISE, wAPOST, wARAISE, wESOP2, wPUB, wSS, wSA = 5, 6, 7, 9, 10, 11, 12, 13, 14
for lab, f, note in [("転換時のシード持分", "=C7/C6", "ポストマネー・キャップなので 1.42 ÷ 6"),
                     ("シリーズA の持分", "=C10/C9", "3億 ÷ post 15億")]:
    put(W, r, 2, lab, font=F_B)
    put(W, r, 3, f, fmt=P, fill=CALCBG, align="right", font=F_B)
    put(W, r, 10, note, font=F_S)
    r += 1
wCONV, wASH = 15, 16

band(W, 18, "持分の推移")
header(W, 19, ["時期", "イベント", "金額", "創業者", "ESOP", "シード", "シリーズA", "公募",
               "合計", "経営権の判定"])
WALK = [
    ("2026/10", "設立（資本金800万）", "—", ["=1", "=0", "=0", "=0", "=0"]),
    ("2026/10", "ESOP枠を設計", "—", ["=D{p}*(1-$C${e})", "=$C${e}", "=0", "=0", "=0"]),
    ("2026/10", "J-KISS 発行（未転換）", "1.42億", ["=D{p}", "=E{p}", "=0", "=0", "=0"]),
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
r = 20
JUDGE = '=IF(D{r}>0.5,"経営権あり（50%超）",IF(D{r}>0.334,"拒否権あり（1/3超）","1/3割れ"))'
for when, ev, amt, fs in WALK:
    put(W, r, 1, when)
    put(W, r, 2, ev, font=F_B)
    put(W, r, 3, amt, align="right")
    for j, f in enumerate(fs):
        put(W, r, 4 + j, f.format(p=r - 1, e=wESOP, c=wCONV, a=wASH, e2=wESOP2,
                                  pb=wPUB, ss=wSS, sa=wSA),
            fmt=P, align="right", font=F_B if j == 0 else F_N,
            fill=KEYBG if j == 0 else None)
    put(W, r, 9, "=SUM(D%d:H%d)" % (r, r), fmt=P, align="right", font=F_S)
    put(W, r, 10, JUDGE.format(r=r))
    r += 1
wFINAL, wIPO = r - 1, r - 2

band(W, r + 1, "流通株式比率 — 基準25%を満たす設計")
header(W, r + 2, ["株主", "上場後の保有", "10%の判定", "流通株式への算入", "算入される持分",
                  "", "", "", "", "理由"])
fr = r + 3
FLOAT = [("創業者（役員）", "D", False, "役員の保有分は除外"),
         ("ESOP枠", "E", False, "役員・従業員分は除外"),
         ("シード投資家 保有分", "F", None, "10%未満なら全株が算入。売出しでここを越える"),
         ("シリーズA 保有分", "G", None, "10%以上なので除外"),
         ("公募・売出し", "H", True, "市場に出た分")]
JUD10 = '=IF(B{r}<0.1,"10%未満","10%以上")'
INC10 = '=IF(B{r}<0.1,"○ 算入","× 除外")'
for k2, (lab, col, fixed, why) in enumerate(FLOAT):
    rr = fr + k2
    put(W, rr, 1, lab)
    put(W, rr, 2, "=%s%d" % (col, wFINAL), fmt=P, align="right", font=F_B)
    if fixed is None:
        put(W, rr, 3, JUD10.format(r=rr), align="center")
        put(W, rr, 4, INC10.format(r=rr), align="center")
        put(W, rr, 5, "=IF(B%d<0.1,B%d,0)" % (rr, rr), fmt=P, align="right", font=F_B)
    else:
        put(W, rr, 3, "—", align="center")
        put(W, rr, 4, "○ 算入" if fixed else "× 除外", align="center",
            font=F_N if fixed else F_R)
        put(W, rr, 5, "=B%d" % rr if fixed else 0, fmt=P, align="right", font=F_B)
    put(W, rr, 10, why, font=F_S)
fsum = fr + 5
put(W, fsum, 1, "流通株式比率", font=F_B)
put(W, fsum, 5, "=SUM(E%d:E%d)" % (fr, fr + 4), fmt=P, align="right", font=F_B, fill=KEYBG)
put(W, fsum + 1, 1, "基準25%に対する過不足", font=F_B)
put(W, fsum + 1, 4, '=IF(E%d>=0.25,"○ 満たす","× 不足")' % fsum, align="center", font=F_B)
put(W, fsum + 1, 5, "=E%d-0.25" % fsum, fmt="+0.0%;-0.0%;0.0%", align="right", font=F_B)
put(W, fsum + 3, 1, "シードが5.5%を売出すと保有が10%未満になり、残りの保有株も一括で算入される。"
                    "公募を25%に上げる案より創業者持分が2.6ポイント厚く残る（42.2% vs 39.5%）。",
    font=F_S, border=False)

# ══════════════════════════════════════════════════════════════
# 資本政策とリターン
# ══════════════════════════════════════════════════════════════
CP = sheet("資本政策とリターン", [30, 16, 10, 12, 16, 14, 12, 12, 46])
title(CP, "資本政策とシード投資家のリターン",
      "⚠ 事業計画からの逆算であって、投資の推奨でも利回りの保証でもない。計画が達成された場合の数字。")
header(CP, 3, ["項目", "値", "単位", "区分", "", "", "", "", "備考"])
CAP = [
    ("J-KISS キャップ（ポストマネー）", "='資本構成の推移'!C%d" % wCAP, "億円", "確定", ""),
    ("シード調達額", "='資本構成の推移'!C%d" % wRAISE, "億円", "確定", "残り0.08億は代表個人"),
    ("転換時のシード持分", "='資本構成の推移'!C%d" % wCONV, "%", "計算", "＝ 調達額 ÷ キャップ"),
    ("転換後の希薄化", "=B8/B6", "倍", "計算", "シリーズA→ESOP補充→IPO公募 の積"),
    ("上場後のシード持分", "='資本構成の推移'!F%d" % wIPO, "%", "計算",
     "売出し分を含む経済持分。CAP_TABLE 第5章"),
    ("出資 → 上場", 4.9, "年", "計画", "2026年10月 → 2031年9月 東証グロース"),
]
r = 4
for name, v, unit, kind, note in CAP:
    put(CP, r, 1, name)
    put(CP, r, 2, v, fmt=P if unit == "%" else ("0.000" if unit == "倍" else "0.00"),
        fill=CALCBG if isinstance(v, str) else INBG, align="right",
        font=F_B if kind == "計算" else F_N)
    put(CP, r, 3, unit, align="center")
    put(CP, r, 4, kind, align="center")
    put(CP, r, 9, note, font=F_S)
    r += 1
CP_SHARE = 8

r += 1
band(CP, r, "① ライン別に倍率を分けた場合（証券会社が実際にやる見方）")
r += 1
header(CP, r, ["ケース", "ツール倍率", "C2C倍率", "制作倍率", "時価総額(億)", "取り分(億)",
               "倍率", "IRR", "考え方"])
r += 1
CP_LINE0 = r
for name, a, b, cc, note in [("保守", 6, 4, 1.5, "人手に比例しない90%超を根拠にツールへSaaS寄りの倍率"),
                             ("中庸", 7, 5, 2.0, ""),
                             ("強気", 8, 6, 2.5, "Synthesia・HeyGenと同じ土俵に立てた場合")]:
    put(CP, r, 1, name, font=F_B)
    for j, v in enumerate([a, b, cc]):
        put(CP, r, 2 + j, v, fmt="0.0", fill=INBG, align="right")
    put(CP, r, 5, "=(損益計算書!$G$%d*B%d+損益計算書!$G$%d*C%d+損益計算書!$G$%d*D%d)/100"
        % (RL["p2"], r, RL["p3"], r, RL["p1"], r), fmt=N, align="right", font=F_B, fill=CALCBG)
    put(CP, r, 6, "=E%d*$B$%d" % (r, CP_SHARE), fmt="0.00", align="right")
    put(CP, r, 7, "=F%d/$B$5" % r, fmt='0.0"倍"', align="right", font=F_R)
    put(CP, r, 8, "=G%d^(1/$B$9)-1" % r, fmt=P, align="right")
    put(CP, r, 9, note, font=F_S)
    r += 1
r += 1
band(CP, r, "② 全社に PSR を当てた場合")
r += 1
header(CP, r, ["ケース", "PSR", "", "", "時価総額(億)", "取り分(億)", "倍率", "IRR", "考え方"])
r += 1
CP_PSR0 = r
for name, ps, note in [("PSR 4倍", 4, "人手に比例しない収益が9割であることを根拠にする"),
                       ("PSR 5倍", 5, "")]:
    put(CP, r, 1, name, font=F_B)
    put(CP, r, 2, ps, fmt="0.0", fill=INBG, align="right")
    put(CP, r, 5, "=損益計算書!$G$%d*B%d/100" % (RL["rev"], r), fmt=N, align="right",
        font=F_B, fill=CALCBG)
    put(CP, r, 6, "=E%d*$B$%d" % (r, CP_SHARE), fmt="0.00", align="right")
    put(CP, r, 7, "=F%d/$B$5" % r, fmt='0.0"倍"', align="right", font=F_R)
    put(CP, r, 8, "=G%d^(1/$B$9)-1" % r, fmt=P, align="right")
    put(CP, r, 9, note, font=F_S)
    r += 1

# ══════════════════════════════════════════════════════════════
# 業界ベンチマーク
# ══════════════════════════════════════════════════════════════
B = sheet("業界ベンチマーク", [30, 14, 26, 30, 54])
title(B, "実在企業と並べる（5期の当社）",
      "⚠ 世界の「映像制作会社ランキング」は存在しない。大手広告グループは制作事業を分離開示しないため。")
header(B, 3, ["会社", "売上(億円)", "区分", "決算期・出所", "備考"])
BENCH = [
    ("東映", 1853, "映画・映像製作", "2026/3期", "国内最大"),
    ("IMAGICA GROUP", 1000, "ポスプロ・映像技術", "2026/3期（Q1 222億からの推計）", "推計値"),
    ("東映アニメーション", 937, "アニメ製作", "2026/3期", ""),
    ("AOI TYO Holdings", 511, "広告・企業映像", "2020/12期", "その後 非公開化"),
    ("東北新社", 477, "広告・企業映像", "2026/3期", "①制作の比較対象"),
    ("HeyGen", 300, "AI動画・ARR", "$200M（1ドル150円換算）", "$100M→$200M を8ヶ月"),
    ("Synthesia", 210, "AI動画・ARR", "$140M（1ドル150円換算）", "②ツールの比較対象"),
    ("IG Port", 141, "アニメ製作", "2026/5期", ""),
    ("Runway", None, "AI動画", "非開示", "売上を公表していない"),
    ("Technicolor", None, "VFX・ポスプロ", "2026年 経営破綻", "上場していた制作会社は消えつつある"),
]
r = 4
for name, v, kind, src, note in BENCH:
    put(B, r, 1, name)
    put(B, r, 2, v if v is not None else "非開示", fmt=N if v else None, align="right")
    put(B, r, 3, kind)
    put(B, r, 4, src, font=F_S)
    put(B, r, 5, note, font=F_S)
    r += 1
put(B, r, 1, "【当社 5期（2031年）】", font=F_R)
put(B, r, 2, "=損益計算書!$G$%d/100" % RL["rev"], fmt=N, align="right", font=F_R, fill=KEYBG)
put(B, r, 3, "①制作＋②ツール＋③C2C", font=F_R)
put(B, r, 4, "本計画", font=F_S)
r += 2
for lab, f in [("① 制作 ÷ 東北新社", "=損益計算書!$G$%d/100/477" % RL["p1"]),
               ("② ツール（ARRベース）÷ Synthesia", "=商品マスタ②!$G$49/100/210")]:
    put(B, r, 1, lab, font=F_B, border=False)
    put(B, r, 2, f, fmt=P, align="right")
    r += 1

# ══════════════════════════════════════════════════════════════
# 出所と仮置き
# ══════════════════════════════════════════════════════════════
O = sheet("出所と仮置き", [36, 24, 14, 64])
title(O, "数字の出所と、［仮置き］の一覧",
      "投資家に聞かれて最初に困るのがここ。実測値と仮置きを混ぜないこと。★は私（Claude）が置いた値。")
header(O, 3, ["項目", "値", "区分", "出所・根拠"])
SRC = [
    ("── 実測 ──", "", "", ""),
    ("国内 映像制作市場", "4,580億円", "実測", "矢野経済研究所（BtoB映像制作）"),
    ("インターネット広告制作費", "4,922億円", "実測", "電通 2025年 日本の広告費（前年比104.0%）"),
    ("法人数", "295万6,717社", "実測", "国税庁 令和5年度分 会社標本調査"),
    ("中国 剪辑師 平均月給", "8,935元", "実測", "Indeed 中国。③の価格下限の起点"),
    ("中国 微短劇 直接就業者", "約69万人", "実測", "中国網絡視聴協会 2024。必要人数の母数"),
    ("Stripe 決済手数料", "国内カード3.6%／銀行振込1.5%", "実測", "stripe.com/pricing"),
    ("S3 Standard 東京", "1TB/月 ≈ $25", "実測", "aws.amazon.com/s3/pricing"),
    ("CloudFront 東京", "$0.085/GB", "実測", "同上"),
    ("ベンチマーク各社の売上", "業界ベンチマーク シート", "実測", "各社の決算短信・公表ARR"),
    ("東証グロース 上場維持基準", "5年経過後 時価総額100億円", "実測", "日本取引所グループ"),
    ("── 確認できなかった ──", "", "", ""),
    ("スキルシェア市場の映像比率", "非公表", "確認不能", "ココナラ決算・矢野経済とも分離開示なし"),
    ("── 松田さんの決定 ──", "", "", ""),
    ("③ 手数料率", "一律30%（クリエイター70%）", "決定", "30%から決済・送金・システム原価を引く"),
    ("③ 送金・為替", "3%", "決定", "中国の制作パートナー経由"),
    ("③ 成約位置", "上限（需要側の支払意思）", "決定", "中点なら約59%、下限寄りなら約18%まで落ちる"),
    ("① クリエイター支払", "厚いまま（実効時給3,000〜6,000円）", "決定", "③より高く払い優先的に押さえる"),
    ("②-C セルフサーブ", "②に置く／用途特化", "決定", "汎用エディタは作らない"),
    ("② 解約率", "法人 年5%／個人 年30%", "決定", "法人はB2B SaaS一般水準5〜15%の下限。個人は月3〜5%の下限側"),
    ("── ★私が置いた値 ──", "", "", ""),
    ("AX倍率", "1.0 → 4.0倍", "★", "未実証。最重要前提。3倍でも営業利益率は成立する"),
    ("① 商品の値引率", "一律50%", "★", "企業の現行支払の半額。顧客が浮かせる額が提案の中身"),
    ("① 難度係数", "3.0 / 1.8 / 1.0 / 0.8", "★", "商品構成比から平均難度を導出している"),
    ("① 商品構成比", "年を追って上位帯へシフト", "★", "事例が溜まるほど上の帯が取れる前提"),
    ("① 営業の担当社数・リピート", "40社／年6本", "★", "エンタープライズ営業の標準的な水準"),
    ("② SKU単価・席数・Ent比率", "商品マスタ② 参照", "★", "チェックポイントに重い値付け"),
    ("③ 工数・上限価格・件数", "商品マスタ③ 参照", "★", "上限は日本の支払意思。実測ではない"),
    ("③ システム原価の内訳", "尺・保管期間・トークン数", "★", "単価は公表値、使用量は仮置き"),
    ("希薄化係数", "資本構成の推移 参照", "★", "シリーズA post 15億は未交渉"),
    ("貸倒引当率", "売上の0.5%", "★", "0.5〜1%の下限。貸倒が立つのは①の掛売のみ（③は収納代行・②は前受）"),
    ("採用費率", "想定年収の30%", "★", "4人目から計上。最初の3名は確保済み／リファラル前提"),
    ("監査法人費用", "3期から 年2,000万", "★", "N-2期から。その他販管費の見積からは監査報酬を外している"),
    ("上場関連費用", "上場期に 1億", "★", "主幹事・印刷・株式事務。5期に一括計上"),
    ("知財関連費", "1期300万／2期以降 売上の0.5%", "★", "出願・維持・侵害監視。件数ではなく売上比で置いている"),
    ("為替ヘッジ付保率", "外貨支払見込みの50%", "★", "3〜6ヶ月の為替予約。残高が薄い1〜2期は付保率を下げる"),
    ("── 未確定 ──", "", "", ""),
    ("中国の映像制作パートナー", "社名 ［記入予定］", "未確定", "契約前。権利は日本側に帰属する設計"),
    ("パートナーの取り分", "30%側か70%側か", "未確定", "契約で決まる。利益に直結する"),
    ("業務委託の契約設計", "─", "未着手", "偽装請負と読まれない設計。1年目に弁護士と"),
]
r = 4
for name, v, kind, note in SRC:
    head = name.startswith("──")
    put(O, r, 1, name, font=F_B if head else F_N,
        fill=CALCBG if head else None)
    put(O, r, 2, v, align="right")
    put(O, r, 3, kind, font=F_R if kind in ("★", "未確定", "未着手", "確認不能") else F_N,
        align="center")
    put(O, r, 4, note, font=F_S)
    r += 1

# ══════════════════════════════════════════════════════════════
# 知財
# ══════════════════════════════════════════════════════════════
IP = sheet("知財・法規制・リスク", [30, 14, 44, 46])
title(IP, "知財・法規制・リスク",
      "他人の権利を使って作り、自分の権利を積む事業。払う側・取る側・守る側を1枚で持つ。")
band(IP, 3, "① 支払う側 — 他人の権利にいくら払うか")
header(IP, 4, ["項目", "発生する事業", "中身", "対応"])
PAY = [
    ("フォント・音源・ストック素材", "①②③",
     "商用ライセンスが必要。納品物に混入すると後から遡及請求される",
     "許諾済み素材のホワイトリストを持ち、工程ツールで自動チェック（②の商品でもある）"),
    ("映像コーデックの特許プール料", "② 主に",
     "H.264／H.265 は特許プール（Via LA 等）の対象。**アプリを配布すると台数課金が発生する**",
     "②はクラウド配信（SaaS）を基本にする。配信側での処理なら負担は軽い。"
     "オンプレ配布を求められた場合は、その時点で料率を確認してから受ける"),
    ("生成AIモデルの商用利用条件", "①③",
     "モデルごとに商用可否・出力物の権利・再配布条件が違う。"
     "③は中国クリエイターが何のツールで作ったかまで把握しないと、納品物の権利が確定しない",
     "登録時に使用ツールを申告させ、許諾済みモデルのリストを提示。"
     "リスト外のツールで作られた納品物は受け付けない運用にする"),
    ("学習データの権利", "②",
     "①の制作データをモデル学習に使う。顧客の素材・肖像・ブランドが含まれる",
     "制作委託契約に「学習利用の許諾」条項を入れる。入っていない案件のデータは学習に回さない"),
]
r = 5
for nm, biz, what, how in PAY:
    put(IP, r, 1, nm, font=F_B)
    put(IP, r, 2, biz, align="center")
    put(IP, r, 3, what.replace("**", ""), font=F_S)
    put(IP, r, 4, how, font=F_S)
    r += 1

band(IP, r + 1, "② 取る側 — 自分の権利をどう積むか")
header(IP, r + 2, ["項目", "手段", "中身", "なぜそうするか"])
r += 3
TAKE = [
    ("越境取引の機構", "ビジネスモデル特許（出願検討）",
     "権利処理・決済（収納代行）・品質保証を1本の流れに通す仕組み",
     "③の参入障壁は仕組みそのもの。出願することで後発の同型モデルを牽制する"),
    ("商標", "日本・中国・台湾で先行取得",
     "サービス名・ロゴ。指定区分は 第9類・第35類・第42類を想定★",
     "**中国は先願主義。**使っていなくても先に出された側が勝つ。"
     "制作パートナーとの取引が始まる前に押さえる"),
    ("プロンプト設計・ワークフロー", "特許化せず、営業秘密として管理",
     "AX倍率を支える中核。出願すると公開され、そのまま模倣される",
     "不競法の営業秘密として守る。秘密管理性を満たす運用が条件（下記）"),
    ("チェックポイント・LoRA", "著作物＋営業秘密",
     "②の商品そのもの。学習済みモデルの重みと、その作り方",
     "配布形態はライセンス。ソースと学習手順は開示しない"),
]
for nm, how, what, why in TAKE:
    put(IP, r, 1, nm, font=F_B)
    put(IP, r, 2, how, font=F_S)
    put(IP, r, 3, what.replace("**", ""), font=F_S)
    put(IP, r, 4, why.replace("**", ""), font=F_S)
    r += 1

band(IP, r + 1, "営業秘密として守るための運用（不競法の秘密管理性）")
r += 2
for t in ["アクセス制限 … プロンプト・ワークフローは権限者のみ。委託先には必要な範囲だけを渡す",
          "秘密表示 … ファイル・ドキュメントに「秘」を明示し、管理台帳を持つ",
          "NDA … 社員・業務委託（ベトナム開発／制作ディレクション）・中国クリエイター・パートナーの全員と締結",
          "退職・契約終了時の返還・削除の取り決めを契約に含める"]:
    put(IP, r, 1, "・" + t, border=False, font=F_S)
    r += 1

band(IP, r + 1, "知財の帰属")
r += 2
put(IP, r, 1, "代表個人が設立前に開発したプロンプト・ツール類は、設立時に会社へ譲渡または実施許諾する。"
              "上場審査で必ず確認される項目なので、設立と同時に書面化する。", border=False, font=F_R)
r += 2

band(IP, r, "費用計画")
r += 1
header(IP, r, ["期", "金額（百万円）", "中身", ""])
r += 1
COST = [("1期", "3", "★特許出願（ビジネスモデル特許）＋商標3か国（日・中・台）の初期費用 300万"),
        ("2期", "2", "★売上の0.5%。出願維持・年金・監視・権利処理"),
        ("3期", "12", "同上"), ("4期", "34", "同上"), ("5期", "60", "同上")]
for y, v, note in COST:
    put(IP, r, 1, y, align="center", font=F_B)
    put(IP, r, 2, v, align="right", font=F_B, fill=KEYBG)
    put(IP, r, 3, note, font=F_S)
    r += 1
put(IP, r + 1, 1, "★ 金額はいずれも仮置き。弁理士の見積を取っていない。"
                  "出願を1件でなく複数に分けると初期費用は上振れする。", font=F_R, border=False)
r += 3

band(IP, r, "④ 法規制 — 1年目に確定させる")
r += 1
header(IP, r, ["項目", "いつ", "中身", "なぜ効くか"])
r += 1
LAW = [
    ("★ 資金決済法上の位置づけ", "1年目に弁護士と確認",
     "③の仲介が収納代行で済むか、資金移動業の登録が必要か",
     "登録が要るなら供託・体制整備・監督が乗り、③の設計そのものが変わる。最重要論点"),
    ("データの越境", "1年目",
     "中国のデータ越境規制と、日本の個人情報保護法への対応",
     "①③とも日本の発注者の素材が中国へ渡る。越境移転の同意取得と委託先管理が必要"),
    ("業務委託契約", "1年目に雛形を作成",
     "偽装請負と読まれない設計（指揮命令をしない／成果物単位で発注する）",
     "制作ディレクション・ベトナム開発・中国クリエイターの全てが業務委託。"
     "上場審査で必ず見られる"),
]
for nm, when, what, why in LAW:
    put(IP, r, 1, nm, font=F_R if nm.startswith("★") else F_B)
    put(IP, r, 2, when, font=F_S)
    put(IP, r, 3, what, font=F_S)
    put(IP, r, 4, why, font=F_S)
    r += 1

band(IP, r + 1, "⑤ リスク — ③では一次責任が当社に来る")
r += 2
header(IP, r, ["リスク", "", "中身", "対応"])
r += 1
RISK = [
    ("生成物の類似性", "", "生成AIの出力が既存作品に似る。学習元をたどれないため事前検証に限界がある",
     "★賠償責任保険の付保。工程ツールに類似チェックを組み込み、検収前に走らせる"),
    ("肖像・声の権利", "", "実在人物に似た顔・声が出る。③は発注者とクリエイターの間で素材が動く",
     "★契約書で責任上限を設定（当社が受領した手数料額を上限とする等）。素材の権利表明を発注者に求める"),
]
for nm, _x, what, how in RISK:
    put(IP, r, 1, nm, font=F_B)
    put(IP, r, 2, "")
    put(IP, r, 3, what, font=F_S)
    put(IP, r, 4, how, font=F_S)
    r += 1
put(IP, r + 1, 1, "⚠ ③は当社が場を提供する以上、権利侵害の申立ては一次的に当社へ来る。"
                  "クリエイター任せにはできない。保険の料率と填補範囲、責任上限の水準はいずれも★仮置きで、"
                  "1年目に弁護士および保険代理店と確定させる。", font=F_R, border=False)

# ══════════════════════════════════════════════════════════════
# 改訂履歴
# ══════════════════════════════════════════════════════════════
HX = sheet("改訂履歴", [10, 14, 34, 62])
title(HX, "改訂履歴",
      "数字が変わった理由を残す。投資家に「前はこうだったのでは」と聞かれたときに答えられるようにするため。")
header(HX, 3, ["版", "日付", "何を変えたか", "理由・出所"])
HIST = [
    ("0.4", "2026-09-23", "B案・強気。制作を半減しツールとC2Cを伸ばす",
     "人手に比例する①で無理をして、比例しない②③を小さく置いていたため"),
    ("", "", "市場規模の次に「業界の売上」を新設",
     "実在企業と並べないと88億の位置が読めない"),
    ("0.5", "2026-09-23", "一本値をやめ、事業×商品まで割って積み上げ",
     "「平均単価60万」は94.5万の商売と14万の商売を1つの数字に潰していた"),
    ("", "", "① 単価を「企業の現行支払×50%」に。本数は営業体制から",
     "見積比較サイトの相場帯は中小向けに偏る。市場シェアは結果であって根拠ではない"),
    ("", "", "② 5SKU・法人2階建て・②-Cセルフサーブを新設",
     "チェックポイントと工程ツールは別売り。LoRA個別構築は②の売上"),
    ("", "", "③ 14商品。下限はクリエイターの留保価格、上限は日本の支払意思",
     "中国 剪辑師 平均月給8,935元（Indeed中国）から時給を出して下限を逆算"),
    ("0.6", "2026-09-23", "③ 工数は旧maxを標準に置き直し",
     "ミニマムの見立てが甘かった。ウェディングの下限は11,500→34,500円"),
    ("", "", "③ 手数料を一律30%に。30%から決済・送金・システム原価を引く",
     "Stripe 国内カード3.6%・銀行振込1.5%／送金3%／システム原価53円/件"),
    ("", "", "③ システム原価を商品別に積み上げ（120円→53円）",
     "120円は根拠のない置き値だった。S3 3.66円/GB月・CloudFront 12.75円/GBから再計算"),
    ("", "", "② ACVとARRを分離。①③のARRはゼロと明示",
     "LoRA個別構築は一過性。Synthesia・HeyGenの公表値はARRなので土俵を揃える"),
    ("", "", "エンジニアを社員40名 → PM4名＋ベトナム委託19名",
     "オフショア開発.com 2026。ベトナムBSE59.0/PG40.1のピラミッド、加重527万/年"),
    ("", "", "エンジニアにもAX倍率（5期2.2倍）",
     "ミドル中心なのでレビューが制約。制作の4.0倍より低く置く"),
    ("", "", "中国・東欧・ロシアを委託先から外す",
     "中国71.7・東欧104.0はベトナムより高い。ロシアは外為法の役務取引規制で対象外"),
    ("", "", "中国クリエイターの登録数を採用計画（入力）に。1期30名",
     "工数から導出される数ではない。先に人を集めないと受注できない"),
    ("", "", "③ の価格を中点から上限に",
     "全取引が発注者の支払意思の上限で成約する前提。最も強気の置き方"),
    ("", "", "管理・コーポレートを6名→3名",
     "AX化と BPO。社外の顧問弁護士等が補う前提。その費用が4%に収まるかを検算"),
    ("0.7", "2026-09-23", "③-C の件数を調整し、5期売上を120億に",
     "個人オーダー 8,000→5,900件／企業オーダー 12,000→8,900件（比例で74%に）"),
    ("", "", "版番号を繰り下げ（1.x → 0.x）",
     "1.0 を提出版に充てるため。旧1.4→0.4／1.5→0.5／1.6→0.6"),
    ("0.8", "2026-09-23", "知財シートを新設（支払う側／取る側／帰属／費用計画）",
     "AI映像は他人の権利を使って作り、自分の権利を積む事業。両方を1枚で持つ"),
    ("", "", "知財関連費を新設（1期300万★／2期以降 売上の0.5%★）",
     "5期60百万。営業利益 46.0億→45.4億、利益率 38.3%→37.8%"),
    ("", "", "AX倍率を「実測して更新する指標」と明記",
     "1期の最初の20案件で実工数を計測し、2027年6月までに更新する★"),
    ("", "", "知財シートを「知財・法規制・リスク」に拡張（法規制3項目・リスク2項目を追加）",
     "資金決済法の位置づけ／データ越境／偽装請負／生成物の類似性／肖像・声の権利"),
    ("", "", "デッキ19枚目を「知財・法規制・リスク」1枚に集約（28枚のまま）",
     "枚数を増やさないため、知財単独スライドを作り替えた"),
    ("", "", "③の価格前提を「次版で中点成約に変更」と記述（数値は未変更）",
     "⚠ この段階では損益計算書・資金計画の数値を一切変更していない。数値改訂は次版"),
    ("0.8 数値改訂", "2026-09-23", "③ 価格は ToC・ToB とも上限成約（松田さん指示）",
     "一度は中点成約に下げ、次に ToC だけ上限に戻したが、ToB を中点に置くと採用価格が下がるため"
     "全商品で上限を採用する。5期GMV 142.5億（Ver0.7と同じ）。区分列は買い手の違いを示すために残す"),
    ("", "", "② に解約率を新設（★法人 年5%／個人 年30%）",
     "契約数は「新規獲得−解約」の純増に。法人600→578社、個人17,000→14,180人。②売上 41.6億→37.5億"),
    ("", "", "②の解約が①にも波及",
     "制作会社チャネル＝法人契約数×転換率なので、①の本数 3,780→3,727本、売上 35.7→35.2億"),
    ("", "", "貸倒引当を新設（★売上の0.5%）",
     "③は収納代行・②は前受なので、貸倒が立つのは①の掛売のみ。0.5〜1%の下限を採る"),
    ("", "", "採用費を新設（★4人目から・想定年収の30%）",
     "最初の3名は確保済み／リファラル前提で計上しない。5期4百万"),
    ("", "", "監査法人費用を新設（★3期から年2,000万）",
     "その他販管費の見積からは監査報酬を外して二重計上を避けた"),
    ("", "", "上場関連費用を新設（★上場期に1億）", "主幹事引受・取引所上場料・印刷・株式事務"),
    ("", "", "設備投資ゼロの前提を見直し（★1期2／3期6／4期12百万）",
     "20名規模のオフィス。1人あたり内装・什器・敷金で60万★。減価償却は金額が小さいため未計上"),
    ("", "", "為替感応度を追加（資金計画シート）",
     "外貨建て支払は5期12.2億。10%円安で1.2億の利益圧迫。ヘッジは外貨支払見込みの50%★を予約"),
    ("", "", "再計算の結果",
     "5期 売上 120.0→115.4億、営業利益 45.4→40.8億（37.8%→35.3%）。減少分は②の解約と追加費用。"
     "黒字化は3期のまま。2期末キャッシュ208百万でシリーズA前の資金ショートなし"),
]
r = 4
for ver, date, what, why in HIST:
    put(HX, r, 1, ver, align="center", font=F_B if ver else F_N,
        fill=KEYBG if ver else None)
    put(HX, r, 2, date, align="center", font=F_S)
    put(HX, r, 3, what)
    put(HX, r, 4, why, font=F_S)
    r += 1
r += 1
put(HX, r, 1, "⚠ 0.4 → 0.5 は構造の作り直し、0.5 → 0.6 は前提を実勢データで詰めたもの、"
             "0.7 は③-Cの件数を落として120億に合わせ、0.8 は知財を明示して前提を保守化したもの。"
             "5期の売上は 88.1億 → 130.3億 → 120.0億 → 115.4億、社員は 61名 → 22名。"
             "数字が良くなった分だけ、前提の説明責任が重くなっている。", font=F_R, border=False)
put(HX, r + 1, 1, "PPTX「投資家向け企画書 Ver0.8.pptx」は本シートと同じ数値で再生成済み。"
                  "deck/build.js を直して node build.js → slim.py の順で作る。", font=F_R, border=False)

# ══════════════════════════════════════════════════════════════
# サマリー
# ══════════════════════════════════════════════════════════════
S = wb["Sheet"]
S.title = "サマリー"
for i, w in enumerate([30, 3, 14, 14, 14, 14, 14, 46], start=1):
    S.column_dimensions[get_column_letter(i)].width = w
S.sheet_view.showGridLines = False
S.freeze_panes = "A4"
title(S, "AI映像制作事業　5年計画サマリー（Ver%s）" % VERSION,
      "単位：百万円。事業×商品まで割って積み上げたもの。一本値は使っていない。"
      "⚠［仮置き］の前提に乗った計画であり、実績ではない。")
header(S, 3, ["項目", ""] + Y + ["備考"])
SUM = [
    ("売上高", "L", "rev", N, True, ""),
    ("　① 映像制作", "L", "p1", N, False, "4商品・本数は営業体制から"),
    ("　② ツール外販", "L", "p2", N, False, "法人2階建て＋個人＋セルフサーブ"),
    ("　③ 越境C2C手数料", "L", "p3", N, False, "14商品・手数料30%"),
    ("売上総利益", "L", "gp", N, False, ""),
    ("営業利益", "L", "op", N, True, ""),
    ("　営業利益率", "L", "opr", P, True, ""),
    ("営業キャッシュフロー", "K", "ocf", N, False, "税・運転資本の後"),
    ("期末キャッシュ残高", "K", "cash", N, True, "一度もマイナスにならないこと"),
    ("社員数", "L", "heads", N, False, "業務委託・BPOは含まない"),
    ("売上 / 社員（万円）", "L", "rph", N, True, ""),
    ("人手に比例しない収益 比率", "L", "nsr", P, True, "受託と読まれないための中心指標"),
    ("研究開発費 ÷ 売上", "L", "rndr", P, False, ""),
    ("AX倍率", "L", "ax", "0.0", False, "最重要前提★。3倍でも成立する"),
    ("顧客が浮かせる額", "L", "save", N, False, "①の提案の中身"),
]
r = 4
for label, src, key, fmt, bold, note in SUM:
    put(S, r, 1, label, font=F_B if bold else F_N)
    put(S, r, 2, "")
    for i, c in enumerate(C5):
        ref = "損益計算書!%s%d" % (c, RL[key]) if src == "L" else "資金計画!%s%d" % (c, RK[key])
        put(S, r, 3 + i, "=" + ref, fmt=fmt, align="right",
            font=F_B if bold else F_N, fill=KEYBG if bold else None)
    put(S, r, 8, note, font=F_S)
    r += 1

r += 1
band(S, r, "Ver0.8 数値改訂の前後（5期）")
r += 1
header(S, r, ["項目", "", "改訂前", "改訂後", "差", "", "", "変更の中身"])
r += 1
CMP = [
    ("売上高", 12005, "rev", "②に解約率／費用5項目を追加。③は上限成約のまま"),
    ("　③ 越境C2C", 4274, "p3", "変更なし。ToC・ToBとも上限成約を採用"),
    ("　② ツール外販", 4158, "p2", "★法人5%・個人30%の年次解約率を新設"),
    ("営業利益", 4536, "op", "上に加えて費用5項目（貸倒・採用・監査・上場・オフィス）"),
]
CMP_R0 = r
for name, before, key, note in CMP:
    put(S, r, 1, name, font=F_B if "　" not in name else F_N)
    put(S, r, 2, "")
    put(S, r, 3, before, fmt=N, align="right", font=F_S)
    put(S, r, 4, "=損益計算書!G%d" % RL[key], fmt=N, align="right", font=F_B, fill=KEYBG)
    put(S, r, 5, "=D%d-C%d" % (r, r), fmt="+#,##0;-#,##0", align="right", font=F_R)
    put(S, r, 8, note, font=F_S)
    r += 1
put(S, r, 1, "営業利益率", font=F_B)
put(S, r, 2, "")
put(S, r, 3, 0.378, fmt=P, align="right", font=F_S)
put(S, r, 4, "=損益計算書!G%d" % RL["opr"], fmt=P, align="right", font=F_B, fill=KEYBG)
put(S, r, 5, "=D%d-C%d" % (r, r), fmt="+0.0%;-0.0%", align="right", font=F_R)
put(S, r, 8, "各期の対比は改訂履歴シート", font=F_S)
r += 2
band(S, r, "継続収益（ARR）と非継続の内訳")
r += 1
header(S, r, ["項目", ""] + Y + ["考え方"])
r += 1
ARR_ROWS = {}
for tag, name, ref, note in [
        ("p1", "① 映像制作 ARR", "'商品マスタ①'!{I}21", "案件ベース。リテイナー契約分のみ（いまは0）"),
        ("p2", "② ツール外販 ARR", "'商品マスタ②'!{c}49", "LoRA個別構築とセルフサーブ都度分を除く"),
        ("p3", "③ 越境C2C ARR", "'商品マスタ③'!{c}49", "取引ベースなのでゼロ")]:
    ARR_ROWS[tag] = r
    put(S, r, 1, name)
    put(S, r, 2, "")
    for i2, c in enumerate(C5):
        col = get_column_letter(9 + i2)
        put(S, r, 3 + i2, "=" + ref.format(I=col, c=c), fmt=N, align="right")
    put(S, r, 8, note, font=F_S)
    r += 1
ARR_TOT = r
put(S, r, 1, "全社 ARR", font=F_B)
put(S, r, 2, "")
for i2, c in enumerate(C5):
    put(S, r, 3 + i2, "=%s%d+%s%d+%s%d" % (c, ARR_ROWS["p1"], c, ARR_ROWS["p2"], c, ARR_ROWS["p3"]),
        fmt=N, align="right", fill=KEYBG, font=F_B)
put(S, r, 8, "投資家に「御社のARRは？」と聞かれたらこの行", font=F_S)
r += 1
put(S, r, 1, "　ARR比率（対 売上）", font=F_B)
put(S, r, 2, "")
for i2, c in enumerate(C5):
    put(S, r, 3 + i2, "=IF(%s4=0,0,%s%d/%s4)" % (c, c, ARR_TOT, c),
        fmt=P, align="right", fill=KEYBG, font=F_B)
put(S, r, 8, "②以外は継続収益にならない", font=F_S)
r += 1
put(S, r, 1, "⚠ 継続収益になるのは②だけ。①は案件ベース、③は取引ベース。"
             "下のライン別評価でツール6〜8倍・C2C4〜6倍・制作1.5〜2.5倍と差をつけているのは、"
             "まさにこの違いを反映している。", font=F_S, border=False)
r += 2
band(S, r, "シード投資家（1.42億）のリターン")
r += 1
header(S, r, ["ケース", "", "時価総額(億)", "取り分(億)", "倍率", "IRR", "", "根拠"])
r += 1
for label, src, note in [("ライン別・保守", CP_LINE0, "ツール6倍＋C2C4倍＋制作1.5倍"),
                         ("ライン別・中庸", CP_LINE0 + 1, "ツール7倍＋C2C5倍＋制作2.0倍"),
                         ("ライン別・強気", CP_LINE0 + 2, "ツール8倍＋C2C6倍＋制作2.5倍"),
                         ("全社 PSR 4倍", CP_PSR0, "人手に比例しない収益が9割であること"),
                         ("全社 PSR 5倍", CP_PSR0 + 1, "")]:
    put(S, r, 1, label, font=F_B)
    put(S, r, 2, "")
    put(S, r, 3, "='資本政策とリターン'!E%d" % src, fmt=N, align="right")
    put(S, r, 4, "='資本政策とリターン'!F%d" % src, fmt="0.00", align="right")
    put(S, r, 5, "='資本政策とリターン'!G%d" % src, fmt='0.0"倍"', align="right",
        font=F_R, fill=KEYBG)
    put(S, r, 6, "='資本政策とリターン'!H%d" % src, fmt=P, align="right")
    put(S, r, 7, "")
    put(S, r, 8, note, font=F_S)
    r += 1
r += 1
put(S, r, 1, "⚠ 上の倍率は事業計画からの逆算であって、投資の推奨でも利回りの保証でもない。"
             "前提の多くは未実証（「出所と仮置き」シート参照）。", font=F_S, border=False)
r += 2
band(S, r, "このモデルの読み方")
r += 1
for t in ["入力は「前提」と3つの「商品マスタ」の黄色セルだけ。ほかは全部そこを参照する数式。",
          "①の平均単価と平均難度は、商品構成比から導出される。直接は入力できない。",
          "③は成約が価格帯のどこに落ちるかで約6倍動く。いまは上限（需要側の支払意思）を採用している。",
          "⚠ xlsx を手で編集しないこと。make_xlsx.py を直して再生成する。"]:
    put(S, r, 1, t, font=F_S, border=False)
    r += 1

wb.active = 0

for ws in wb.worksheets:
    ws.freeze_panes = "A4"
wb.save(OUT)
print("書き出し: %s（%d シート）" % (OUT, len(wb.worksheets)))
for ws in wb.worksheets:
    print("  - %s" % ws.title)
