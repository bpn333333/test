# pricediff — 淘宝 × Amazon.co.jp × 楽天市場 価格差ツール

淘宝(タオバオ)の仕入れ値と、日本側(Amazon.co.jp / 楽天市場)の販売価格を突き合わせて、
**商品名・商品リンク・価格差・重さ・Amazonランキング・楽天ランキング**を一覧にします。

既定では **淘宝の商品代を円換算して日本側の価格と比べます**。送料・代行手数料・税まで
積み上げた「日本着原価」で比べたくなったら `--cost landed` に切り替えます。

```
 #            商品名            商品代   Amazon    楽天    価格差    差率   重さ   Amazonランク 楽天ランク
--- -------------------------- -------- -------- -------- --------- ------ ------- ------------ ----------
  1 デスク収納ラック 木製         1,457    4,280    3,980    +2,823  +194%  1.25kg     45,100位       圏外
  2 トラベルポーチ 6点セット        621    2,980    2,680    +2,359  +380%    410g     22,400位       圏外
  3 ヨガマット 6mm 滑り止め       1,178    3,480    2,980    +2,302  +195%  1.05kg     12,800位       31位
  4 ステンレス保温タンブラー …      825    2,480    2,180    +1,655  +201%    320g      8,420位       14位
```

出力は **コンソール / CSV(Excel用BOM付き) / HTML(列クリックで並べ替え) / JSON** の4形式。

---

## 1. すぐ試す

```bash
git clone <このリポジトリ>
cd pricediff
pip install -r requirements.txt          # requests と PyYAML だけ

# APIキー無しでも、同梱サンプル(ダミー値)で動作確認できます
python -m pricediff run --demo

# ファイルにも書き出す
python -m pricediff run --demo -f console,csv,html -o out
```

インストールして使う場合:

```bash
pip install -e .
pricediff init          # config.yaml / watchlist.csv / .env.example の雛形を作る
pricediff doctor        # どのAPIが使える状態かを診断
pricediff run -w watchlist.csv -f console,csv,html
```

> `--demo` が読む `pricediff/templates/watchlist.csv` の数値と淘宝URLは**動作確認用のダミー**です。実データではありません。

---

## 2. データの取り方(3段階)

APIキーが揃っているほど自動になりますが、**1つも無くても表は完成します**。

