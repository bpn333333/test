# -*- coding: utf-8 -*-
"""組織を組み直す — 社員はPM中心、開発はオフショア業務委託、管理はAX化で極小

松田さんの指示（2026-09-23）
  ・エンジニアの人数が多すぎる。基本的に PM を社員として、
    あとは中国・ベトナム・東ヨーロッパに業務委託する構成に
  ・管理・コーポレートの人数比率が多い。AX化で極小に

旧: モデル開発エンジニアを社員で40名（5期・社員61名中）抱える
新: モデル開発PMを社員で8名、その下にオフショア40名を業務委託

オフショア単価（国別・実測）
  オフショア開発.com 2026年2月更新。シニアエンジニアの人月単価。
  ⚠ 中国は最も高い（71.7万/月）。「中国の方が安い」は成り立たない。
    安いのは中国の**クリエイター**（剪辑師 月18.8万・雇用ベース）であって、
    エンジニアの受託単価ではない。両者は性質が違う。
  ⚠ 東欧はこの調査に含まれないため★推定。
"""

import math

Y = ["1期", "2期", "3期", "4期", "5期"]
n = 5
BURDEN = 1.16

# ── オフショア単価（国別・実測）───────────────────────────
# アジア: オフショア開発.com 2026年2月更新（人月・万円）
# 東欧:  Devico / RemoteMore / Wild.Codes 2026（時給ドル）→ 月160h・1ドル150円で換算
USD, HRS = 150.0, 160.0
EE_HOURLY = {"ルーマニア": (30, 45), "ウクライナ": (40, 55), "ポーランド": (35, 55)}
EE_MONTH = {k: (lo + hi) / 2 * HRS * USD / 10000 for k, (lo, hi) in EE_HOURLY.items()}
EE_SENIOR = sum(EE_MONTH.values()) / len(EE_MONTH)

SENIOR = {"ミャンマー": 40.0, "インド": 45.0, "フィリピン": 47.5, "ベトナム": 50.0,
          "バングラデシュ": 52.5, "中国": 71.7, "東欧": EE_SENIOR}
# AX前提のリード級（ブリッジSE／アーキテクト相当）
LEAD = {"ベトナム": 59.0, "中国": 75.8, "東欧": EE_SENIOR * 1.2}

print("=" * 92)
print("オフショア単価（シニア・人月）")
print("=" * 92)
print("  東欧の内訳（時給ドル → 月160h・1ドル150円）")
for k, (lo, hi) in EE_HOURLY.items():
    print("    %-10s $%d〜%d/h  →  月 %.1f万円" % (k, lo, hi, EE_MONTH[k]))
print("    3か国平均 月 %.1f万円" % EE_SENIOR)
print()
print("  %-12s %10s %12s  %s" % ("国", "月額(万)", "年額(万)", "ベトナム比"))
print("  " + "-" * 60)
for k, v in sorted(SENIOR.items(), key=lambda x: x[1]):
    mk = "  ← 最も高い" if v == max(SENIOR.values()) else ("  ← 中国" if k == "中国" else "")
    print("  %-12s %10.1f %12.0f %11.2f倍%s" % (k, v, v * 12, v / SENIOR["ベトナム"], mk))
print()
print("  ⚠ 私は東欧を★80万/月と置いていたが、実勢は %.1f万/月。**低く見積もっていた**。"
      .replace("**", "") % EE_SENIOR)
print("     そして東欧は中国より高い。安い順は ミャンマー＜インド＜フィリピン＜ベトナム＜中国＜東欧。")
print("     出所はAI・DevOps等は「baseline より上」としており、モデル開発は上振れ側。")
print()

print("=" * 92)
print("委託先として外す国と、その理由")
print("=" * 92)
EXCL = [
    ("ロシア", "×", "外為法の役務取引規制（2022/3/18〜）。経産大臣の許可制で、限定的な例外を除き"
                   "許可されない。送金も銀行の確認義務に引っかかる。単価の問題ではない"),
    ("ベラルーシ", "×", "ロシアと同じ枠組みで規制対象"),
    ("ミャンマー", "△", "単価は最安（月40万）だが、2021年以降の政情。送金・事業継続の安定性に懸念"),
    ("インド", "○", "月45万。ベトナムより安い。英語圏で人材層が厚い"),
    ("フィリピン", "○", "月47.5万。英語圏。日本向けの実績もある"),
]
print("  %-10s %4s  %s" % ("国", "判定", "理由"))
print("  " + "-" * 86)
for nm, jd, why in EXCL:
    print("  %-10s %4s  %s" % (nm, jd, why))
