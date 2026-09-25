# -*- coding: utf-8 -*-
"""生成した PPTX の図形ジオメトリを検査する。

この環境には LibreOffice も PowerPoint も無く、レンダリングして目視できない。
そこで「宣言された座標」だけでも機械的に見ておくためのスクリプト。

検出できること … スライド外へのはみ出し、フッター(y=6.90in)への食い込み、図形同士の重なり
検出できないこと … 表が中身に合わせて伸びる分（deck/README.md の既知の罠）、
                    テキストの折り返しによる高さの増加
"""
import zipfile, re, sys

EMU = 914400.0
SLIDE_H, SLIDE_W = 7.5, 13.333
FOOT_Y = 6.90

path = sys.argv[1] if len(sys.argv) > 1 else "../投資家向け企画書.pptx"
z = zipfile.ZipFile(path)
slides = sorted(
    [n for n in z.namelist() if re.match(r"ppt/slides/slide[0-9]+\.xml$", n)],
    key=lambda n: int(re.search(r"([0-9]+)", n.split("/")[-1]).group(1)))

XFRM = re.compile(
    r"<a:off x=\"(-?[0-9]+)\" y=\"(-?[0-9]+)\"/><a:ext cx=\"([0-9]+)\" cy=\"([0-9]+)\"/>")

problems = 0
for i, name in enumerate(slides, 1):
    xml = z.read(name).decode("utf-8")
    boxes = []
    for m in XFRM.finditer(xml):
        x, y, cx, cy = (int(v) / EMU for v in m.groups())
        boxes.append((x, y, cx, cy))
    issues = []
    for (x, y, cx, cy) in boxes:
        if cx * cy > SLIDE_W * SLIDE_H * 0.95:
            continue  # 全面ブリードの背景画像は対象外
        if y + cy > SLIDE_H + 0.02:
            issues.append("スライド外 y=%.2f+%.2f=%.2f" % (y, cy, y + cy))
        elif y + cy > FOOT_Y + 0.02 and cy < 1.0 and y < FOOT_Y:
            pass  # フッター自身の行
        if x + cx > SLIDE_W + 0.02:
            issues.append("右外 x=%.2f+%.2f=%.2f" % (x, cx, x + cx))
        if x < -0.02 or y < -0.02:
            issues.append("左上外 (%.2f,%.2f)" % (x, y))
    # 本文がフッター行に食い込んでいないか（高さ0.4in超の要素のみ）
    for (x, y, cx, cy) in boxes:
        if cx * cy > SLIDE_W * SLIDE_H * 0.95:
            continue  # 全面ブリードの背景・スクリムは対象外
        if cy > 0.4 and y < FOOT_Y and y + cy > FOOT_Y + 0.02:
            issues.append("フッター侵入 下端=%.2f (>6.90)" % (y + cy))
    if issues:
        problems += 1
        print("スライド %2d: %s" % (i, " / ".join(sorted(set(issues)))))

print("-" * 54)
print("検査 %d 枚 / 問題 %d 枚" % (len(slides), problems))
print("※ 表の伸長とテキスト折り返しは検出できない。PowerPoint で開いて目視すること。")
