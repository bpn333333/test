# -*- coding: utf-8 -*-
"""東アジアの地図（生産体制スライド用）を描く

    python make_map.py                       # assets/eastasia_50m.geojson から描く
    python make_map.py countries-50m.json    # 元データから東アジア分を切り出し直してから描く

出力
    assets/map_eastasia.png   … 地図・国の塗り分け・流れの矢印（文字は入れない）
    assets/map_eastasia.json  … 拠点ピンと矢印ラベルの位置（スライド上のインチ）

文字は PPTX 側で載せる（游ゴシックを当て、あとから直せるようにするため）。
元データは Natural Earth 1:50m（world-atlas@2.0.2 の TopoJSON）。パブリックドメイン。
"""
import io
import json
import math
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Polygon
import matplotlib.patheffects as pe

HERE = os.path.dirname(os.path.abspath(__file__))
SUBSET = os.path.join(HERE, "assets", "eastasia_50m.geojson")
OUT_PNG = os.path.join(HERE, "assets", "map_eastasia.png")
OUT_JSON = os.path.join(HERE, "assets", "map_eastasia.json")

# スライド上の置き場所（インチ）。右側に拠点カードが来る
BOX = dict(x=0.65, y=1.50, w=7.45, h=5.30)

# 投影：経度に cos(25°) を掛けるだけの正距円筒。東アジアの縦横比が崩れない程度で十分
K = math.cos(math.radians(25))
LAT0, LAT1 = 7.0, 46.5
LON0 = 96.0
LON1 = LON0 + (LAT1 - LAT0) * (BOX["w"] / BOX["h"]) / K

VERM, ORANGE, TEAL, GOLD = "#B3121B", "#D9601A", "#1F6F63", "#C9962C"
SEA, LAND, EDGE = "#EEF1F3", "#DEDBD6", "#FFFFFF"
HILITE = {"Japan": (VERM, 0.88), "China": (ORANGE, 0.50), "Vietnam": (TEAL, 0.85)}

PINS = {  # 位置は国の代表点。都市を特定する意図はない
    "日本": dict(lon=139.7, lat=35.7, role="本社・受注・品質保証", color=VERM, side="ne"),
    "中国": dict(lon=115.5, lat=31.0, role="制作", color=ORANGE, side="w"),
    "ベトナム": dict(lon=105.8, lat=21.0, role="開発", color=TEAL, side="w"),
}
# 流れ：始点, 終点, 曲がり, ラベル, 色, ラベルを置く曲線上の t, ラベルのずらし(in: 右, 下)
# ラベルは線の上に載せず、曲線の外側に逃がす（線と文字が重ならないように）
FLOWS = [
    ("日本", "中国", 0.36, "①③ 制作を発注", VERM, 0.50, (0.00, -0.24)),
    ("中国", "日本", 0.36, "納品・品質保証", ORANGE, 0.50, (0.05, 0.24)),
    ("ベトナム", "日本", 0.42, "②③ ツール・PFを開発", TEAL, 0.45, (0.30, 0.22)),
    ("日本", (155.5, 30.0), 0.10, "② ツール外販 → 海外へ", GOLD, 1.00, (-0.78, 0.30)),
]


def proj(lon, lat):
    return ((lon - LON0) * K, lat)


def to_inch(X, Y):
    x = BOX["x"] + X / ((LON1 - LON0) * K) * BOX["w"]
    y = BOX["y"] + (LAT1 - Y) / (LAT1 - LAT0) * BOX["h"]
    return round(x, 3), round(y, 3)