print()
print("  ⚠ ロシアは上場を目指す会社としては特に危険。")
print("    主幹事証券・監査法人はロシア向けの支払いを必ず見る。1件でもあると審査が止まる。")
print("    米国OFAC・EU・英国の制裁も重なっており、日本の規制だけの問題ではない。")
print()
print("  ※ 2022年以降、ロシア人エンジニアはジョージア・アルメニア・カザフスタン・")
print("    セルビア・UAE等に移っている。それらの国の法人と契約する形はありうるが、")
print("    実質的支配者が制裁対象でないかの確認が要り、デューデリの負担は重い。")
print()

MIX = {"ベトナム": 0.50, "中国": 0.30, "東欧": 0.20}
SEN_BLEND = sum(SENIOR[k] * w for k, w in MIX.items())
LEAD_BLEND = sum(LEAD[k] * w for k, w in MIX.items())
print("=" * 92)
print("エンジニアのAX化 — 人数を減らして単価を上げる")
print("=" * 92)
print("  構成比 ベトナム50% / 中国30% / 東欧20%（松田さんの指示どおり）")
print("  %-28s 月 %5.1f万  年 %4.0f万" % ("シニア級（AXなし）", SEN_BLEND, SEN_BLEND * 12))
print("  %-28s 月 %5.1f万  年 %4.0f万  （+%.0f%%）"
      % ("リード級（AX前提）", LEAD_BLEND, LEAD_BLEND * 12,
         (LEAD_BLEND / SEN_BLEND - 1) * 100))
print("    リード級＝ブリッジSE／アーキテクト相当。AIを使い切れる層に絞る。")
print()
NEED = [5, 10, 20, 30, 40]           # ★必要開発工数（AXなし換算・人年）
AX_DEV = [1.0, 1.3, 1.7, 2.1, 2.5]   # ★エンジニアのAX倍率
OFF_HEADS = [int(math.ceil(NEED[i] / AX_DEV[i])) for i in range(n)]
OFF_YEAR = LEAD_BLEND * 12
OFF_COST = [OFF_HEADS[i] * OFF_YEAR / 100 for i in range(n)]
PM_HEADS = [int(math.ceil(OFF_HEADS[i] / 5)) for i in range(n)]

print("  %-26s" % "" + "".join("%10s" % y for y in Y))
print("  " + "-" * 78)
print("  %-26s" % "必要開発工数（AXなし換算）" + "".join("%10d" % v for v in NEED))
print("  %-26s" % "★エンジニアのAX倍率" + "".join("%10.1f" % v for v in AX_DEV))
print("  %-26s" % "実エンジニア数（委託）" + "".join("%10d" % v for v in OFF_HEADS))
print("  %-26s" % "PM（社員・1名で5名を見る）" + "".join("%10d" % v for v in PM_HEADS))
print("  %-26s" % "開発委託費（百万円）" + "".join("%10.0f" % v for v in OFF_COST))
print()
OLD_OFF = [38, 75, 150, 225, 300]
print("  %-26s" % "（AXなしの場合）" + "".join("%10.0f" % v for v in OLD_OFF))
print("  %-26s" % "差" + "".join("%+10.0f" % (OFF_COST[i] - OLD_OFF[i]) for i in range(n)))
print()
print("  → 5期は %d名 → %d名。単価は年%.0f万 → %.0f万に上げても、費用は %.0f → %.0f百万。"
      % (40, OFF_HEADS[-1], SEN_BLEND * 12, OFF_YEAR, OLD_OFF[-1], OFF_COST[-1]))
print("     **1〜2期は高くつく**（AX倍率が立ち上がっていないのに単価だけ上がるため）。"
      .replace("**", ""))
print("     制作のAXと同じ形。先に投資して、後で効いてくる。")
print()

