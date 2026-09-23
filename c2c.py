# -*- coding: utf-8 -*-
"""事業③ 越境C2C — 単価に幅を持たせ、クリエイター側から下限を決める

値付けの順序を変えた。
  旧: 日本の相場から単価を1つ決める → 件数を掛ける
  新: **中国のクリエイターがその仕事を受けるか** から下限を出す → 幅を持たせる

マーケットプレイスは、供給側が受けてくれなければ1件も成立しない。
だから拘束条件はクリエイター側にある。

  クリエイター受取 ＝ 発注額 × (1 − 手数料率)
  実効時給        ＝ 受取 ÷ 所要時間
  これが中国の実勢を上回らないと、誰も受けない。

出所
  中国の剪辑師（映像編集者）平均月給 8,935元 … Indeed 中国
  為替 1元＝21円［仮置き］

★ 所要時間・価格帯の上限・件数は私が置いた値。
⚠ Ver1.2の一本値（GMV83億・平均9万）には寄せない。積み上げた結果をそのまま出す。
"""

RMB = 21.0                      # 円/元［仮置き］
CN_MONTHLY_RMB = 8935.0         # 元/月。中国の剪辑師 平均月給（Indeed中国）
CN_HOURS = 168.0                # 月あたり労働時間（21日×8h）
FREELANCE = 1.4                 # ★フリーランス割増（社保・不安定性・営業時間の補償）

cn_hourly = CN_MONTHLY_RMB * RMB / CN_HOURS
floor_hourly = cn_hourly * FREELANCE

print("=" * 100)
print("まず、クリエイターがいくらなら受けるか")
print("=" * 100)
print("  中国の剪辑師 平均月給 %s元 × %.0f円 = 月 %s円" % (f"{CN_MONTHLY_RMB:,.0f}", RMB,
                                                  f"{CN_MONTHLY_RMB * RMB:,.0f}"))
print("  月%.0f時間で割ると 時給 %s円（雇用ベース）" % (CN_HOURS, f"{cn_hourly:,.0f}"))
print("  フリーランス割増 ×%.1f  →  **受注の判断ライン 時給 %s円**".replace("**", "")
      % (FREELANCE, f"{floor_hourly:,.0f}"))
print()
print("  ③は1人のクリエイターが完結する仕事なので、発注額はこの時給に工数を掛けたものになる。")
print("  価格の幅＝「工数の幅 × 時給の幅（新人1,600円〜熟練3,500円）」。")
print()
print("  手数料30%・クリエイター70%なので、発注額 ＝ 時給 × 工数 ÷ 0.70。")
print("  （20%だったときより発注額は 0.80/0.70 = 1.14倍になる。クリエイターの受取は変えない）")
print()

# 松田さんの決定（2026-09-23）: 手数料は一律30%。70%をクリエイターに渡す。
# 30%から決済手数料・送金手数料・システム原価を引いたものが粗利。
TAKE_PKG = 0.30
TAKE_CUSTOM = 0.30

# 30%の中身（すべてGMV比。★は［仮置き］）
PAY_CARD, PAY_CARD_MIX = 0.036, 0.80    # Stripe 国内カード 3.6%
PAY_BANK, PAY_BANK_MIX = 0.015, 0.20    # Stripe 銀行振込 1.5%
PAY_FEE = PAY_CARD * PAY_CARD_MIX + PAY_BANK * PAY_BANK_MIX
REMIT_FEE = 0.030                        # 中国の制作パートナー経由の送金・為替（松田さん指示）
SYS_COST_PER_TXN = 53                    # 円/件。systemcost.py で商品別に積んだ加重平均
                                         # （ストレージ・転送・AI-bot・アプリ基盤）

