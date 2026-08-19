# 販売チャネル・配信チャネル 調査

調査日: 2026-08-19

## この調査の限界(先に読むこと)

- **すべて検索結果の要約に基づく。** この開発環境は外部ページの直接取得が
  ネットワークポリシーで遮断されているため、公式ページの原文を読めていない
- 手数料率・API料金・規約は変動する。**金額に関わる判断の前に、必ず各社の
  公式ページで一次情報を確認すること**
- 法規制の記述は論点の整理であって、法的助言ではない

---

## 1. EA販売プラットフォーム

### 手数料の比較

| プラットフォーム | 販売手数料 | 開発者の取り分 | 市場 |
|---|---|---|---|
| **MQL5 Market** | 20% | 80% | 世界(MT4/MT5ユーザーが直接来る) |
| **MQL5 Signals**(シグナル購読) | 20% | 80% | 世界 |
| **GogoJungle** | 35% | 65% | 日本最大 |
| GogoJungle(アフィリエイト併用) | 35% + 10%〜 | 55% | 日本 |
| 自社販売(BASE/Stripe等) | 決済手数料のみ(3〜4%) | 96%前後 | 集客は自前 |

**MQL5 Market の 20% は突出して条件が良い。** かつ、MT5ユーザーが端末内から
直接買えるため、集客を自前で用意しなくても露出が発生する。
海外展開を軸にするなら、ここが第1候補。

### MQL5 Market の制約(設計に直結する)

出品前に強制的な検証(バリデーション)を通る必要があり、以下が禁止されている。

- **DLL呼び出しの禁止**(Windows システムライブラリを含む)
- **WebRequest を使ったライセンス管理・更新管理・課金システムの禁止**
  (第三者の販売/会計/ライセンス制御システムの組み込み全般が不可)
- 動作制限のある製品の禁止(期間限定・口座限定・通貨ペア限定は不可。
  有料・無料を問わず、どの口座でも完全に機能する必要がある)
- チャート上・ダイアログでの自社サイトや他製品の宣伝の禁止
- ポップアップや多数のリンクなど、押しつけがましい機能の禁止
- 「Demo」「Free」「Trial」「Light」等を名前に含む制限版はスパム扱い
- 複数アカウント・匿名でのSeller登録は不可
- EAは「実際に取引すること」が必須

> **設計への影響(重要):** MQL5 Market に出す EA は、**外部サーバーと通信して
> シグナルを取りに行く構成にできない。** 現在の `SignalFile.mqh` は
> ファイル書き出しのみなので問題ないが、「クラウドでロジックを回して EA は
> 実行するだけ」という構成にすると出品できない。
> **EA本体に判定ロジックを内包する構成を維持すること。**

### MQL5 Signals(シグナル購読)

自分の口座の取引を配信し、購読者が自動コピーする仕組み。手数料20%。
購読期間の終了から約1週間で支払われる。出金は PayPal / 銀行カード等。

- EA を売らずに「実績のある口座」自体を収益化できる
- **実際に自分の口座で運用した結果がそのまま実績になる**(検証コストが二重にならない)
- 販売と違い、成績が落ちれば購読者が減る = 継続的な運用品質が要る

### コピートレード系(EA販売の代替)

| プラットフォーム | モデル |
|---|---|
| **Darwinex** | 戦略をDARWINという投資商品に変換。リスクエンジンが目標VaRに正規化。成功報酬 15〜20%。第三者投資家の資金を集められる。英FCA規制下 |
| **ZuluTrade** | 37以上のFXブローカーに対応。プロフィットシェア型(フォロワーが勝ったときだけ報酬)+スプレッドマークアップ |

**Darwinex は「EAを売る」のではなく「運用実績で報酬を得る」モデル。**
販売に伴う投資助言規制の論点を回避しやすく、かつ自己資金の少なさを
外部資金で補える。**3戦略の統合運用と最も相性が良い可能性がある。**

---

## 2. ブローカーサイトへの設置について

調査した限り、「ブローカーのサイトにEAを置いて販売する」という
一般的な仕組みは見つからなかった。ブローカー側の代表的な収益共有の形は
**IB(Introducing Broker)/アフィリエイト**であり、構造が違う。

| モデル | 内容 |
|---|---|
| ロット単位リベート | 紹介客の取引1ロットあたり固定額。相場は **$2〜$10/ロット**。大口IBはより高率 |
| スプレッドリベート | ブローカーが得たスプレッド収益の一定割合を還元 |
| レベニューシェア | 紹介客から得た収益の割合(例:30%)を受け取る |
| マスターIB | 配下にサブIBを持ち、その取引量からもオーバーライド報酬 |

