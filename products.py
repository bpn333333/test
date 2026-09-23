# -*- coding: utf-8 -*-
"""事業 × 商品に分解して積み上げる

これまで ① は「本数 × 平均単価」、② は「契約数 × ACV」の一本値だった。
どちらも商品の集合であって、単一の商品ではない。SKU 単位に割る。

【確定】松田さんの指示
  ・難度係数を採用する（1本あたり原価 ＝ 難度係数 × 基準原価）
  ・BtoBマーケ・SNS量産帯を ① に戻す

【提案】★の付いた値は私が置いたもの。承認されるまで確定値ではない
  ・SKU別の値引き率（SNS量産は▲50%だと原価割れのため▲30%）
  ・SKU別の難度係数
  ・① の商品構成比
  ・② の商品分解（チェックポイント／LoRA／工程ツール）

【変えていない】
  ① の本数 3,780本（sales.py）、② の契約数・ACV、③ の全て、
  社員数・人件費・研究開発費・BPO・獲得費率6%・AX倍率・シード持分14.5%
"""

BASE = 12.0 + 20.0 / 4.0 + 2.0 + 1.5     # 20.5万。AX4倍時の基準原価（Ver1.4から変えない）
UNITS_5 = 3780                            # sales.py

# ── 事業① 映像制作（受託）────────────────────────────
# (商品, 企業の現行支払, ★値引き率, ★難度係数, ★構成比, 主な販路)
# 1-A エンタープライズ4商品。本数は sales.py の 3,780本（営業体制の積み上げ）
#      構成比は pricing.py のまま（15/35/35/15）— 変えていない
P1 = [
    ("ブランドムービー・Web CM",      500, 0.50, 3.00, 0.15, "直販"),
    ("企業VP・採用（ブランド型）",     200, 0.50, 1.80, 0.35, "直販・代理店"),
    ("企業VP・会社紹介（標準）",       100, 0.50, 1.00, 0.35, "代理店・インバウンド"),
    ("展示会・社内イベント映像",        60, 0.50, 0.80, 0.15, "制作会社経由"),
]
# 1-B BtoBマーケ・SNS量産。★販路が別なので本数は「3,780本の内数」ではなく加算
SNS = ("BtoBマーケ・SNS量産", 20, 0.30, 0.35)

print("=" * 100)
print("事業① 映像制作 — 1-A エンタープライズ（販路: 直販・代理店・制作会社・インバウンド）")
print("=" * 100)
print("  商品                       現行支払  値引率   当社単価  顧客削減   原価   粗利率  構成比   本数   売上")
print("  " + "-" * 96)
pw = cw = rev1 = 0.0
for name, cur, disc, k, share, ch in P1:
    price = cur * (1 - disc); cost = BASE * k
    units = UNITS_5 * share; rev = units * price / 10000.0
    rev1 += rev; pw += price * share; cw += cost * share
    print("  %-26s %5d万 %5.0f%% %7.0f万 %6.0f万 %6.1f万 %5.1f%% %5.0f%% %6.0f本 %6.1f億"
          % (name, cur, disc * 100, price, cur - price, cost,
             (1 - cost / price) * 100, share * 100, units, rev))
print("  " + "-" * 96)
print("  %-26s %5s %5s %7.1f万 %6.1f万 %6.1f万 %5.1f%% %5.0f%% %6d本 %6.1f億"
      % ("小計", "", "", pw, pw, cw, (1 - cw / pw) * 100, 100, UNITS_5, rev1))
print()

print("=" * 100)
print("事業① 映像制作 — 1-B BtoBマーケ・SNS量産（★販路が未定）")
print("=" * 100)
name, cur, disc, k = SNS
price = cur * (1 - disc); cost = BASE * k
print("  %s: 現行%d万 → ★値引率%.0f%% → 当社単価%.0f万／原価%.1f万（難度%.2f）／粗利率%.1f%%"
      % (name, cur, disc * 100, price, cost, k, (1 - cost / price) * 100))
print("  ※ ▲50%%だと当社単価10万・原価7.2万で粗利2.8万（28%%）。受注・検収・請求の手間に見合わない。")
print("     ★▲30%%は私が置いた値です。")
print()
print("  本数        売上      売上総利益   必要な委託ディレクション   ① 合計売上")
print("  " + "-" * 74)
PYU = 1.0 / 120 + 1.0 / 90
gig_ent = UNITS_5 * PYU * (sum(k2 * s for _, _, _, k2, s, _ in P1)) / 4
for nunits in [0, 2000, 5000, 10000]:
    rev = nunits * price / 10000.0
    gp = rev * (1 - cost / price)
    gig = nunits * PYU * k / 4
    print("  %6d本 %8.1f億 %9.1f億 %14.1f名 %12.1f億"
          % (nunits, rev, gp, gig, rev1 + rev))
print()
print("  ※ エンタープライズ4商品だけで委託ディレクションは %.1f名。上表はそれに加算されます。" % gig_ent)
print("  ★ 指示をください: SNS量産の販路（セルフサーブ／定額パッケージ／③C2Cへ）と本数。")
print("     決まるまで ① は 1-A の %.1f億 のみで置きます。" % rev1)
print()
print("  ＜わかったこと＞")
print("    最初に置いた「平均単価60万」は、間違いというより **2つの別の商売を1つの数字に潰していた**。"
      .replace("**", ""))
print("    1-A は %.1f万、1-B は %.0f万。平均を取ると %.1f万になり、どちらの実態も表さない。"
      % (pw, price, (rev1 * 10000 + 5000 * price) / (UNITS_5 + 5000)))