# ③は「1人のクリエイターが完結する」仕事（松田さんの定義）。
# だから価格は工数に連動する。単純な案件＝短時間＝安い、複雑な案件＝長時間＝高い。
# 時給にも幅がある。新人は判断ラインぎりぎり、熟練は上位の月収水準。
HOURLY_LO = 1600      # 円。受注判断ライン（平均月給8,935元＋フリーランス割増）に余裕を見た額
HOURLY_HI = 3500      # ★熟練クリエイター。月20,000元相当×フリーランス割増


def price_floor(hmin, take):
    """下限 ＝ クリエイターの留保価格。単純な案件を新人が受けても時給が出る額。
       丸めで判断ラインを割らないよう、500円単位で切り上げる"""
    import math
    return int(math.ceil(HOURLY_LO * hmin / (1 - take) / 500) * 500)


# 上限は「日本の発注者の留保価格」。これ以上なら発注者が既存手段を選ぶ、という線。
# 下限と上限は別々の側から決まる。挟まれた中で価格が動くのが市場の実態。


def block(title, items, take, note=""):
    print("=" * 100)
    print(title + "（手数料率 %.0f%%・1人のクリエイターが完結）" % (take * 100))
    print("=" * 100)
    print("  %-20s %9s %19s %11s %12s"
          % ("商品", "所要時間", "価格帯（下限=供給/上限=需要）", "受取（下限〜上限）", "実効時給"))
    print("  " + "-" * 86)
    out = []
    for name, hmin, hmax, hi, cnt, why in items:
        lo = price_floor(hmin, take)
        rl, rh = lo * (1 - take), hi * (1 - take)
        print("  %-20s %3.1f〜%4.1fh %8s〜%9s円 %6s〜%8s円 %5s〜%6s円"
              % (name, hmin, hmax, f"{lo:,}", f"{hi:,}",
                 f"{rl:,.0f}", f"{rh:,.0f}",
                 f"{rl / hmin:,.0f}", f"{rh / hmax:,.0f}"))
        out.append((name, lo, hi, cnt, hmin, hmax, why))
    print()
    if note:
        print("  " + note)
        print()
    return out


# (商品, 所要時間min, max, ★価格上限, 5期件数, 考え方)
# (商品, 工数min, max, ★上限＝日本の支払意思, 5期件数, 上限の根拠)
A = [
    ("SNS用ショート",        0.5, 1.5,   10000, 25000, "個人の動画編集外注 5千〜3万の下側"),
    ("誕生日ムービー",        1.0, 2.5,   15000, 12000, "サプライズ動画。数千〜2万"),
    ("記念日ムービー",        1.0, 3.0,   18000,  8000, "還暦・退職。誕生日より構成が重い"),
    ("イベント・余興ムービー",  2.0, 5.0,   30000, 10000, "二次会・余興 1〜5万"),
    ("WEBサイト用",          3.0, 8.0,   50000,  6000, "個人事業主のサイト用 3〜10万の下側"),
    ("ウェディングムービー",    5.0, 15.0,  80000,  9000, "結婚式ムービー外注 3〜10万"),
]
B = [   # 中身は①と同じ。違いは「③は1人・①は複数スタック」
    ("会社紹介ショート",       6.0, 12.0, 120000,  4000, "①の当社価格50万の1/4。1人作業の上限"),
    ("採用（小規模・1職種）",   8.0, 16.0, 180000,  2500, "①の当社価格100万の1/5〜1/6"),
    ("商品・サービス紹介",     6.0, 14.0, 150000,  5000, "機能数で振れる"),
    ("店舗・施設紹介",        5.0, 10.0, 100000,  3500, "撮影なし・生成のみ"),
    ("展示会・イベント告知",    4.0,  9.0,  80000,  2000, "①の当社価格30万の1/4"),
    ("SNS広告用（縦型3本）",   6.0, 12.0, 120000,  6000, "3本セット"),
]
C = [
    ("個人オーダーメイド",     3.0, 10.0,  150000,  8000, "パッケージに収まらない個別要望"),
    ("企業オーダーメイド",    10.0, 50.0, 1000000, 12000, "上限100万［Ver1.2の決定］"),
]