**つまりブローカー経由の現実的な形は「EAを無料配布し、指定ブローカーで
口座開設させてIB報酬を得る」。** EA販売の代わりに取引量から収益を得るモデル。

- 利点: 顧客の初期費用がゼロなので配布数が伸びる。継続収益になる
- 欠点: **EAが高頻度で取引するほど自分の収益が増える構造**になり、
  利用者の利益と自分の利益が対立しうる。スキャルピングEAとの組み合わせは
  特に利益相反が起きやすい。信用を毀損すると全事業に波及する

> IBモデルを採るなら、**利益相反を開示するか、採らないかを先に決めること。**

---

## 3. Kindle(AIをトレードに使う方法)

### ロイヤリティ

| 条件 | 印税率 | 価格帯 |
|---|---|---|
| KDPセレクト登録(Amazon独占) | **70%** | ¥250〜¥1,250 |
| 非独占 | 35% | ¥99〜¥20,000 |

- 70%プランはファイルサイズに応じた配信コストが差し引かれる(35%プランは無し)
- 70%を取るには**Amazon独占**が条件。楽天Kobo等で並売できなくなる
- Kindle Unlimited(読み放題)の既読ページ数による収益もKDPセレクト登録が前提

### 競合状況

このジャンルは**2026年時点で活発かつ飽和しつつある。**
検索で確認できた近接タイトル:

- "AI Stock Trading Playbook"(2026年向けを明示したシリーズ物)
- "Trading and Artificial Intelligence (AI)" シリーズ(2026年1月の新刊あり)
- **"Build TradingView Signals with Claude Code"**
- **"The No-BS Guide To Agentic AI For Traders: Let AI Agents Research,
  Analyze, and Execute Trades While You Sleep"**

英語圏では「AIエージェントにトレードをやらせる」という切り口まで既に
出版されている。**一般論の「AI×トレード」で後発参入しても埋もれる。**

差別化できるとすれば、**実際に自分で作ったツールと検証記録を持っていること**。
「AIの使い方」ではなく「AIと作ったツールで実際にどう検証したか、
何が失敗したか」という一次情報。これは既存 HANDOFF.md にある
「管理職向けAI教育」の Kindle 戦略とは別テーマとして立つ。

---

## 4. 配信チャネル(X / YouTube)

### X API の料金(2026年、大きく変わっている)

| プラン | 状態 |
|---|---|
| Free | 存在するが投稿上限は小さい |
| Basic($200/月) | **新規受付終了。** 2026年6月1日から従量課金へ強制移行 |
| Pro($5,000/月) | 新規受付終了 |
| **従量課金** | **投稿 $0.015/件、リンクを含む投稿 $0.20/件、読み取り $0.005/件。月額最低額なし** |

> **設計への影響:** **リンクを含む投稿は13倍のコスト。**
> 1日3投稿 × 30日 = 90投稿の場合、
> リンク無し **月 $1.35** / リンク有り **月 $18**。
> シグナル速報はリンク無し、誘導はまとめ投稿にだけリンクを付ける、
> といった使い分けで大きく差が出る。

自動化ポリシー上、同一・類似内容の連投は制限対象。
`PublisherConfig` の上限を緩めないこと。

### YouTube のAI生成コンテンツ規約(2026年7月16日施行)

**「AIエージェントで自動発信」という当初の構想は、そのままだと収益化できない。**

- 「不真正なコンテンツ(inauthentic content)」の定義が明確化された。
  第1カテゴリが**AI・CGI・テンプレートに大きく依存した、ほぼ同一の
  反復コンテンツ**で、これが収益化不可
- 一方、**編集・制作・脚本にAIを使うこと自体は許容される。**
  独自の価値があり、品質基準を満たしていれば収益化できる
- 「あなたの人格が動画の中心にあること」「人間的でオリジナルであること」が判断軸
- 罰則の中心は動画削除ではなく**収益化剥奪**

> **結論: YouTube を広告収益源として設計しない。**
> 集客ファネル(EAとシグナルへの導線)として設計し、
> 本人が顔と声で出る前提にする。AIは台本・編集・分析の補助に使う。

---

## 5. 各国の規制(販売先を広げる前に)

### 日本

`docs/COMPLIANCE.md` を参照。有償のシグナル配信は金商法の
投資助言・代理業の登録が論点。無登録営業は刑事罰の対象。

### 米国(NFA / CFTC)

