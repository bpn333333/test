"""比較エンジン: 追跡リストの各行について3モールを引き、価格差を計算する。"""

from __future__ import annotations

import logging
from typing import Callable, Optional

from .cost import calc_landed_cost
from .models import AMAZON, RAKUTEN, TAOBAO, ComparisonRow, Offer, WatchItem
from .sources.amazon import AmazonSource
from .sources.http import FetchError
from .sources.manual import build_manual_offer, merge_offers
from .sources.rakuten import RakutenSource
from .sources.taobao import TaobaoSource

log = logging.getLogger(__name__)

MARKETS = (TAOBAO, AMAZON, RAKUTEN)
SORT_KEYS = ("diff", "ratio", "rank", "price", "name")


def build_sources(config, client) -> dict[str, object]:
    """設定に応じて有効なAPIソースだけを返す。"""
    sources: dict[str, object] = {}
    for market, factory in (
        (TAOBAO, TaobaoSource),
        (AMAZON, AmazonSource),
        (RAKUTEN, RakutenSource),
    ):
        source = factory(config, client)
        if source.available():
            sources[market] = source
    return sources


def resolve_weight(item: WatchItem, offers: dict[str, Offer]) -> tuple[Optional[float], str]:
    """重量(g)を、信頼できる順に決める。"""
    if item.weight_g:
        return item.weight_g, "手入力"
    for market, label in ((AMAZON, "Amazon"), (TAOBAO, "淘宝"), (RAKUTEN, "楽天")):
        offer = offers.get(market)
        if offer and offer.weight_g:
            return offer.weight_g, label
    return None, "既定値"


def compare_item(
    item: WatchItem,
    config,
    fx,
    sources: dict[str, object],
) -> ComparisonRow:
    row = ComparisonRow(key=item.key, name=item.name, fx_rate=fx.rate)

    for market in MARKETS:
        api_offer: Optional[Offer] = None
        source = sources.get(market)
        if source is not None:
            try:
                api_offer = source.fetch(item)  # type: ignore[attr-defined]
            except FetchError as exc:
                row.errors.append(f"{market}: {exc}")
                log.warning("[%s] %s の取得に失敗: %s", market, item.name, exc)
            except Exception as exc:  # noqa: BLE001 - 1商品の失敗で全体を止めない
                row.errors.append(f"{market}: 予期しないエラー {exc}")
                log.exception("[%s] %s の取得中に例外", market, item.name)

        merged = merge_offers(api_offer, build_manual_offer(item, market))
        if merged is not None:
            row.offers[market] = merged

    row.weight_g, row.weight_source = resolve_weight(item, row.offers)

    taobao = row.offers.get(TAOBAO)
    dimensions = None
    amazon = row.offers.get(AMAZON)
    if amazon and amazon.raw.get("dimensions_cm"):
        dims = amazon.raw["dimensions_cm"]
        if dims and all(dims):
            dimensions = tuple(dims)

    row.landed = calc_landed_cost(
        taobao.price if taobao else None,
        row.weight_g,
        fx,
        config.section("cost"),
        dimensions_cm=dimensions,
    )

    if not taobao or taobao.price is None:
        row.errors.append("淘宝の価格が無いため価格差を計算できません")
    if not any(row.offers.get(m) and row.offers[m].price for m in (AMAZON, RAKUTEN)):
        row.errors.append("日本側の価格が取得できませんでした")

    return row


def compare_all(
    items: list[WatchItem],
    config,
    fx,
    sources: dict[str, object],
    *,
    progress: Optional[Callable[[int, int, WatchItem], None]] = None,
) -> list[ComparisonRow]:
    rows: list[ComparisonRow] = []
    total = len(items)
    for index, item in enumerate(items, start=1):
        if progress:
            progress(index, total, item)
        rows.append(compare_item(item, config, fx, sources))
    return rows


# --- 並べ替え・絞り込み ------------------------------------------------
def sort_rows(rows: list[ComparisonRow], key: str = "diff") -> list[ComparisonRow]:
    """価格差の大きい順(既定)。値が無い行は必ず末尾へ送る。"""
    if key == "name":
        return sorted(rows, key=lambda r: r.name)
    if key == "rank":
        return sorted(rows, key=lambda r: (r.best_rank is None, r.best_rank or 0))
    if key == "ratio":
        return sorted(rows, key=lambda r: (r.best_diff_ratio is None, -(r.best_diff_ratio or 0)))
    if key == "price":
        return sorted(rows, key=lambda r: (r.best_jp[1] is None, -(r.best_jp[1] or 0)))
    return sorted(rows, key=lambda r: (r.best_diff is None, -(r.best_diff or 0)))


def filter_rows(
    rows: list[ComparisonRow],
    *,
    min_diff_jpy: Optional[float] = None,
    max_rank: Optional[int] = None,
    top: Optional[int] = None,
) -> list[ComparisonRow]:
    result = rows
    if min_diff_jpy is not None:
        result = [r for r in result if (r.best_diff or float("-inf")) >= min_diff_jpy]
    if max_rank is not None:
        result = [r for r in result if r.best_rank is not None and r.best_rank <= max_rank]
    if top:
        result = result[:top]
    return result
