# deck — スライドのジェネレータ

PowerPoint を手で作らず、**コードから生成**しています。数字が変わったときに
「デッキのどこを直し忘れたか」が起きないようにするためです。

## ファイル

| ファイル | 出力 | 中身 |
|---|---|---|
| `build.js` | `投資家向け企画書 Ver0.8.pptx` | **投資家向けデッキ 28枚**（本体） |
| `extra.js` | `市場規模と制作費の構造.pptx` | 補足 2枚（市場規模／制作費とAI） |
| `av.js` | `市場規模と制作費の構造_AV含む版.pptx` | 上の 3枚版（AVの行と解説を追加） |
| `slim.py` | — | **必ず通す後処理**（下記） |
| `check_layout.py` | — | PPTX の EMU 座標を読んで**枠外・フッター侵食**を検出（表の伸長と折り返しは検出不可） |
| `shot.mjs` | `p*.png` | `investor_deck.html` のスライドを Playwright で撮る |

## 手順

```bash
cd deck
npm install                      # pptxgenjs
node build.js                    # -> deck.pptx
python3 slim.py deck.pptx "../投資家向け企画書 Ver0.8.pptx"
python3 check_layout.py "../投資家向け企画書 Ver0.8.pptx"   # 枠外・フッター侵食を検出

# レンダリング確認（レイアウト崩れは目で見ないと分からない）
soffice --headless --convert-to pdf ../投資家向け企画書.pptx --outdir .
pdftoppm -jpeg -r 85 投資家向け企画書.pdf slide
# slide-01.jpg … を1枚ずつ確認する
```

## ⚠️ slim.py を飛ばさないこと

pptxgenjs の出力には 2つ問題があり、`slim.py` がその両方を直しています。

1. **ZIP を無圧縮で書く。** 198KB → 19KB。**10分の1**になります。
2. **`<a:latin>` しか書かない。** PowerPoint は日本語（CJK）ランに
   *東アジア用フォント* を使うため、`<a:ea>` が無いと游ゴシックになりません。
   `slim.py` が `<a:ea>` と `<a:cs>` を注入します。

## ⚠️ 日本語フォントの罠

この環境には日本語フォントが入っていません。入れずに PDF 化すると、
**中国語フォント（文泉驛）で代替描画され、字形がおかしくなります。**

```bash
apt-get install -y fonts-noto-cjk
mkdir -p ~/.config/fontconfig && cat > ~/.config/fontconfig/fonts.conf <<'XML'
<?xml version="1.0"?><!DOCTYPE fontconfig SYSTEM "fonts.dtd"><fontconfig>
  <match target="pattern"><test name="family"><string>Yu Gothic</string></test>
    <edit name="family" mode="assign" binding="strong"><string>Noto Sans CJK JP</string></edit></match>
  <alias><family>sans-serif</family><prefer><family>Noto Sans CJK JP</family></prefer></alias>
</fontconfig>
XML
fc-cache -f
```

PPTX 側のフォント指定は **`Yu Gothic`**（Windows/Office 標準）のままにして、
この環境でだけ Noto Sans CJK JP に読み替えます。

## レイアウトの作法（ハマったところ）

- キャンバスは **13.333 × 7.5 インチ**（`LAYOUT_WIDE`）。左右マージン `M=0.65`、本文幅 `W=12.03`。
- **表の高さは `rowH` 通りにならない。** LibreOffice / PowerPoint が中身に合わせて伸ばすので、
  表の下に置いた要素と重なる。**セル内で折り返す長文を作らない**のが唯一の回避策。
- `stat()` は `note` を渡すなら高さ 1.5 以上。足りないとラベルと注記が重なる。
- フッターは `y=6.90`。本文は **6.6 より下に置かない**。
- 図はすべて **ネイティブ図形**（`p.ShapeType.*`）。画像にしないので PowerPoint 上で編集できる。

## HTML 版デッキとの関係

`../investor_deck.html` は**別実装**です。`build.js` とは**自動では同期しません。**
数字を変えたら **両方** 直す必要があります（現状、5枚の図は PPTX 側にしかありません）。

HTML 版の確認:
```bash
node shot.mjs     # deck.html を同じ階層に置いて実行
```
Playwright のブラウザは `/opt/pw-browsers/chromium-1194/chrome-linux/chrome` を
`executablePath` で明示指定すること（バージョン不一致で落ちるため）。
