# Web スクレイパー(画像保存 + テキスト収集)

指定したHP(Webページ)にアクセスして、

1. ページ内の**画像をダウンロードして保存**
2. **指定したテキスト**(CSSセレクタ / 正規表現 / キーワード)を収集

する Python 製のコマンドラインツールです。追加のブラウザ不要で動きます。

## セットアップ

```bash
pip install -r scraper/requirements.txt
```

Python 3.9 以降が必要です(標準ライブラリ + `requests` + `beautifulsoup4` のみ)。

## 使い方

いちばん簡単な例(画像を全部保存するだけ):

```bash
python3 scraper/scrape.py --url https://example.com --out ./output
```

テキストも一緒に集める例:

```bash
python3 scraper/scrape.py --url https://example.com --out ./output \
  --select "見出し=h1,h2" \
  --select "本文=article p" \
  --regex "[\w.+-]+@[\w-]+\.[\w.]+" \
  --contains "お問い合わせ"
```

複数ページをまとめて処理する例(`urls.txt` に1行1URL):

```bash
python3 scraper/scrape.py --url-file urls.txt --out ./output --delay 2
```

## 出力

```
output/
├── images/         ← 保存した画像(複数URL指定時はページごとのフォルダに分かれます)
├── results.json    ← 全結果(URL・タイトル・テキスト・画像一覧)
├── texts.csv       ← 収集したテキスト(Excelでそのまま開けるUTF-8 BOM付き)
└── images.csv      ← 画像URLと保存先の対応表
```

## 主なオプション

| オプション | 説明 |
| --- | --- |
| `--url URL` | 対象URL(複数指定可) |
| `--url-file FILE` | URLを1行ずつ書いたファイル |
| `--out DIR` | 出力先(既定: `./output`) |
| `--select "ラベル=セレクタ"` | CSSセレクタでテキストを収集(複数指定可)。`=` を省くとセレクタがそのままラベルになります |
| `--regex PATTERN` | ページ全文から正規表現で抜き出す(メール・電話番号・価格など) |
| `--contains 文字列` | その文字列を含む行を丸ごと収集 |
| `--no-images` | 画像を保存しない(テキストだけ集めたいとき) |
| `--ext jpg,png` | 保存する拡張子を限定 |
| `--min-bytes N` | N バイト未満の画像は無視(既定: 1024。アイコンやスペーサー除け) |
| `--max-images N` | 1ページあたりの保存上限(既定: 0=無制限) |
| `--delay 秒` / `--image-delay 秒` | アクセス間隔(既定: 1.0 / 0.2 秒) |
| `--ignore-robots` | robots.txt を無視(自分のサイトなど権限がある場合のみ) |
| `--quiet` | 進捗表示を出さない |

### CSSセレクタの書き方(よく使うもの)

| 目的 | 書き方 |
| --- | --- |
| 見出し | `--select "見出し=h1,h2,h3"` |
| 特定クラス | `--select "価格=.price"` |
| 特定ID配下 | `--select "本文=#main p"` |
| テーブルのセル | `--select "表=table td"` |
| 属性で絞る | `--select "商品名=div[itemprop='name']"` |

## 仕様メモ

- 画像は `img` の `src` / `srcset` / `data-src` などの遅延読み込み属性、`<source>`、`og:image`、
  `<link rel="icon">`、`style="background-image:url(...)"` から収集します。
- 相対URLは自動で絶対URLに変換します。`data:` URI は対象外です。
- 同じ内容の画像は SHA-1 で判定して重複保存しません。ファイル名は
  `元の名前_ハッシュ8桁.拡張子` で、上書き事故が起きません。
- 文字コードは自動判定します(日本語サイトの Shift_JIS / EUC-JP も可)。
- ネットワークエラーと 5xx は最大3回、2秒→4秒と待って再試行します。
- 既定で `robots.txt` を確認し、禁止されているURLはスキップします。

## 注意

- 取得先サイトの利用規約・著作権を確認してから使ってください。画像の再利用には権利者の許可が必要な場合があります。
- `--delay` を短くしすぎると相手サーバに負荷をかけます。既定値のままの利用を推奨します。
- JavaScript で描画されるページ(SPA・無限スクロールなど)は、HTMLに含まれない画像・テキストを取得できません。
  必要であれば Playwright 等でのレンダリング対応を追加できます。