RA = block("③-A 個人向けパッケージ", A, TAKE_PKG,
           "※ 下限はクリエイターが受ける最低額、上限は発注者が既存手段に流れる手前の額。")
RB = block("③-B 中小企業向けパッケージ（内容は①と同じ）", B, TAKE_PKG,
           "※ 松田さんの定義: ①との違いは中身ではなく体制。③は1人、①は複数スタック。"
           "同じ「会社紹介」でも、人数が違えば価格が変わる。")
RC = block("③-C オーダーメイド（AI-botが仲介）", C, TAKE_CUSTOM,
           "※ 上限100万は Ver1.2 の決定。①の当社価格帯（30〜250万）と重なるので、"
           "発注者は「当社に任せる（①）か、自分でクリエイターとやり取りする（③）か」で選ぶ。")

# ── 価格帯のどこに落ちるか ────────────────────────────
# 松田さんの決定（2026-09-23）: 均等。期待単価は価格帯の中点。
W = [(1.00, 0.50)]   # (構成比, 価格帯の中での位置)


def expected(pmin, pmax):
    return sum(w * (pmin + (pmax - pmin) * pos) for w, pos in W)


print("=" * 100)
print("価格帯のどこに落ちるか（均等＝中点。松田さんの決定）")
print("=" * 100)
print("  %-22s %10s %10s %12s %10s %14s"
      % ("商品", "下限", "上限", "期待単価", "5期件数", "5期GMV(百万)"))
print("  " + "-" * 84)
tot = {}
for label, rows, take in [("A", RA, TAKE_PKG), ("B", RB, TAKE_PKG), ("C", RC, TAKE_CUSTOM)]:
    g = c = 0
    for name, pmin, pmax, cnt, hmin, hmax, why in rows:
        e = expected(pmin, pmax)
        gm = e * cnt / 1e6
        g += gm
        c += cnt
        print("  %-22s %9s円 %9s円 %11s円 %9s件 %13.0f"
              % (name, f"{pmin:,}", f"{pmax:,}", f"{e:,.0f}", f"{cnt:,}", gm))
    tot[label] = (g, c, take)
    print("  %-22s %31s %11s円 %9s件 %13.0f"
          % ("  小計 " + label, "", f"{g * 1e6 / c:,.0f}", f"{c:,}", g))
    print()

gmv5 = sum(v[0] for v in tot.values())
cnt5 = sum(v[1] for v in tot.values())
rev5 = sum(v[0] * v[2] for v in tot.values())
print("  " + "=" * 84)
print("  %-22s %31s %11s円 %9s件 %13.0f"
      % ("③ 合計（5期）", "", f"{gmv5 * 1e6 / cnt5:,.0f}", f"{cnt5:,}", gmv5))
print("  %-22s 実効手数料率 %.1f%%  →  ③ 売上 %.1f億"
      % ("", rev5 / gmv5 * 100, rev5 / 100))
print()

print("=" * 100)
print("幅で見たときの③（5期）")
print("=" * 100)
for tag, pos in [("全部が下限", 0.0), ("期待値", None), ("全部が上限", 1.0)]:
    g = r = 0
    for label, rows, take in [("A", RA, TAKE_PKG), ("B", RB, TAKE_PKG), ("C", RC, TAKE_CUSTOM)]:
        for name, pmin, pmax, cnt, hmin, hmax, why in rows:
            p = expected(pmin, pmax) if pos is None else pmin + (pmax - pmin) * pos
            g += p * cnt / 1e6
            r += p * cnt / 1e6 * take
    print("  %-12s GMV %6.1f億   ③売上 %5.1f億   平均単価 %8s円"
          % (tag, g / 100, r / 100, f"{g * 1e6 / cnt5:,.0f}"))
