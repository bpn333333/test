# -*- coding: utf-8 -*-
"""
AI映像制作事業 5年計画モデル（映像制作メイン・プラットフォーム副次版）
単位: 百万円。1期 = 2026/10-2027/9

出所つきの単位あたり数字と、[仮置き]の数量前提を分けて持つ。
"""
Y = ["1期", "2期", "3期", "4期", "5期"]

# ---- 出所のある単価・率 --------------------------------------------------
GM_P1   = 0.60   # 制作受託の粗利率  BUSINESS_PLAN 7-1（実力値63%を保守的に60%）
GM_PF   = 0.85   # PF（純額計上のため原価は配信インフラのみ）[仮置き]
GM_P4   = 0.80   # プロダクト外販   MARKET_SIZING 10章
ARPU    = 464    # 円/MAU/年（当社取り分） PLATFORM_PIVOT 11-3
PAY_SH  = 324/464  # うち課金の割合（残りが広告）
TAKE_PAY= 0.30   # 課金テイクレート PLATFORM_PIVOT 2章

# ---- [仮置き] 数量前提 ---------------------------------------------------
UNITS   = [54, 190, 420, 836, 1667]     # 制作本数  BUSINESS_PLAN 7-3（4-5期は外挿）
PRICE   = [0.50, 0.55, 0.60, 0.60, 0.60] # 平均単価（百万円）
MAU_END = [6, 25, 55, 90, 125]          # 期末MAU（万人）[仮置き]
MONTHS  = [7, 12, 12, 12, 12]           # PF稼働月数（1期は2027/4公開）
P4      = [0, 0, 30, 120, 300]          # プロダクト外販の売上 [仮置き]
HEADS   = [6, 14, 25, 36, 50]           # 日本側人員
PAY_PP  = [5.0, 7.0, 8.0, 9.0, 10.0]    # 1人あたり人件費（百万円）
ADS     = [15, 60, 120, 180, 230]       # 流量投放 [仮置き]
SGA_OTH = [20, 45, 80, 120, 150]        # その他販管費 [仮置き]

# ---- 計算 ----------------------------------------------------------------
rev_p1 = [round(u*p) for u, p in zip(UNITS, PRICE)]

mau_avg, rev_pf = [], []
prev = 0
for end, m in zip(MAU_END, MONTHS):
    avg = (prev + end) / 2
    mau_avg.append(avg)
    rev_pf.append(round(avg * 10000 * ARPU * (m/12) / 1_000_000))
    prev = end

rev_tot = [a+b+c for a, b, c in zip(rev_p1, rev_pf, P4)]
gp = [round(a*GM_P1 + b*GM_PF + c*GM_P4) for a, b, c in zip(rev_p1, rev_pf, P4)]
pay = [round(h*p) for h, p in zip(HEADS, PAY_PP)]
op  = [g - w - a - s for g, w, a, s in zip(gp, pay, ADS, SGA_OTH)]

gmv_pay = [r*PAY_SH/TAKE_PAY for r in rev_pf]           # 課金の流通総額
ratio   = [a/g*100 if g else 0 for a, g in zip(ADS, gmv_pay)]

def row(label, vals, f="{:>8,}"):
    print(label.ljust(22) + "".join(f.format(v) for v in vals))

print("="*62)
print("売上（百万円）")
row("  P1 制作受託", rev_p1); row("  P2+P3 PF課金・広告", rev_pf); row("  P4 プロダクト外販", P4)
row("  合計", rev_tot)
print("-"*62)
row("売上総利益", gp)
row("  人件費", pay); row("  流量投放", ADS); row("  その他販管費", SGA_OTH)
row("営業利益", op)
row("営業利益率(%)", [round(o/r*100, 1) for o, r in zip(op, rev_tot)], "{:>8}")
print("-"*62)
row("期末MAU(万人)", MAU_END); row("期中平均MAU(万人)", mau_avg, "{:>8}")
row("日本側人員", HEADS)
row("投放÷課金GMV(%)", [round(x) for x in ratio])
row("人手に比例しない%", [round((b+c)/t*100) for b, c, t in zip(rev_pf, P4, rev_tot)])
print("="*62)

# ---- 資金繰り ------------------------------------------------------------
WC = [round(r*1.7/12) for r in rev_tot]      # 運転資金所要 ≒ 売上1.7ヶ月
raise_ = [150, 300, 0, 0, 0]                 # シード1.5億 / シリーズA 3億
cash, prev_wc = 0, 0
print("資金繰り（百万円）")
for i in range(5):
    d_wc = WC[i] - prev_wc
    cash += raise_[i] + op[i] - d_wc
    print(f"  {Y[i]}  調達{raise_[i]:>5,}  営業利益{op[i]:>6,}  運転資金増{d_wc:>5,}  → 期末現金 {cash:>6,}")
    prev_wc = WC[i]
print("="*62)

# ---- 上場時の時価総額（デッキp18と同じ3手法） ----------------------------
rev5, op5 = rev_tot[4], op[4]
net = op5 * 0.67
DEP = 40  # 累計開発投資 約2.05億の5年償却 [仮置き]
ebitda = op5 + DEP
print("5期の時価総額試算（百万円）")
print(f"  PSR法        売上{rev5:,} × 2〜5倍        = {rev5*2:,} 〜 {rev5*5:,}")
print(f"  PER法        純利益{net:,.0f} × 20〜40倍    = {net*20:,.0f} 〜 {net*40:,.0f}")
print(f"  EV/EBITDA法  EBITDA{ebitda:,} × 8.9〜15倍  = {ebitda*8.9:,.0f} 〜 {ebitda*15:,.0f}")

# ---- 感応度① 5期の制作平均単価（本数1,667本は据え置き） -----------------
print("="*62)
print("感応度① 5期の制作平均単価")
for p in [0.70, 0.60, 0.50, 0.40]:
    r1 = round(1667*p); tot = r1 + rev_pf[4] + P4[4]
    g  = round(r1*GM_P1 + rev_pf[4]*GM_PF + P4[4]*GM_P4)
    o  = g - pay[4] - ADS[4] - SGA_OTH[4]
    mk = "  <-標準" if abs(p-0.60) < 1e-9 else ""
    print(f"  単価{p*100:>3.0f}万  売上{tot:>6,}  営業利益{o:>6,} ({o/tot*100:>5.1f}%){mk}")

# ---- 感応度② 5期の期中平均MAU -------------------------------------------
print("感応度② 5期の期中平均MAU（制作・プロダクトは据え置き）")
for m in [150, 107.5, 70, 40]:
    rp = round(m*10000*ARPU/1_000_000); tot = rev_p1[4] + rp + P4[4]
    g  = round(rev_p1[4]*GM_P1 + rp*GM_PF + P4[4]*GM_P4)
    o  = g - pay[4] - ADS[4] - SGA_OTH[4]
    mk = "  <-標準" if abs(m-107.5) < 1e-9 else ""
    print(f"  MAU{m:>6.1f}万  売上{tot:>6,}  営業利益{o:>6,} ({o/tot*100:>5.1f}%){mk}")

# ---- ランウェイ ----------------------------------------------------------
print("="*62)
burn1 = (pay[0] + ADS[0] + SGA_OTH[0] - gp[0]) / 12
print(f"1期の月次バーン（粗利控除後） = {burn1:>5.1f} 百万/月")
print(f"シード150百万 ÷ バーン        = {150/burn1:>5.1f} ヶ月（運転資金・開発投資を除く）")
