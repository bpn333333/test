# -*- coding: utf-8 -*-
"""① 映像制作の本数を、営業体制から積み上げる

これまで本数は「SAMの何%」から逆算していた。市場シェアは結果であって、
計画の根拠にはならない。単価を94.5万（企業の現行支払の50%）に上げた以上、
買い手はエンタープライズになり、営業の形も変わる。

積み上げの単位は「本」ではなく「アカウント」。
企業は年に1本だけ作るのではなく、採用・展示会・製品説明・IRと複数本を出す。
だから “何社と取引があるか × 1社が年に何本出すか” で積む。

4つのチャネル
  1 直販          事業開発が担当するエンタープライズ
  2 制作会社経由   ②ツール外販の法人顧客が、自社案件を当社に流す ★ここが効く
  3 代理店経由     広告代理店・人材会社
  4 インバウンド   事例・検索

⚠ 担当社数・リピート本数・転換率はすべて［仮置き］。単価は pricing.py。
"""

Y = ["1期", "2期", "3期", "4期", "5期"]
n = 5

# ── 1 直販 ────────────────────────────────────────────
BD_HEADS = [1, 2, 4, 5, 6]        # 事業開発・アライアンス（payroll.py と同じ）
ACC_PER_BD = [15, 25, 35, 40, 40]  # 1名あたり担当アカウント数［仮置き］
REPEAT = [4, 5, 6, 6, 6]           # 1アカウントの年間発注本数［仮置き］

# ── 2 制作会社経由（②の法人顧客が発注元になる）────────────
TOOL_CORP = [0, 15, 100, 320, 600]      # ②の法人契約数
CONV = [0.0, 0.20, 0.25, 0.30, 0.30]    # そのうち当社に発注もする割合［仮置き］
CORP_REPEAT = [0, 6, 7, 8, 8]           # 1社あたり年間本数［仮置き］

# ── 3 代理店経由 ──────────────────────────────────────
AGENCY = [0, 2, 10, 25, 40]             # 提携代理店数［仮置き］
AGENCY_REPEAT = [0, 8, 12, 15, 15]      # 1社あたり年間本数［仮置き］

# ── 4 インバウンド ────────────────────────────────────
INBOUND = [0, 20, 80, 200, 300]         # 本［仮置き］

# ── 単価（pricing.py の加重平均へ向けて上げていく）──────────
# 立ち上げ期は標準帯（企業VP 50万）中心。事例が溜まるほど上の帯が取れる。
PRICE = [65, 75, 85, 90, 94.5]

direct = [BD_HEADS[i] * ACC_PER_BD[i] * REPEAT[i] for i in range(n)]
via_corp = [round(TOOL_CORP[i] * CONV[i] * CORP_REPEAT[i]) for i in range(n)]
via_agency = [AGENCY[i] * AGENCY_REPEAT[i] for i in range(n)]
units = [direct[i] + via_corp[i] + via_agency[i] + INBOUND[i] for i in range(n)]
rev = [units[i] * PRICE[i] / 10000.0 for i in range(n)]

accounts = [BD_HEADS[i] * ACC_PER_BD[i] + round(TOOL_CORP[i] * CONV[i]) + AGENCY[i] for i in range(n)]

SAM_2031 = 2238.0
OLD_UNITS = [54, 350, 1200, 2800, 5594]
OLD_REV = [27, 192.5, 720, 1680, 3356.4]


def row(label, vals, f="{:>10,.0f}"):
    print(label.ljust(30) + "".join(f.format(v) for v in vals))


print("=" * 94)
print("チャネル別の積み上げ（本／年）")
print("=" * 94)
row("", Y, "{:>10}")
print("-" * 94)
row("  1 直販", direct)
row("      事業開発（名）", BD_HEADS)
row("      1名あたり担当社数", ACC_PER_BD)
row("      1社あたり年間本数", REPEAT)
row("  2 制作会社経由", via_corp)
row("      ②の法人契約数", TOOL_CORP)
row("      うち発注もする割合(%)", [c * 100 for c in CONV], "{:>10.0f}")
row("  3 代理店経由", via_agency)
row("      提携代理店数", AGENCY)
row("  4 インバウンド", INBOUND)
print("-" * 94)
row("受注本数 合計", units)
row("  （旧・SAM逆算）", OLD_UNITS)
row("平均単価（万円）", PRICE, "{:>10.1f}")
row("① 売上（億円）", rev, "{:>10.1f}")
row("  （旧・単価60万）", [v / 100 for v in OLD_REV], "{:>10.1f}")
print("=" * 94)
print()