print("    → ①は今後、平均単価を使わず商品別に積みます。")
print()

# ── 事業② 制作ツール外販 ──────────────────────────────
# 松田さんの決定（2026-09-23）
#   ・チェックポイントと工程ツールは別売り
#   ・LoRA個別構築は ② の売上（①の制作案件には含めない）
#   ・法人は Enterprise / Standard の2階建て
# ★単価・席数・構成比は私が置いた値
SKU = {
    "cp_ent":  ("チェックポイント Enterprise", "年額",      300, "全業種・商用利用・10席"),
    "cp_std":  ("チェックポイント Standard",   "年額",      100, "1業種・3席"),
    "tool":    ("工程ツール（要件定義・自動チェック）", "月額2万/席", 24, "1席あたり年額"),
    "lora_m":  ("LoRA 年間保守",              "年額",       24, "追加学習モデルの更新・再学習"),
    "lora_b":  ("LoRA 個別構築",              "初期・都度",  80, "顧客のブランド・商品を学習"),
}
SEATS = {"Enterprise": 10, "Standard": 3}
LORA_ATTACH = 0.25            # ★個別構築の付帯率
CORP = [0, 15, 100, 320, 600]                  # 契約数（Ver1.4から変えない）
ENT_SHARE = [0.0, 0.13, 0.20, 0.25, 0.30]      # ★Enterprise比率
OLD_ACV = [0, 250, 280, 300, 320]              # Ver1.4の一本値
Y = ["1期", "2期", "3期", "4期", "5期"]

print("=" * 100)
print("事業② 制作ツール外販 — 商品（★単価・席数・構成比は私の提案）")
print("=" * 100)
print("  %-34s %-12s %8s  %s" % ("商品", "課金形態", "単価(万)", "中身"))
print("  " + "-" * 96)
for k in ["cp_ent", "cp_std", "tool", "lora_m", "lora_b"]:
    nm, kind, pr, note = SKU[k]
    print("  %-34s %-12s %8d  %s" % (nm, kind, pr, note))
print()

def plan_acv(tier):
    cp = SKU["cp_ent"][2] if tier == "Enterprise" else SKU["cp_std"][2]
    tool = SKU["tool"][2] * SEATS[tier]
    return cp, tool, SKU["lora_m"][2], cp + tool + SKU["lora_m"][2]

print("  プラン構成（LoRA個別構築は別枠）")
print("  %-12s %10s %10s %10s %10s" % ("", "チェックポイント", "工程ツール", "LoRA保守", "年額計"))
print("  " + "-" * 60)
for tier in ["Enterprise", "Standard"]:
    cp, tool, lm, tot = plan_acv(tier)
    print("  %-12s %10d %10d %10d %10d  （%d席）" % (tier, cp, tool, lm, tot, SEATS[tier]))
ent_acv = plan_acv("Enterprise")[3]
std_acv = plan_acv("Standard")[3]
lora_add = SKU["lora_b"][2] * LORA_ATTACH
print("  %-12s %43d  （付帯率%.0f%%）" % ("＋LoRA個別構築", lora_add, LORA_ATTACH * 100))
print()

print("  期別の積み上げと、Ver1.4の一本値との突き合わせ")
print("  %-22s" % "" + "".join("%10s" % y for y in Y))
print("  " + "-" * 72)
def row2(lab, vals, f="%10.0f"):
    print("  %-22s" % lab + "".join(f % v for v in vals))
ent_n = [round(CORP[i] * ENT_SHARE[i]) for i in range(5)]
std_n = [CORP[i] - ent_n[i] for i in range(5)]
acv = [((ent_n[i] * ent_acv + std_n[i] * std_acv) / CORP[i] + lora_add) if CORP[i] else 0
       for i in range(5)]
rev2 = [CORP[i] * acv[i] / 100.0 for i in range(5)]
old2 = [CORP[i] * OLD_ACV[i] / 100.0 for i in range(5)]
row2("法人契約数", CORP)
row2("  Enterprise", ent_n)
row2("  Standard", std_n)
row2("積み上げACV(万)", acv)
row2("Ver1.4の一本値(万)", OLD_ACV)
row2("  差(万)", [acv[i] - OLD_ACV[i] for i in range(5)], "%+10.0f")
row2("法人売上(百万)", rev2)
row2("  Ver1.4(百万)", old2)
print()
print("  → 積み上げたACVは一本値を %+.0f〜%+.0f万でなぞる。数字を置き換えるのではなく再現できている。"
      % (min(acv[i] - OLD_ACV[i] for i in range(1, 5)),
         max(acv[i] - OLD_ACV[i] for i in range(1, 5))))
print("     5期の法人売上は %.0f百万（Ver1.4は %.0f百万）。差 %+.0f百万。"
      % (rev2[-1], old2[-1], rev2[-1] - old2[-1]))
print()
print("  個人向け（別売りの決定を反映）")
print("  %-34s %-12s %8s" % ("チェックポイント 個人", "月額6,000円", 7.2))
print("  %-34s %-12s %8s" % ("工程ツール 個人（1席）", "月額4,000円", 4.8))
print("  %-34s %-12s %8s  ← Ver1.4の12万と一致" % ("計", "", 12.0))
print()

# ── 事業③ 越境C2C ────────────────────────────────────
print("=" * 100)
print("事業③ 越境C2C — 未分解（指示がないため触っていない）")
print("=" * 100)
print("  現状: GMV 83億 × 手数料率18% = 14.9億 の一本値")
print("  取引手数料以外の商品（エスクロー・翻訳・品質保証オプション）は未定義。")
