# -*- coding: utf-8 -*-
"""② チェックポイント・LoRA・工程ツールの価格が適正かを、実勢と突き合わせる

これらは私が★として置いた値で、外部の裏取りをしていなかった。ここで検算する。

出所（1ドル150円）
  HeyGen Business        $7,500/年（25席）        … 25席で割ると $300/席/年
  エンタープライズ導入      $25,000〜40,000/年       … Vendr 中央値 $30,000（AI動画SaaS）
  HeyGen カスタムアバター   $1,000/体/年
  Adobe Firefly Premium  $199.99/月              … 50,000クレジット
  Runway Max             $76/月（年払い）
"""

USD = 150.0

HEYGEN_BIZ_YR, HEYGEN_SEATS = 7500 * USD, 25
ENT_LO, ENT_MID, ENT_HI = 25000 * USD, 30000 * USD, 40000 * USD
AVATAR_YR = 1000 * USD
FIREFLY_YR = 199.99 * 12 * USD
RUNWAY_YR = 76 * 12 * USD

# 当社の設定（★私が置いた値）
CP_ENT, CP_STD = 300 * 10000, 100 * 10000
TOOL_SEAT_YR = 24 * 10000
SEATS_ENT, SEATS_STD = 10, 3
LORA_M, LORA_B = 24 * 10000, 80 * 10000
ENT_TOTAL = CP_ENT + TOOL_SEAT_YR * SEATS_ENT + LORA_M
STD_TOTAL = CP_STD + TOOL_SEAT_YR * SEATS_STD + LORA_M


def yen(v):
    return "%s円" % f"{v:,.0f}"


print("=" * 92)
print("実勢（1ドル150円）")
print("=" * 92)
for lab, v, note in [
        ("HeyGen Business（25席）", HEYGEN_BIZ_YR, "1席あたり %s/年" % yen(HEYGEN_BIZ_YR / HEYGEN_SEATS)),
        ("AI動画SaaS エンタープライズ 中央値", ENT_MID, "レンジ %s〜%s" % (yen(ENT_LO), yen(ENT_HI))),
        ("HeyGen カスタムアバター", AVATAR_YR, "1体/年"),
        ("Adobe Firefly Premium", FIREFLY_YR, "1席/年"),
        ("Runway Max", RUNWAY_YR, "1席/年")]:
    print("  %-34s %14s   %s" % (lab, yen(v), note))
print()

print("=" * 92)
print("判定① 法人プランの年額")
print("=" * 92)
print("  %-24s %14s %16s %s" % ("", "当社", "実勢", "判定"))
print("  " + "-" * 80)
ok_ent = ENT_LO <= ENT_TOTAL <= ENT_HI
print("  %-24s %14s %16s %s"
      % ("Enterprise（10席）", yen(ENT_TOTAL), "%s〜%s" % (yen(ENT_LO), yen(ENT_HI)),
         "○ レンジ内" if ok_ent else "× レンジ外"))
print("  %-24s %14s %16s %s"
      % ("　中央値との比", "", yen(ENT_MID), "%.2f倍" % (ENT_TOTAL / ENT_MID)))
print("  %-24s %14s %16s %s"
      % ("Standard（3席）", yen(STD_TOTAL), yen(HEYGEN_BIZ_YR),
         "HeyGen Business(25席)の %.2f倍" % (STD_TOTAL / HEYGEN_BIZ_YR)))
print()
print("  → Enterprise 564万は、AI動画SaaSのエンタープライズ導入 375〜600万の中に収まる。**適正**。"
      .replace("**", ""))
print()

print("=" * 92)
print("判定② 席単価 — ここが問題")
print("=" * 92)
ours = TOOL_SEAT_YR
print("  %-34s %14s %s" % ("当社 工程ツール（1席/年）", yen(ours), ""))
print("  " + "-" * 80)
for lab, v in [("HeyGen Business", HEYGEN_BIZ_YR / HEYGEN_SEATS),
               ("Runway Max", RUNWAY_YR),
               ("Adobe Firefly Premium", FIREFLY_YR)]:
    print("  %-34s %14s   当社は %.1f倍" % (lab, yen(v), ours / v))
print()
print("  → 当社の席単価24万/年は、AI動画ツールの席単価の 0.7〜5.3倍。**比較対象で大きくぶれる**。"
      .replace("**", ""))
print("     Firefly Premium（36万/年）より安く、HeyGen Business（4.5万/年）より5倍高い。")
print()
print("  どちらが正しい比較か:")
print("    ・HeyGen/Runway はアバター生成・クリップ生成の**単機能ツール**。席を増やして使う。")
print("    ・当社の工程ツールは**制作会社の工程に入る道具**（要件定義・自動チェック）。")
print("      買い手は既に Adobe CC や編集ソフトに席単価を払っている層。")
print("    → Firefly Premium 36万/年が最も近い比較対象で、当社24万はその2/3。**高すぎない**。"
      .replace("**", ""))
print()

print("=" * 92)
print("判定③ LoRA — ここは説明が要る")
print("=" * 92)
print("  %-34s %14s" % ("当社 LoRA 個別構築（初期・都度）", yen(LORA_B)))
print("  %-34s %14s" % ("当社 LoRA 年間保守", yen(LORA_M)))
print("  %-34s %14s" % ("HeyGen カスタムアバター（年額）", yen(AVATAR_YR)))
print("  " + "-" * 80)
print("  保守 24万 vs アバター 15万 … %.1f倍。**近い**" .replace("**", "") % (LORA_M / AVATAR_YR))
print("  構築 80万 vs アバター 15万 … %.1f倍。**開きがある**" .replace("**", "") % (LORA_B / AVATAR_YR))
print()
CN_HOURLY = 8935 * 21 / 168 * 1.4
for h in [20, 30, 40, 50]:
    print("    構築80万が %2d時間の作業なら 時給 %s" % (h, yen(LORA_B / h)))
print()
print("  → HeyGenのアバターは「動画を撮って学習させる」標準化された工程。")
print("     当社のLoRAは顧客のブランド・商品を学習させる個別開発で、データ整備と反復が要る。")
print("     40〜50時間なら時給1.6〜2万円。制作会社向けの受託単価としては妥当。")
print("     ただし**工数の裏取りはしていない**。実測が出るまでは★のまま。".replace("**", ""))
print()

print("=" * 92)
print("結論")
print("=" * 92)
print("  Enterprise 564万/年   ○ 実勢レンジ（375〜600万）の中。中央値の %.2f倍" % (ENT_TOTAL / ENT_MID))
print("  Standard 196万/年     △ 席単価は妥当だが、3席で196万は中小制作会社には重い可能性")
print("  工程ツール 24万/席/年  ○ Firefly Premium 36万の2/3。単機能ツールとは比較対象が違う")
print("  LoRA 保守 24万/年     ○ カスタムアバター15万と近い")
print("  LoRA 構築 80万/都度   △ 工数の裏取りがない。40〜50時間前提なら妥当")
print()
print("  ★ 唯一気になるのは Standard。3席で196万は、Enterprise(10席564万)と比べて")
print("     席あたりが割高になっている（65万/席 vs 56万/席）。")
print("     小さい方が席単価が高いのは普通だが、買い手は中小制作会社なので逆風になりうる。")
print("     席数を3→5に増やすか、チェックポイントStandardを100万→80万に下げる余地がある。")
