# -*- coding: utf-8 -*-
"""③ のシステム原価を、商品別に積む

⚠ これまで「120円/件」と置いていたが、**あれは根拠がない。私が置いただけの数字**だった。
   ここで積み直す。

原価の中身
  ストレージ   成果物 ＋ 中間版。検収後も一定期間は保管する
  転送        発注者のプレビューとダウンロード
  AI-bot      要件ヒアリングと仕様書化。③-C オーダーメイドだけに発生する
  アプリ基盤   アプリサーバー・DB・通知・監視。件数で按分

出所
  S3 Standard 東京   1TB/月 ≈ $25（約3,750円）→ 3.66円/GB/月
  CloudFront 東京    $0.085/GB
  為替 1ドル150円［仮置き］
★ 尺・保管期間・転送回数・LLMトークン数・アプリ基盤費は私が置いた値。
"""

USD = 150.0
STORAGE_YEN_GB_MONTH = 25 * USD / 1024        # S3 Standard 東京
CDN_YEN_GB = 0.085 * USD                       # CloudFront 東京
MB_PER_MIN = 60.0                              # ★1080p H.264 約8Mbps
KEEP_MONTHS = 3                                # ★検収後の保管期間
VERSIONS = 3                                   # ★成果物＋中間版2本
TRANSFER_X = 4                                 # ★プレビュー＋ダウンロードの合計転送量倍率

# AI-bot（③-C のみ）★中位モデルのAPI公表価格
LLM_IN_TOK, LLM_OUT_TOK = 30000, 12000
LLM_IN_USD_M, LLM_OUT_USD_M = 3.0, 15.0
LLM_YEN = (LLM_IN_TOK / 1e6 * LLM_IN_USD_M + LLM_OUT_TOK / 1e6 * LLM_OUT_USD_M) * USD

# アプリ基盤（★月額を件数で按分）
PLATFORM_YEN_MONTH = 300000
TXN_PER_YEAR = 113000

print("=" * 96)
print("単価")
print("=" * 96)
print("  ストレージ  %6.2f 円/GB/月   S3 Standard 東京（1TB/月 ≈ $25）" % STORAGE_YEN_GB_MONTH)
print("  転送       %6.2f 円/GB      CloudFront 東京（$0.085/GB）" % CDN_YEN_GB)
print("  AI-bot    %6.2f 円/件      入力%s＋出力%sトークン ★"
      % (LLM_YEN, f"{LLM_IN_TOK:,}", f"{LLM_OUT_TOK:,}"))
print("  アプリ基盤  %6.2f 円/件      月%s円 ÷ 年%s件 ÷ 12 ★"
      % (PLATFORM_YEN_MONTH * 12 / TXN_PER_YEAR, f"{PLATFORM_YEN_MONTH:,}", f"{TXN_PER_YEAR:,}"))
PLATFORM_PER_TXN = PLATFORM_YEN_MONTH * 12 / TXN_PER_YEAR
print()

# (商品, ★完成尺(分), 5期件数, AI-botを使うか)
ITEMS = [
    ("SNS用ショート",         0.5, 25000, False),
    ("誕生日ムービー",         2.0, 12000, False),
    ("記念日ムービー",         2.5,  8000, False),
    ("イベント・余興ムービー",   4.0, 10000, False),
    ("WEBサイト用",           1.5,  6000, False),
    ("ウェディングムービー",    12.0,  9000, False),
    ("会社紹介ショート",        2.0,  4000, False),
    ("採用（小規模・1職種）",    3.0,  2500, False),
    ("商品・サービス紹介",      2.0,  5000, False),
    ("店舗・施設紹介",         1.5,  3500, False),
    ("展示会・イベント告知",     2.0,  2000, False),
    ("SNS広告用（縦型3本）",    1.5,  6000, False),
    ("個人オーダーメイド",       3.0,  8000, True),
    ("企業オーダーメイド",       4.0, 12000, True),
]

print("=" * 96)
print("商品別のシステム原価（円/件）")
print("=" * 96)
print("  %-22s %6s %8s %9s %9s %9s %9s %9s"
      % ("商品", "尺(分)", "容量MB", "ストレージ", "転送", "AI-bot", "基盤", "合計"))
print("  " + "-" * 86)
tot_cost = tot_cnt = 0
for name, mins, cnt, bot in ITEMS:
    size_gb = mins * MB_PER_MIN / 1024
    storage = size_gb * VERSIONS * KEEP_MONTHS * STORAGE_YEN_GB_MONTH
    transfer = size_gb * TRANSFER_X * CDN_YEN_GB
    llm = LLM_YEN if bot else 0.0
    total = storage + transfer + llm + PLATFORM_PER_TXN
    tot_cost += total * cnt
    tot_cnt += cnt
    print("  %-22s %6.1f %8.0f %9.1f %9.1f %9.1f %9.1f %9.1f"
          % (name, mins, mins * MB_PER_MIN, storage, transfer, llm, PLATFORM_PER_TXN, total))
print("  " + "-" * 86)
avg = tot_cost / tot_cnt
print("  %-22s %6s %8s %9s %9s %9s %9s %9.1f" % ("加重平均", "", "", "", "", "", "", avg))
print()
print("  → 加重平均 **%.0f円/件**。これまで置いていた120円は %.1f倍だった。"
      .replace("**", "") % (avg, 120 / avg))
print("     年間の総額 %s円（5期・%s件）" % (f"{tot_cost:,.0f}", f"{tot_cnt:,}"))
print()
print("=" * 96)
print("どこが効くか")
print("=" * 96)
print("  1 尺が長いものほど重い。ウェディング(12分)は SNS(0.5分)の %.0f倍。"
      % ((12 * MB_PER_MIN / 1024 * (VERSIONS * KEEP_MONTHS * STORAGE_YEN_GB_MONTH + TRANSFER_X * CDN_YEN_GB))
         / (0.5 * MB_PER_MIN / 1024 * (VERSIONS * KEEP_MONTHS * STORAGE_YEN_GB_MONTH + TRANSFER_X * CDN_YEN_GB))))
print("  2 AI-botは③-Cだけ。%.0f円/件は、パッケージには乗らない。" % LLM_YEN)
print("  3 アプリ基盤 %.0f円/件は件数で薄まる。件数が倍なら半分になる。" % PLATFORM_PER_TXN)
print()
print("  ⚠ 安い商品ほど原価率が重い。SNS用ショートは下限1,500円・手数料450円に対し、")
sns = 0.5 * MB_PER_MIN / 1024
sns_cost = sns * VERSIONS * KEEP_MONTHS * STORAGE_YEN_GB_MONTH + sns * TRANSFER_X * CDN_YEN_GB + PLATFORM_PER_TXN
print("     システム原価 %.0f円。手数料の %.0f%% がここで消える。" % (sns_cost, sns_cost / 450 * 100))
print("     決済手数料(3.18%)と送金(3%)を足すと、下限での成約は利益が薄い。")