print()
print("  → 下限は「クリエイターが受ける最低ライン」なので、これを割ると供給が付かない。")
print("     上限は日本の発注者が払う気になる上限。実際はこの間に散る。")
print()
print("  ⚠ 幅が広いので、**どこで成約するかの置き方で③は7倍動く**。".replace("**", ""))
print("     下限寄りをどれだけ厚く見るかの感応度:")
print()
print("     %-28s %10s %10s %12s" % ("成約位置の分布", "GMV", "③売上", "平均単価"))
print("     " + "-" * 62)
for tag, ws in [("下限寄り90%/中位10%", [(0.90, 0.10), (0.10, 0.50)]),
                ("下限寄り75%/中位20%/上限5%", [(0.75, 0.12), (0.20, 0.50), (0.05, 0.85)]),
                ("下限寄り60%/中位30%/上限10%", [(0.60, 0.15), (0.30, 0.50), (0.10, 0.85)]),
                ("均等（採用）", [(1.00, 0.50)])]:
    g = 0
    for label, rows, take in [("A", RA, TAKE_PKG), ("B", RB, TAKE_PKG), ("C", RC, TAKE_CUSTOM)]:
        for name, lo, hi, cnt, hmin, hmax, why in rows:
            pr = sum(w * (lo + (hi - lo) * pos) for w, pos in ws)
            g += pr * cnt / 1e6
    print("     %-28s %9.1f億 %9.1f億 %11s円"
          % (tag, g / 100, g * 0.30 / 100, f"{g * 1e6 / cnt5:,.0f}"))
print()
print("     供給が厚い（必要なのは中国の母数の0.2%）ほど、成約価格は下限側に寄る。")
print("     「中国とやるから人が集まる」と「だから値段が下がる」は同じことの裏表。")
print("     採用したのは均等（中点）。上の4つで最も大きい置き方であり、")
print("     供給の厚さを踏まえると **上振れ側の前提** だという自覚が要る。".replace("**", ""))

# ── 期別（★立ち上がりカーブ）────────────────────────────
RAMP = {"A": [0.01, 0.07, 0.28, 0.62, 1.00],    # 1期から。仲介が要らない
        "B": [0.00, 0.04, 0.22, 0.58, 1.00],    # 2期から
        "C": [0.00, 0.00, 0.15, 0.55, 1.00]}    # 3期から。AI-botの開発後
CANNIB_A = [0.00, 0.0375, 0.18, 0.49, 1.00]     # ②-Cセルフサーブの立ち上がり（selfserve.py）
CANNIB_5 = 0.18                                  # ③-Aの件数のうち共食いする割合（SKU別の加重）

print()
print("=" * 100)
print("期別（②-C セルフサーブの共食いを差し引いた後）")
print("=" * 100)
Y = ["1期", "2期", "3期", "4期", "5期"]
gA5, cA5, _ = tot["A"]; gB5, cB5, _ = tot["B"]; gC5, cC5, _ = tot["C"]
gmv_y, rev_y, cnt_y = [], [], []
for i in range(5):
    a = gA5 * RAMP["A"][i] * (1 - CANNIB_5 * CANNIB_A[i])
    b = gB5 * RAMP["B"][i]
    c = gC5 * RAMP["C"][i]
    gmv_y.append(a + b + c)
    rev_y.append((a + b) * TAKE_PKG + c * TAKE_CUSTOM)
    cnt_y.append(cA5 * RAMP["A"][i] * (1 - CANNIB_5 * CANNIB_A[i])
                 + cB5 * RAMP["B"][i] + cC5 * RAMP["C"][i])
def r2(lab, v, f="{:>11,.0f}"):
    print(lab.ljust(26) + "".join(f.format(x) for x in v))