| モール | 自動取得 | 取れるもの | 手に入れ方 |
|---|---|---|---|
| 楽天市場 | ◎ 簡単 | 価格・URL・ジャンル別ランキング | [楽天ウェブサービス](https://webservice.rakuten.co.jp/)でアプリID発行(無料・即日) |
| Amazon.co.jp | ○ 審査あり | 価格・**重量**・売れ筋ランキング・URL | PA-API 5.0(アソシエイト審査の通過が必要) |
| 淘宝 | △ 難しい | 価格・URL | 淘宝開放平台のアプリ登録。取れない場合は CSV に手入力 |

**現実的な運用**: まず楽天のアプリIDだけ取る(5分で終わる)。淘宝の価格と重さは商品ページを見て
CSV に書く。Amazon は PA-API が通るまで手入力 or ASIN だけ入れておく。
これで「日本側ランキングを見ながら仕入れ候補を絞る」という本来の目的は達成できます。

キーは `.env` に置きます(`git` には入りません):

```bash
cp .env.example .env
# RAKUTEN_APPLICATION_ID=xxxxxxxx を記入
```

### ブラウザで集めて貼る運用

API が取れないモールは、自分でブラウザを開いて見た数字を貼る形になります。
`pricediff add` が CSV行の貼り付けを受け取り、重複を弾いて watchlist.csv に追記します。

```bash
pricediff add -w watchlist.csv          # 貼り付けて Ctrl-D
pricediff add < rows.csv                # ファイルから
printf 'name,taobao_price_cny\n保温タンブラー,39.9\n' | pricediff add --update   # 価格だけ更新
```

同じ商品(商品名か淘宝URLが一致)は自動で飛ばします。`--update` は**貼り付けた列だけ**を
上書きするので、書かなかった列は残ります。ブラウザ側に投げるプロンプトの雛形と手順は
[docs/browser-workflow.md](docs/browser-workflow.md) にあります。

### 淘宝をスクレイピングしない理由

淘宝の商品ページを HTML 解析する実装は**意図的に入れていません**。利用規約で禁じられている上、
ログイン・地域判定・ボット対策があり、動いたとしてもすぐ壊れて数字を静かに間違えるためです。
API 権限が取れない間は、ブラウザで価格を見て CSV に書く運用が結局いちばん速く、正確です。

---

## 3. 追跡リスト(watchlist.csv)

1行1商品。**`name` と、淘宝側の価格(`taobao_price_cny`)があれば動きます**。
残りは埋まっているほど精度が上がります。日本語ヘッダ(`商品名` `淘宝価格` `重さ` など)でも読めます。

| 列 | 必須 | 説明 |
|---|---|---|
| `key` | | 行のID。空なら自動採番 |
| `name` | ✓ | 商品名。日本側の検索キーワードとしても使われる |
| `taobao_url` | | 淘宝/天猫の商品URL。API有効時はここからIDを取って価格を引く |
| `taobao_price_cny` | ✓ | 淘宝の価格(元)。API未設定ならこれが使われる |
| `weight_g` | | 実測重量(g)。**国際送料に直結するので最優先で埋める** |
| `amazon_asin` | | ASIN。あれば検索でなく直接引くので正確 |
| `amazon_keyword` / `rakuten_keyword` | | 検索語を商品名と変えたいとき |
| `rakuten_genre_id` | | 楽天のジャンルID。指定するとそのジャンルのランキングを見る |
| `amazon_price_jpy` / `rakuten_price_jpy` | | 手入力の日本側価格(APIの代わり) |
| `amazon_rank` / `rakuten_rank` | | 手入力のランキング |
| `note` | | 自由記入 |

API から取れた値が優先され、**手入力値は欠けている項目だけを埋めます**。
価格・リンクが両方無い場合は、確認用の検索URL(Amazon/楽天/淘宝の検索結果)が自動で入ります。

---

## 4. 価格差の計算

### 既定: `--cost item`(商品代だけ)

```
商品代 = 淘宝価格(元) × 為替
価格差 = 日本側の最高値(Amazon と楽天の高い方) − 商品代
差率   = 価格差 ÷ 商品代
```

重さは一覧に出ますが、計算には影響しません。

### 任意: `--cost landed`(日本に着くまでの費用を積み上げる)

```
日本着原価 = 商品代
           + 中国国内送料
           + 代行手数料(率と最低額の大きい方)
           + 国際送料(課金重量 × 円/kg + 固定費)
           + 輸入時の税

価格差 = 日本側の最高値 − 日本着原価
```

- **課金重量**は実重量と容積重量(縦×横×高さ÷6000)の重い方。かさばる商品の見落としを防ぎます
- 重量が取れない行は `default_weight_g`(既定500g)で計算し、`重さ取得元` に「既定値」と記録します
- 単価はすべて `config.yaml` で自分の代行業者の実績値に置き換えてください。**既定値は概算です**

どちらのモードでも、為替は `buffer_pct`(既定2%)だけ円安側に倒して計算します
(`--fx-rate` で明示指定したときはそのまま使います)。

> 価格差 = 利益ではありません。ここから国際送料・代行手数料・販売手数料
> (Amazon 8〜15%)・FBA配送料・広告費が引かれます。まず候補を絞るための道具です。

---

## 5. ランキングについて

- **Amazon**: PA-API の `WebsiteSalesRank`(売れ筋ランキング)。全体順位が無い場合はカテゴリ順位で代用
- **楽天**: 商品検索APIは順位を返さないため、ヒットした商品のジャンルIDで
  ランキングAPI(リアルタイム/日次/週次/月次)を引き、同じ商品コードがあればその順位を採用。
  無ければ「圏外」と表示します。`ranking_pages: 2` にすると60位まで拾えます

順位は**需要のあたりを付けるため**のものです。順位が良い＝売れる、ではなく、
「差額はあるが誰も買っていない商品」を弾くために見ます。

---

## 6. よく使うコマンド

```bash
pricediff run --sort ratio --top 20        # 差率の高い順に上位20件
pricediff run --min-diff 800               # 価格差800円未満を捨てる
pricediff run --max-rank 50000             # ランキング5万位以内だけ
pricediff run --fx-rate 20.5               # 為替を固定して試算
pricediff run --cost landed                # 送料・手数料・税まで積み上げて比較
pricediff run --offline                    # APIを一切呼ばない(手入力値のみ)
pricediff run --no-cache -v                # キャッシュを使わず詳細ログ
pricediff add --dry-run                    # 貼り付けた行を書き込まずに確認
```

API 応答は既定で6時間キャッシュされます(`~/.cache/pricediff`)。同じ日に何度回しても API は消費しません。

終了コード: `0` 正常 / `1` 価格差を1件も計算できなかった / `2` 入力エラー。cron で回すときの判定に使えます。

---

## 7. 開発

```bash
python -m unittest discover -s tests -t .    # 外部通信なし
```

```
pricediff/
├── cli.py          コマンド定義(run / init / doctor)
├── compare.py      比較エンジン。1商品ごとに3モールを引いて突き合わせる
├── cost.py         日本着原価の積み上げ(重量→国際送料)
├── fx.py           為替
├── models.py       Offer / WatchItem / ComparisonRow
├── report.py       コンソール(全角幅対応)/ CSV / JSON / HTML
├── watchlist.py    CSV・YAML の読み込み
├── templates/      init 用の雛形(config.yaml / watchlist.csv / env.example)
└── sources/
    ├── http.py     リトライ・レート制限・ディスクキャッシュ
    ├── rakuten.py  楽天ウェブサービス(検索 + ランキング)
    ├── amazon.py   PA-API 5.0(AWS SigV4署名)
    ├── taobao.py   淘宝開放平台(MD5署名)
    └── manual.py   CSV手入力値・APIとのマージ
```

1商品の取得に失敗しても全体は止まりません。失敗は行ごとの「警告」として出力に残ります。

### ネットワークについて

Claude Code のリモート環境(ネットワークポリシー `Trusted`)からは外部APIに接続できません。
実データで動かすときは手元の PC で実行するか、環境設定でネットワークを `Custom` にして
`app.rakuten.co.jp` / `webservices.amazon.co.jp` / `eco.taobao.com` / `api.frankfurter.app` を許可してください。
`--offline` はネットワークを一切使いません。
