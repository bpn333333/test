# -*- coding: utf-8 -*-
"""組織を組み直す — 社員はPM中心、開発はオフショア業務委託、管理はAX化で極小

松田さんの指示（2026-09-23）
  ・エンジニアの人数が多すぎる。基本的に PM を社員として、
    あとは中国・ベトナム・東ヨーロッパに業務委託する構成に
  ・管理・コーポレートの人数比率が多い。AX化で極小に

旧: モデル開発エンジニアを社員で40名（5期・社員61名中）抱える
新: モデル開発PMを社員で8名、その下にオフショア40名を業務委託

オフショア単価
  ベトナム シニアエンジニア 48.3万円/月 … オフショア開発.com（2024年・実測）
  中国・東欧は★私の推定（ベトナム比 1.3倍 / 1.6倍）
"""

Y = ["1期", "2期", "3期", "4期", "5期"]
n = 5
BURDEN = 1.16

# ── オフショア単価 ─────────────────────────────────────
VN_MONTH = 48.3          # 万円/月。ベトナム シニアエンジニア（実測）
CN_MULT, EE_MULT = 1.3, 1.6   # ★ベトナム比
MIX = {"ベトナム": 0.50, "中国": 0.30, "東欧": 0.20}
RATE = {"ベトナム": VN_MONTH, "中国": VN_MONTH * CN_MULT, "東欧": VN_MONTH * EE_MULT}
OFF_MONTH = sum(RATE[k] * MIX[k] for k in MIX)
OFF_YEAR = OFF_MONTH * 12

print("=" * 92)
print("オフショア単価")
print("=" * 92)
print("  %-12s %10s %10s %10s  %s" % ("国", "月額(万)", "年額(万)", "構成比", "出所"))
print("  " + "-" * 72)
for k in MIX:
    print("  %-12s %10.1f %10.0f %9.0f%%  %s"
          % (k, RATE[k], RATE[k] * 12, MIX[k] * 100,
             "オフショア開発.com 2024（実測）" if k == "ベトナム"
             else "★ベトナム比 %.1f倍" % (CN_MULT if k == "中国" else EE_MULT)))
print("  " + "-" * 72)
print("  %-12s %10.1f %10.0f %9.0f%%" % ("加重平均", OFF_MONTH, OFF_YEAR, 100))
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
    "モデル開発PM":              [1, 2, 4, 6, 8],
    "制作統括":                 [1, 2, 3, 3, 3],
    "事業開発・アライアンス":      [1, 2, 4, 5, 6],
    "クリエイターネットワーク統括": [1, 1, 2, 3, 3],
    "管理・コーポレート":         [0, 1, 1, 2, 2],
}
PER_PM = 5      # ★PM1名あたりのオフショアエンジニア数
OFF_HEADS = [HEADS["モデル開発PM"][i] * PER_PM for i in range(n)]
OFF_COST = [OFF_HEADS[i] * OFF_YEAR / 100 for i in range(n)]   # 百万円

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
      % (OFF_YEAR, 850 * BURDEN))
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