r2("", Y, "{:>11}")
print("-" * 100)
r2("GMV（百万円）", gmv_y)
r2("取引件数", cnt_y)
r2("平均単価（円）", [g * 1e6 / c if c else 0 for g, c in zip(gmv_y, cnt_y)])
r2("③ 売上（百万円）", rev_y)
r2("  実効手数料率(%)", [r / g * 100 if g else 0 for r, g in zip(rev_y, gmv_y)], "{:>11.1f}")
print("=" * 100)
print()
print("  plan用: GMV = %s" % [round(x) for x in gmv_y])
print("  plan用: C2C = %s" % [round(x) for x in rev_y])

print()
print("=" * 100)
print("30%の中身 — 何が引かれて、いくら残るか")
print("=" * 100)
avg = gmv5 * 1e6 / cnt5
print("  1件あたり（期待単価 %s円）" % f"{avg:,.0f}")
print("  " + "-" * 62)
print("  %-34s %12s  %7s" % ("発注者が支払う額（GMV）", f"{avg:,.0f}円", "100.0%"))
print("  %-34s %12s  %7s" % ("  クリエイターへ（70%）", f"{-avg * 0.70:,.0f}円", "-70.0%"))
print("  %-34s %12s  %7s" % ("当社の手数料収入（30%）", f"{avg * 0.30:,.0f}円", " 30.0%"))
items = [("決済手数料（Stripe 加重%.2f%%）" % (PAY_FEE * 100), avg * PAY_FEE),
         ("送金・為替（中国パートナー経由 %.0f%%）" % (REMIT_FEE * 100), avg * REMIT_FEE),
         ("システム原価（systemcost.py）", SYS_COST_PER_TXN)]
cogs = 0
for nm, v in items:
    cogs += v
    print("  %-34s %12s  %7s" % ("  − " + nm, f"{-v:,.0f}円", "%.1f%%" % (-v / avg * 100)))
gp = avg * 0.30 - cogs
print("  " + "-" * 62)
print("  %-34s %12s  %7s" % ("売上総利益", f"{gp:,.0f}円", "%.1f%%" % (gp / avg * 100)))
print("  %-34s %12s" % ("  手数料収入に対する粗利率", "%.1f%%" % (gp / (avg * 0.30) * 100)))
print()

print("  期別（百万円）")
print("  %-24s" % "" + "".join("%11s" % y for y in Y))
print("  " + "-" * 80)
cogs_y = [gmv_y[i] * (PAY_FEE + REMIT_FEE) + cnt_y[i] * SYS_COST_PER_TXN / 1e6 for i in range(5)]
gp_y = [rev_y[i] - cogs_y[i] for i in range(5)]
def r3(lab, v, f="%11.0f"):
    print("  %-24s" % lab + "".join(f % x for x in v))
r3("GMV", gmv_y)
r3("③ 売上（手数料30%）", rev_y)
r3("  − 決済・送金・システム", cogs_y)
r3("売上総利益", gp_y)
r3("  粗利率（対 手数料収入）", [g / r * 100 if r else 0 for g, r in zip(gp_y, rev_y)], "%10.1f%%")
print()
print("  plan用: C2C_GP_RATE = %s" % [round(g / r, 3) if r else 0 for g, r in zip(gp_y, rev_y)])
print()
print("  → 粗利率は %.0f%%前後。従来モデルで置いていた85%%より低い。"
      % (gp_y[-1] / rev_y[-1] * 100))
print("     決済手数料はGMV比で効くので、**単価が下がるほど粗利率が悪化する**構造。"
      .replace("**", ""))
print("     システム原価が件数比なので、安い案件ほど重い。1件120円は 1,000円の案件では12%%。")

print()
print("=" * 100)
print("必要なクリエイター数 — ここが「なぜ中国か」の答えになる")
print("=" * 100)
tot_h = 0
for label, rows in [("A", RA), ("B", RB), ("C", RC)]:
    for name, lo, hi, cnt, hmin, hmax, why in rows:
        tot_h += cnt * (hmin + hmax) / 2
