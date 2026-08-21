# 店舗条件コレクタ

風俗ポータルの店舗一覧を巡回し、各店舗ページの**本文テキスト**から
「外国人OK」「キャンセル料無料」などの条件を判定して集計するツール。

## なぜ本文から判定するのか

ポータル側の絞り込み条件には限りがある。「外国人OK」は検索条件として
用意されているが、**「キャンセル料無料」は標準の条件に存在しない**。
そのため、条件を掛け合わせた店舗数はフィルタでは数えられず、
各店舗ページを読んで判定するしかない。

DOM構造ではなくテキストのパターン照合で判定するため、サイト改修に強く、
プロファイルを差し替えれば他ポータルにも使い回せる。

## 使い方

```bash
# 動作確認（同梱のローカルfixtureに対して実行）
python3 -m http.server 8899 --bind 127.0.0.1 &   # 別途fixtureを用意
python3 collect.py --profile profiles/example.yaml

# 実サイトに向ける
python3 collect.py --profile profiles/your_site.yaml \
    --out shops.csv --summary summary.json --delay 3.0

# 店舗URLの収集だけ先に確認する
python3 collect.py --profile profiles/your_site.yaml --list-only

# 少数で試す
python3 collect.py --profile profiles/your_site.yaml --limit 20
```

依存は標準ライブラリのみ（プロファイルをJSONで書けばPyYAMLも不要）。

## 主なオプション

| オプション | 意味 |
|---|---|
| `--profile` | 対象サイトのプロファイル (yaml/json) |
| `--out` | CSV出力先（既定 `shops.csv`） |
| `--summary` | 集計JSON出力先（既定 `summary.json`） |
| `--cache` | HTMLキャッシュ先（既定 `.cache`）。再実行時は再取得しない |
| `--limit` | 収集する店舗数の上限 |
| `--delay` | リクエスト間隔(秒)。プロファイルの値を上書き |
| `--list-only` | 店舗URLの収集のみ |
| `--force` | robots.txt が拒否していても続行 |

## 判定の仕組み

1. HTMLから `script` / `style` を除去し、タグを剥がして本文テキスト化
2. **NFKC正規化**（`外国人ＯＫ` と `外国人OK` を同一視）
3. プロファイルの `include` / `exclude` 語で照合

判定は3値。**`exclude` が `include` に優先する**（否定表現の方が確度が高いため）。

| 判定 | 意味 |
|---|---|
| `yes` | `include` に一致し、`exclude` に一致しない |
| `no` | `exclude` に一致 |
| `unknown` | どちらにも一致しない（=ページに記載がない） |

`unknown` を `no` に丸めないのが重要。「記載がない」と「不可と明記されている」は
別の情報で、営業リストとしての価値が変わる。

CSVには判定の根拠になった語（`*_evidence`）も出力するので、
誤判定があればプロファイルの語彙を調整する。

## プロファイルの書き方

`profiles/example.yaml` を参照。差し替えるのは3箇所。

```yaml
base_url: "https://example.com"
listing:
  url_template: "https://example.com/shop-list/page{page}/"  # {page}が連番に
  page_start: 1
  page_max: 50
  shop_link_pattern: 'href="(/shop/[^"]+)"'   # 店舗詳細リンクの正規表現
```

`rules` はサイトに依存しないので、そのまま使い回せる。

一覧ページから新規URLが0件のページが2回続くと、自動で巡回を打ち切る。
`page_max` は多めに設定しておいてよい。

## 運用上の注意

- **`delay` は実サイトでは 2.0 秒以上にする。** 相手サーバに負荷をかけない
- robots.txt を起動時に確認する。拒否されていれば停止する（`--force` で続行可）
- 対象サイトの利用規約を事前に確認すること
- キャッシュが効くので、判定ルールだけ調整して再実行する場合は再取得が走らない

## 制約

- 店舗ページに記載がない条件は判定できない（`unknown` になる）。
  キャンセル料は電話確認時にのみ案内する店が多く、`unknown` が多数を占める見込み
- JavaScriptで描画されるページは取得できない。その場合はヘッドレスブラウザが必要