# ── 社員 ───────────────────────────────────────────────
ROLE = {
    "経営・CxO": 900,
    "モデル開発PM": 950,
    "制作統括": 650,
    "事業開発・アライアンス": 700,
    "クリエイターネットワーク統括": 600,
    "管理・コーポレート": 550,
}
HEADS = {
    "経営・CxO":                [1, 1, 2, 3, 3],
    "モデル開発PM":              PM_HEADS,          # AX後のエンジニア数から逆算
    "制作統括":                 [1, 2, 3, 3, 3],
    "事業開発・アライアンス":      [1, 2, 4, 5, 6],
    "クリエイターネットワーク統括": [1, 1, 2, 3, 3],
    "管理・コーポレート":         [0, 1, 1, 2, 3],   # 松田さん指示。社外の顧問弁護士等が補う前提
}
PER_PM = 5      # ★PM1名あたりのオフショアエンジニア数

heads = [sum(HEADS[r][i] for r in ROLE) for i in range(n)]
pay = [sum(HEADS[r][i] * ROLE[r] * BURDEN for r in ROLE) / 100 for i in range(n)]

# 旧構成
OLD_ROLE = {"経営・CxO": 900, "モデル開発エンジニア": 850, "制作統括": 650,
            "事業開発・アライアンス": 700, "クリエイターネットワーク統括": 600,
            "管理・コーポレート": 550}
OLD_HEADS = {"経営・CxO": [1, 1, 2, 3, 3], "モデル開発エンジニア": [2, 6, 16, 28, 40],
             "制作統括": [1, 2, 3, 3, 3], "事業開発・アライアンス": [1, 2, 4, 5, 6],
             "クリエイターネットワーク統括": [1, 1, 2, 3, 3], "管理・コーポレート": [0, 1, 2, 4, 6]}
old_heads = [sum(OLD_HEADS[r][i] for r in OLD_ROLE) for i in range(n)]
old_pay = [sum(OLD_HEADS[r][i] * OLD_ROLE[r] * BURDEN for r in OLD_ROLE) / 100 for i in range(n)]


def row(lab, vals, f="{:>10,.0f}"):
    print(lab.ljust(28) + "".join(f.format(v) for v in vals))


print("=" * 92)
print("社員（PM中心）")
print("=" * 92)
print("  職種".ljust(28) + "年収".rjust(8) + "".join("%10s" % y for y in Y))
print("  " + "-" * 78)
for r in ROLE:
    print("  %-26s %6d万" % (r, ROLE[r]) + "".join("%10d" % HEADS[r][i] for i in range(n)))
print("  " + "-" * 78)
row("  社員数 合計", heads)
row("  人件費（百万円）", pay)
row("  うち 管理・コーポレート比率", [HEADS["管理・コーポレート"][i] / heads[i] * 100 for i in range(n)],
    "{:>9.1f}%")
print()

print("=" * 92)
print("業務委託（オフショア開発）")
print("=" * 92)
row("  PM（社員）", HEADS["モデル開発PM"])
row("  オフショアエンジニア", OFF_HEADS)
row("  開発委託費（百万円）", OFF_COST)
print()
print("  ★ PM1名あたり %d名。ブリッジは PM が兼ねる前提。" % PER_PM)
print()

print("=" * 92)
print("旧構成との比較")
print("=" * 92)
print("  %-26s" % "" + "".join("%10s" % y for y in Y))
print("  " + "-" * 78)
row("  旧 社員数", old_heads)
row("  新 社員数", heads)
row("  差", [heads[i] - old_heads[i] for i in range(n)], "{:>+10,.0f}")
print("  " + "-" * 78)
row("  旧 人件費", old_pay)
row("  新 人件費", pay)
row("  新 開発委託費", OFF_COST)
row("  新 合計（人件費＋委託）", [pay[i] + OFF_COST[i] for i in range(n)])
row("  差（対 旧人件費）", [pay[i] + OFF_COST[i] - old_pay[i] for i in range(n)], "{:>+10,.0f}")
print()
print("  → 5期の社員は %d名 → %d名（%+d名）。" % (old_heads[-1], heads[-1], heads[-1] - old_heads[-1]))
print("     人件費は %.0f → %.0f百万。開発委託費 %.0f百万を足すと %.0f百万で、旧より %+.0f百万。"
      % (old_pay[-1], pay[-1], OFF_COST[-1], pay[-1] + OFF_COST[-1],
         pay[-1] + OFF_COST[-1] - old_pay[-1]))