print("=" * 94)
print("取引社数と、1社あたりの年間取引額")
print("=" * 94)
row("取引アカウント数", accounts)
row("1社あたり年間取引額（万円）", [rev[i] * 10000 / accounts[i] if accounts[i] else 0 for i in range(n)])
direct_rev = [direct[i] * PRICE[i] / 10000.0 for i in range(n)]
row("  うち直販の売上（億円）", direct_rev, "{:>10.2f}")
row("  直販1名あたり売上（億円）", [direct_rev[i] / BD_HEADS[i] for i in range(n)], "{:>10.2f}")
print()
print("  → 5期で %d社と取引し、1社あたり年 %.0f万円。"
      % (accounts[-1], rev[-1] * 10000 / accounts[-1]))
print("     事業開発1名が自分で持つのは %.2f億（担当%d社 × 年%.0f万）。残りはチャネル経由。"
      % (direct_rev[-1] / BD_HEADS[-1], ACC_PER_BD[-1],
         direct_rev[-1] * 10000 / (BD_HEADS[-1] * ACC_PER_BD[-1])))
print("     ①売上 %.1f億のうち直販は %.0f%%。**営業人数に比例しない売り方になっている。**"
      .replace("**", "") % (rev[-1], direct_rev[-1] / rev[-1] * 100))
print()

print("=" * 94)
print("なぜ社員6名で %d社をカバーできるのか" % accounts[-1])
print("=" * 94)
print("  直販で持つのは %d社だけ。残り %d社は自分で開拓していない。"
      % (BD_HEADS[-1] * ACC_PER_BD[-1], accounts[-1] - BD_HEADS[-1] * ACC_PER_BD[-1]))
print()
print("  ★ 最大の販路は ② のツール外販顧客です。")
print("     制作会社は当社ツールを買った時点で、自社の案件をどう作るか考えている。")
print("     手に余る案件・納期が厳しい案件を当社に流す動線が自然にできる。")
print("     5期 %d社のうち %.0f%%（%d社）が発注元になれば、それだけで %d本。"
      % (TOOL_CORP[-1], CONV[-1] * 100, round(TOOL_CORP[-1] * CONV[-1]), via_corp[-1]))
print("     **②を売ることが①の営業になっている。** ここが人手に比例しない理由。"
      .replace("**", ""))
print()
print("  代理店 %d社は、当社が営業せずに案件が入る導線。" % AGENCY[-1])
print("  インバウンド %d本は、事例と検索から。" % INBOUND[-1])
print()

print("=" * 94)
print("旧計画との比較（5期）")
print("=" * 94)
gig_old = OLD_UNITS[-1] * (1 / 120.0 + 1 / 90.0) / 4
gig_new = units[-1] * (1 / 120.0 + 1 / 90.0) / 4
print("  %-28s %14s %14s" % ("", "旧（SAM逆算）", "新（営業積み上げ）"))
print("  " + "-" * 60)
print("  %-28s %13s %15s" % ("本数の根拠", "SAMの1.5%", "アカウント×リピート"))
print("  %-28s %12d本 %14d本" % ("5期の受注本数", OLD_UNITS[-1], units[-1]))
print("  %-28s %12.1f万 %14.1f万" % ("平均単価", 60.0, PRICE[-1]))
print("  %-28s %12.1f億 %14.1f億" % ("① 売上", OLD_REV[-1] / 100, rev[-1]))
print("  %-28s %12.2f%% %13.2f%%" % ("SAMシェア（結果）", OLD_REV[-1] / 100 / SAM_2031 * 100,
                                    rev[-1] / SAM_2031 * 100))
print("  %-28s %12.0f名 %14.0f名" % ("業務委託ディレクション", gig_old, gig_new))
print("  %-28s %12s %14.0f億" % ("顧客が浮かせる総額", "—", units[-1] * PRICE[-1] / 10000.0))
print()
print("  → 本数は %d本 → %d本（%.0f%%減）。単価が上がるので売上は %.1f億 → %.1f億。"
      % (OLD_UNITS[-1], units[-1], (1 - units[-1] / OLD_UNITS[-1]) * 100,
         OLD_REV[-1] / 100, rev[-1]))
print("     委託ディレクションは %.0f名 → %.0f名。**AX倍率への依存が下がります。**"
      .replace("**", "") % (gig_old, gig_new))
print("     そして市場シェアは目標ではなく、結果として %.2f%% と出てくる。" % (rev[-1] / SAM_2031 * 100))