FTE_HOURS = 1800.0
fte3 = tot_h / FTE_HOURS
# ① の分（1本あたり中国クリエイター支払 12万×難度1.55、実効時給4,000円想定）
UNITS1, CRE_PAY1, EFF_HOURLY1 = 3780, 120000 * 1.55, 4000
h1 = UNITS1 * CRE_PAY1 / EFF_HOURLY1
fte1 = h1 / FTE_HOURS
CN_POOL = 690000    # 人。微短劇産業の直接就業者（中国網絡視聴協会 2024）

print("  ③ 年 %s時間 ÷ 1人年%s時間 = %s人（フル稼働換算）"
      % (f"{tot_h:,.0f}", f"{FTE_HOURS:,.0f}", f"{fte3:,.0f}"))
print("  ① 年 %s時間（支払総額 %.1f億 ÷ 実効時給%s円）= %s人"
      % (f"{h1:,.0f}", UNITS1 * CRE_PAY1 / 1e8, f"{EFF_HOURLY1:,}", f"{fte1:,.0f}"))
print("  " + "-" * 62)
print("  合計 %s人（フル稼働換算）／ 登録ベースは2〜3倍で %s〜%s人"
      % (f"{fte1 + fte3:,.0f}", f"{(fte1 + fte3) * 2:,.0f}", f"{(fte1 + fte3) * 3:,.0f}"))
print()
print("  中国の母数: 微短劇産業の直接就業者 約%s万人（中国網絡視聴協会 2024）"
      % f"{CN_POOL / 10000:,.0f}")
print("  上下流を含めた波及は203万人。短視頻産業の市場規模は4,200億元。")
print()
print("  → 必要なのは登録 %s〜%s人。母数 %s万人に対して **%.2f〜%.2f%%**。"
      .replace("**", "") % (f"{(fte1 + fte3) * 2:,.0f}", f"{(fte1 + fte3) * 3:,.0f}",
                            f"{CN_POOL / 10000:,.0f}",
                            (fte1 + fte3) * 2 / CN_POOL * 100, (fte1 + fte3) * 3 / CN_POOL * 100))
print()
print("  これは制約ではなく、**中国とやる理由そのもの**です。".replace("**", ""))
print("  同じ人数を日本で集めるなら、時給1,600〜3,500円で受ける映像クリエイターを")
print("  千人規模で確保することになり、それは成立しません。")
print("  「人が集まるか」が問題にならない場所を選んだ、という設計です。")
print()
print("=" * 100)
print("⚠ 残る弱点")
print("=" * 100)
ent = [r for r in RC if r[0] == "企業オーダーメイド"][0]
elo, ehi, ecnt = ent[1], ent[2], ent[3]
e = expected(elo, ehi)
print("  1 企業オーダーメイド1商品で、5期GMVの %.0f%%（%.1f億）。価格帯 %s〜%s円、期待単価 %s円。"
      % (e * ecnt / 1e6 / gmv5 * 100, e * ecnt / 1e8, f"{elo:,}", f"{ehi:,}", f"{e:,.0f}"))
print("    下限に張り付くと ③売上は %.2f億 減る。価格帯が最も広いので、ここが一番動く。"
      % ((e - elo) * ecnt / 1e6 * TAKE_CUSTOM / 100))
print()
print("  2 上限は「日本の発注者がここまでなら払う」という線で、実測ではない。★")
print("    下限（クリエイターの留保価格）は中国の賃金データから出ているが、上限は推定。")
print("    実際には競争で下限側に寄る可能性がある。だから期待値は下限寄りに置いている。")
print()
print("  3 システム原価53円/件は systemcost.py で積んだ（S3・CloudFrontの公表単価ベース）。")
print("    送金3%は松田さんの指示値。中国パートナーの取り分が30%側か70%側かは未確定。")
print("    中国の制作パートナーとの契約で、パートナー取り分が30%側から出るのか")
print("    クリエイターの70%側から出るのかが決まっていない。")