print("     **コストはほぼ変わらない。変わるのは社員数**。".replace("**", ""))
print("     1人あたりの単価はオフショアの方が安いが（年%.0f万 vs 日本 %.0f万）、"
      % (OFF_YEAR, 950 * BURDEN))
print("     人数を増やせるぶん相殺される。狙いはコスト削減ではなく組織の身軽さ。")
print()

print("=" * 92)
print("管理・コーポレートのAX化")
print("=" * 92)
print("  %-26s %10s %10s" % ("", "旧", "新"))
print("  " + "-" * 50)
print("  %-26s %10d名 %9d名" % ("5期の管理・コーポレート", OLD_HEADS["管理・コーポレート"][-1],
                                HEADS["管理・コーポレート"][-1]))
print("  %-26s %9.1f%% %9.1f%%" % ("社員数に占める比率",
                                   OLD_HEADS["管理・コーポレート"][-1] / old_heads[-1] * 100,
                                   HEADS["管理・コーポレート"][-1] / heads[-1] * 100))
print()
print("  何を自動化するか")
for t in ["仕訳・入金消込（③はStripeの明細がそのまま入る）",
          "請求・与信（②はSaaS課金、③は収納代行なので人が触らない）",
          "経費精算・労務（クラウド会計＋勤怠の標準機能）",
          "契約レビュー（雛形＋AIの一次レビュー。判断は外部弁護士）"]:
    print("    ・" + t)
print()
print("  ⚠ ここが計画で一番きわどい。")
print("    5期は上場会社で、売上105億・内部統制報告制度の対象になる。管理2名は薄い。")
print("    BPO（5期 10億）が取引処理を担う前提だが、**内部統制の設計・運用・評価は社員の仕事**。"
      .replace("**", ""))
print("    監査法人と主幹事に「この人数で回るか」を早期に当てること。★確認事項")


print()
print("=" * 92)
print("社外の専門家を前提にするなら、その費用が見えている必要がある")
print("=" * 92)
print("  管理を3名に抑えられるのは、顧問弁護士・監査法人・社労士などが外にいるから。")
print("  その費用は「その他販管費（売上の4%）」に入っている。5期で足りるかを検算する。")
print()
SGA5 = 10802 * 0.04      # 百万円。5期売上 × 4%
ITEMS = [
    ("監査報酬（上場後）", 40, 70, "上場会社・売上108億規模"),
    ("株式事務代行・IR", 20, 40, "信託銀行・開示書類・説明会"),
    ("顧問弁護士", 12, 30, "契約審査・中国パートナー・業務委託設計"),
    ("税理士・社会保険労務士", 6, 12, ""),
    ("オフィス（社員26名）", 30, 50, ""),
    ("SaaS・通信・インフラ（非開発）", 20, 40, ""),
    ("採用・教育", 30, 60, "PM・統括級の採用は単価が高い"),
    ("旅費交通", 30, 60, "中国・ベトナム・東欧の往復"),
    ("保険・その他", 20, 40, ""),
]
print("  %-30s %10s %10s  %s" % ("費目", "下限", "上限", "備考"))
print("  " + "-" * 76)
lo = hi = 0
for nm, a, b, note in ITEMS:
    lo += a; hi += b
    print("  %-30s %9d %10d  %s" % (nm, a, b, note))
print("  " + "-" * 76)
print("  %-30s %9d %10d" % ("合計（百万円）", lo, hi))
print("  %-30s %19.0f" % ("その他販管費（売上の4%）", SGA5))
print()
if SGA5 >= hi:
    print("  → 4%%で上限まで賄える（余裕 %.0f百万）。" % (SGA5 - hi))
elif SGA5 >= lo:
    print("  → 4%%は下限%d〜上限%dのレンジに入るが、**上限側だと余裕がない**（差 %.0f百万）。"
          .replace("**", "") % (lo, hi, SGA5 - hi))
    print("     社外の専門家に頼る設計なら、ここは率ではなく積み上げで置き直す方が安全。★")
else:
    print("  → **4%%では足りない**。率を上げるか積み上げに置き直す必要がある。".replace("**", ""))
print()
print("  ⚠ この費目はすべて★私の見積もり。実際の見積を取ったものではない。")