- **報酬を得て**先物・オプション・店頭FXの売買について助言する者は
  **CTA(Commodity Trading Advisor)登録**が必要。
  **自動売買システム・シグナルサービスもこれに含まれる**とされている
- 免除の例:
  - 過去12ヶ月で助言した相手が **15人以下** かつ CTA として一般に
    表示していない場合
  - **個々の顧客に個別化されない標準化された助言で、顧客口座に対する
    裁量を持たない場合**(購読型のコピートレードへのアクセス提供など)
- 登録CTAのうち、顧客口座に裁量を持つ者・顧客の事情に合わせた助言をする者は
  NFA会員である必要がある

> **重要:** 「全員に同じシグナルを配る」形と「個別に助言する」形では
> 扱いが変わりうる。**米国向けに売るなら、この線引きを先に確定させること。**
> グレーのまま販売を始めない。

### EU / UK

未調査。MiFID II の投資助言(investment advice)の定義に触れうるため、
販売先に含める前に個別に調査が必要。

---

## 6. 調査結果から導かれる現実的な優先順位

| 優先 | チャネル | 理由 |
|---|---|---|
| 1 | **MQL5 Market**(EA販売) | 手数料20%が最良。集客が内蔵。ただし技術制約あり |
| 2 | **MQL5 Signals** または **Darwinex** | 実運用の成績がそのまま収益になる。EA販売の実績づくりにもなる |
| 3 | GogoJungle | 日本語サポート・日本市場。手数料35%は重いが、日本語での信用が要る層に届く |
| 4 | Kindle | 単体の収益より、実績と信用の可視化。**AI×トレード一般論では埋もれる** |
| 5 | X | コストが安い(リンク無しなら月$2以下)。実績の継続的な可視化に向く |
| 6 | YouTube | 広告収益ではなく集客ファネルとして。AI完全自動化は収益化不可 |
| — | ブローカーIB | 利益相反の整理がつくまで保留 |

## 出典

- [Rules of Using the Market Service (MQL5)](https://www.mql5.com/en/market/rules)
- [How to publish a product on the Market (MQL5 Articles)](https://www.mql5.com/en/articles/385)
- [Rules for copy trading — the Trading Signals service (MQL5)](https://www.mql5.com/en/signals/rules)
- [How to become a signal provider and receive monthly fees (MetaTrader5)](https://www.metatrader5.com/en/signals/providers)
- [システムトレード（自動売買）手数料が35%なのは、なぜ？ (GogoJungle)](https://www.gogojungle.co.jp/post/1/20251)
- [EA出品手順と手数料等についての指定 (GogoJungle)](https://www.gogojungle.co.jp/en/post/1/14949)
- [【2026年最新】EA販売・配布サービス徹底比較 (Fマガ)](https://www.free-ea-fx.com/mql-ea-sale-best-services/)
- [Commodity Trading Advisor (CTA) Registration (NFA)](https://www.nfa.futures.org/registration-membership/who-has-to-register/cta.html)
- [Commodity Trading Advisor (CTA) FAQs (NFA)](https://www.nfa.futures.org/faqs/members/cta.html)
- [Forex Signal & Copy Trading Regulation and Licensing](https://www.signalmagician.com/copy-trading-regulation/)
- [電子書籍の価格設定ページ (Amazon KDP)](https://kdp.amazon.co.jp/ja_JP/help/topic/G200634500)
- [Kindle出版の印税70％と35％の違いとは？](https://eresa-publishing.co.jp/column/kindle-royalty-70-35-price-strategy/)
- [X (Twitter) API Pricing in 2026: All Tiers (Postproxy)](https://postproxy.dev/blog/x-api-pricing-2026/)
- [The X (Twitter) API in 2026: Pricing, Rate Limits & What Still Works](https://www.socialcrawl.dev/blog/x-twitter-api-2026)
- [YouTube Tightens Monetization Rules for AI-Generated Content (TechRepublic)](https://www.techrepublic.com/article/news-youtube-ai-video-monetization-rules/)
- [YouTube clarifies policies around AI slop (TechCrunch)](https://techcrunch.com/2026/07/20/youtube-clarifies-policies-around-ai-slop-and-upsetting-videos/)
- [The Complete Guide to Forex Introducing Broker (IB) Programs (2026)](https://track360.io/blog/forex-ib-guide)
- [How Forex Brokers Structure IB Rebate Programs That Scale](https://track360.io/blog/forex-ib-rebate-programs-guide)
- [Compare Darwinex vs. ZuluTrade in 2026](https://slashdot.org/software/comparison/Darwinex-vs-ZuluTrade/)
