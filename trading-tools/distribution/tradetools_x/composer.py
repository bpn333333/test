"""X(旧Twitter)へ流す本文の組み立てと検査。

商品化・配信前提のため、ここは表現規制の関所も兼ねる。
 - 免責文を必ず付ける(付いていない本文は publish させない)
 - 断定的判断の提供にあたる表現を弾く(金商法38条2号の禁止行為)
 - 文字数は X の重み付けカウントで数える(日本語は1文字=2)

法的な最終判断は docs/COMPLIANCE.md を読んだうえで専門家に確認すること。
このモジュールは「明らかな地雷を機械的に止める」だけで、適法性を保証しない。
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional, Sequence

# X の文字数上限(重み付け後)
MAX_WEIGHTED_LENGTH = 280
# URL は実際の長さに関係なくこの文字数として数えられる
URL_WEIGHTED_LENGTH = 23
URL_PATTERN = re.compile(r"https?://\S+")

# 重み1(=半角相当)として扱うコードポイント範囲。X の公開設定に準拠
LIGHT_RANGES = ((0, 4351), (8192, 8205), (8208, 8223), (8242, 8247))

DEFAULT_DISCLAIMER = "※投資助言ではありません。売買の最終判断はご自身の責任でお願いします。"

# 使った時点で配信を止める表現。断定・利益保証・元本保証の類
PROHIBITED_PATTERNS = (
    r"必ず(儲|勝|上が|下が|利益)",
    r"絶対に?(儲|勝|上が|下が|安全|損しない)",
    r"確実に(儲|勝|利益|稼)",
    r"元本保証",
    r"損しません",
    r"必勝",
    r"100%",
    r"リスクはありません",
    r"稼げます",
)


def weighted_length(text: str) -> int:
    """X のカウント方式で文字数を数える。日本語は1文字=2、URLは一律23。"""
    remainder = URL_PATTERN.sub("", text)
    url_count = len(URL_PATTERN.findall(text))

    total = url_count * URL_WEIGHTED_LENGTH
    for char in remainder:
        code = ord(char)
        if any(low <= code <= high for low, high in LIGHT_RANGES):
            total += 1
        else:
            total += 2
    return total


def find_prohibited(text: str) -> List[str]:
    """禁止表現に当たる箇所を返す。空リストなら通過。"""
    hits: List[str] = []
    for pattern in PROHIBITED_PATTERNS:
        match = re.search(pattern, text)
        if match:
            hits.append(match.group(0))
    return hits


@dataclass
class Post:
    text: str
    signal_id: str

    def validate(self, disclaimer: str = DEFAULT_DISCLAIMER) -> None:
        """配信前の最終検査。1つでも引っかかれば例外にして止める。"""
        if disclaimer and disclaimer not in self.text:
            raise ValueError("免責文が含まれていません")

        hits = find_prohibited(self.text)
        if hits:
            raise ValueError(f"禁止表現が含まれています: {', '.join(hits)}")

        length = weighted_length(self.text)
        if length > MAX_WEIGHTED_LENGTH:
            raise ValueError(f"文字数超過: {length} / {MAX_WEIGHTED_LENGTH}")
        if not self.text.strip():
            raise ValueError("本文が空です")


def _format_symbol(symbol: str) -> str:
    """USDJPY → USD/JPY。6文字の通貨ペアだけ整形する。"""
    if len(symbol) == 6 and symbol.isalpha():
        return f"{symbol[:3].upper()}/{symbol[3:].upper()}"
    return symbol


def _format_timeframe(timeframe: str) -> str:
    table = {
        "PERIOD_M5": "5分足", "PERIOD_M15": "15分足", "PERIOD_M30": "30分足",
        "PERIOD_H1": "1時間足", "PERIOD_H4": "4時間足", "PERIOD_D1": "日足",
    }
    return table.get(timeframe, timeframe)


def _decimals(symbol: str) -> int:
    """円絡みは3桁、それ以外は5桁で表示する。"""
    return 3 if "JPY" in symbol.upper() else 5


def compose_signal_post(signal, hashtags: Sequence[str] = ("#FX",),
                        disclaimer: str = DEFAULT_DISCLAIMER,
                        show_levels: bool = True) -> Post:
    """シグナル1件を投稿本文にする。

    show_levels=False にすると損切り・利確を伏せる。無料配信で結論だけ出したくない
    場合や、有料会員向けとの差をつけたい場合に使う。
    """
    digits = _decimals(signal.symbol)
    pair = _format_symbol(signal.symbol)
    timeframe = _format_timeframe(signal.timeframe)
    arrow = "▲買い" if signal.direction == "BUY" else "▼売り"

    lines = [
        f"【{pair} {timeframe}】{arrow}シグナル",
        f"検出: {signal.time:%m/%d %H:%M}(サーバー時間)",
        f"価格 {signal.price:.{digits}f}",
    ]
    if show_levels:
        lines.append(
            f"損切 {signal.sl:.{digits}f} / 利確 {signal.tp:.{digits}f}"
            f"(RR {signal.risk_reward:.1f})"
        )
    lines.append(f"根拠: {signal.reason}")
    lines.append("")
    lines.append(disclaimer)

    tags = " ".join(hashtags)
    if tags:
        lines.append(tags)

    text = "\n".join(lines)
    post = Post(text=text, signal_id=signal.signal_id)

    # 長すぎる場合は根拠行を削って収める(免責と価格は絶対に落とさない)
    if weighted_length(text) > MAX_WEIGHTED_LENGTH:
        lines = [line for line in lines if not line.startswith("根拠:")]
        post = Post(text="\n".join(lines), signal_id=signal.signal_id)

    post.validate(disclaimer)
    return post


def compose_daily_summary(signals: Sequence, date_label: str,
                          disclaimer: str = DEFAULT_DISCLAIMER,
                          hashtags: Sequence[str] = ("#FX",)) -> Optional[Post]:
    """その日の検出件数まとめ。件数と内訳だけで、損益は書かない。

    損益実績を書くなら docs/COMPLIANCE.md の記録要件を満たしてからにすること
    (検証可能な記録なしの成績表示は景表法上のリスクが高い)。
    """
    if not signals:
        return None

    buys = sum(1 for s in signals if s.direction == "BUY")
    sells = sum(1 for s in signals if s.direction == "SELL")
    pairs = sorted({_format_symbol(s.symbol) for s in signals})

    lines = [
        f"【{date_label} シグナル検出まとめ】",
        f"検出 {len(signals)}件(買い {buys} / 売り {sells})",
        f"対象: {', '.join(pairs)}",
        "",
        disclaimer,
    ]
    tags = " ".join(hashtags)
    if tags:
        lines.append(tags)

    post = Post(text="\n".join(lines), signal_id=f"summary-{date_label}")
    post.validate(disclaimer)
    return post
