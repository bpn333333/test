#!/usr/bin/env python3
"""pptxgenjs の出力を圧縮 + 日本語フォント(東アジア用)を注入して小さくする。

使い方:  python3 slim.py deck.pptx out.pptx

pptxgenjs は ZIP を無圧縮で書き、<a:latin> しか書かないため
  1) PowerPoint の CJK ランが Yu Gothic にならない
  2) ファイルが 6〜8 倍に膨らむ
という 2 つの問題が出る。両方をここで直す。
"""
import re, sys, zipfile

DROP = ("ppt/notesSlides/", "ppt/notesMasters/")
LATIN = re.compile(r'<a:latin typeface="Yu Gothic"( charset="0")?/>')
EA = '<a:ea typeface="Yu Gothic"/><a:cs typeface="Yu Gothic"/>'

src, dst = sys.argv[1], sys.argv[2]
zin = zipfile.ZipFile(src)
zout = zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED, compresslevel=9)

for name in [n for n in zin.namelist() if not n.startswith(DROP)]:
    data = zin.read(name)
    # ノートマスター/ノートスライドへの参照を落とす
    if name == "[Content_Types].xml":
        data = re.sub(r'<Override PartName="/ppt/notes(Slides|Masters)/[^"]*"[^/]*/>', '', data.decode()).encode()
    elif name == "ppt/_rels/presentation.xml.rels":
        data = re.sub(r'<Relationship[^>]*notesMaster[^>]*/>', '', data.decode()).encode()
    elif name == "ppt/presentation.xml":
        data = re.sub(r'<p:notesMasterIdLst>.*?</p:notesMasterIdLst>', '', data.decode(), flags=re.S).encode()
    elif name.startswith("ppt/slides/_rels/"):
        data = re.sub(r'<Relationship[^>]*notesSlide[^>]*/>', '', data.decode()).encode()
    # 東アジア用フォントを注入 + 空白を詰める
    if name.endswith(".xml"):
        t = data.decode()
        if '<a:latin typeface="Yu Gothic"' in t:
            t = LATIN.sub(lambda m: m.group(0) + EA, t)
        data = re.sub(r">\s+<", "><", t).encode()
    elif name.endswith(".rels"):
        data = re.sub(rb">\s+<", b"><", data)
    zout.writestr(name, data)

zin.close(); zout.close()
print(f"{src} -> {dst}")