def build_subset(topo_path):
    """TopoJSON を解いて、表示範囲にかかる国・リングだけを GeoJSON で保存する"""
    topo = json.load(io.open(topo_path, encoding="utf-8"))
    sx, sy = topo["transform"]["scale"]
    tx, ty = topo["transform"]["translate"]
    arcs = []
    for arc in topo["arcs"]:
        x = y = 0
        pts = []
        for dx, dy in arc:
            x += dx
            y += dy
            pts.append((x * sx + tx, y * sy + ty))
        arcs.append(pts)

    def ring(idx):
        out = []
        for i in idx:
            a = arcs[i] if i >= 0 else arcs[~i][::-1]
            out.extend(a if not out else a[1:])
        return out

    m = 6.0  # 余白（度）
    def hits(r):
        xs = [p[0] for p in r]
        ys = [p[1] for p in r]
        return max(xs) >= LON0 - m and min(xs) <= LON1 + m and max(ys) >= LAT0 - m and min(ys) <= LAT1 + m

    feats = []
    for g in topo["objects"]["countries"]["geometries"]:
        if g.get("type") not in ("Polygon", "MultiPolygon"):
            continue
        polys = [g["arcs"]] if g["type"] == "Polygon" else g["arcs"]
        keep = []
        for poly in polys:
            rings = [ring(r) for r in poly]
            if rings and hits(rings[0]):
                keep.append([[[round(x, 3), round(y, 3)] for x, y in r] for r in rings])
        if keep:
            feats.append({"type": "Feature", "properties": {"name": g["properties"]["name"]},
                          "geometry": {"type": "MultiPolygon", "coordinates": keep}})
    with io.open(SUBSET, "w", encoding="utf-8") as f:
        json.dump({"type": "FeatureCollection",
                   "note": "Natural Earth 1:50m (world-atlas@2.0.2) 東アジア切り出し。パブリックドメイン",
                   "features": feats}, f, ensure_ascii=False, separators=(",", ":"))
    print("切り出し:", len(feats), "か国 →", SUBSET, "(%d KB)" % (os.path.getsize(SUBSET) // 1024))


def curve_point(A, B, rad, t):
    """matplotlib の arc3 と同じ二次ベジェの t 位置"""
    (x1, y1), (x2, y2) = A, B
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    dx, dy = x2 - x1, y2 - y1
    cx, cy = mx + rad * dy, my - rad * dx
    u = 1 - t
    return (u * u * x1 + 2 * u * t * cx + t * t * x2, u * u * y1 + 2 * u * t * cy + t * t * y2)


def render():
    geo = json.load(io.open(SUBSET, encoding="utf-8"))
    fig = plt.figure(figsize=(BOX["w"], BOX["h"]), dpi=300)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, (LON1 - LON0) * K)
    ax.set_ylim(LAT0, LAT1)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.patch.set_facecolor(SEA)
    ax.set_facecolor(SEA)

    for ft in geo["features"]:
        name = ft["properties"]["name"]
        col, alpha = HILITE.get(name, (LAND, 1.0))
        for poly in ft["geometry"]["coordinates"]:
            outer = [proj(x, y) for x, y in poly[0]]
            ax.add_patch(Polygon(outer, closed=True, facecolor=col, alpha=alpha,
                                 edgecolor=EDGE, linewidth=0.5, zorder=2 if name in HILITE else 1))
            for hole in poly[1:]:
                ax.add_patch(Polygon([proj(x, y) for x, y in hole], closed=True,
                                     facecolor=SEA, edgecolor=EDGE, linewidth=0.4, zorder=3))

    pts = {k: proj(v["lon"], v["lat"]) for k, v in PINS.items()}
    flows = []
    for a, b, rad, label, col, t, (ox, oy) in FLOWS:
        A = pts[a]
        B = pts[b] if isinstance(b, str) else proj(*b)
        arr = FancyArrowPatch(A, B, connectionstyle="arc3,rad=%s" % rad, arrowstyle="-|>",
                              mutation_scale=15, linewidth=2.4, color=col,
                              shrinkA=11, shrinkB=11 if isinstance(b, str) else 0, zorder=5)
        arr.set_path_effects([pe.withStroke(linewidth=5.5, foreground="white")])
        ax.add_patch(arr)
        lx, ly = to_inch(*curve_point(A, B, rad, t))
        flows.append(dict(label=label, color=col.lstrip("#").upper(),
                          x=round(lx + ox, 3), y=round(ly + oy, 3), w=1.9))

    fig.savefig(OUT_PNG, dpi=300, facecolor=SEA)
    plt.close(fig)

    pins = []
    for name, v in PINS.items():
        x, y = to_inch(*pts[name])
        lw = 1.75 if name == "日本" else 1.30
        if v["side"] == "ne":
            lx, ly, align = x + 0.42, y - 0.62, "left"
        else:
            lx, ly, align = x - 0.18 - lw, y - 0.28, "right"
        pins.append(dict(name=name, role=v["role"], color=v["color"].lstrip("#").upper(),
                         x=x, y=y, lx=round(lx, 3), ly=round(ly, 3), lw=lw, align=align))
    with io.open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(dict(box=BOX, pins=pins, flows=flows), f, ensure_ascii=False, indent=1)
    print("地図:", OUT_PNG, "(%d KB)" % (os.path.getsize(OUT_PNG) // 1024))
    print("経度 %.1f〜%.1f ／ 緯度 %.0f〜%.0f" % (LON0, LON1, LAT0, LAT1))


if __name__ == "__main__":
    if len(sys.argv) > 1:
        build_subset(sys.argv[1])
    render()
