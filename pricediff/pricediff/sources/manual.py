"""watchlist に手入力された値からオファーを作るソース。

APIキーが1つも無くても表が完成するようにするための土台。API から取れた値が
あればそちらが優先され、手入力値は欠けている項目だけを埋める。
"""

from __future__ import annotations

from typing import Optional
from urllib.parse import quote

from ..models import AMAZON, RAKUTEN, TAOBAO, Offer, WatchItem

SEARCH_URL_TEMPLATES = {
    AMAZON: "https://www.amazon.co.jp/s?k={q}",
    RAKUTEN: "https://search.rakuten.co.jp/search/mall/{q}/",
    TAOBAO: "https://s.taobao.com/search?q={q}",
}


def search_url(market: str, keyword: Optional[str]) -> str:
    """直リンクが分からないときに開ける検索URL。手作業での確認用。"""
    template = SEARCH_URL_TEMPLATES.get(market)
    if not template or not keyword:
        return ""
    return template.format(q=quote(keyword))


def build_manual_offer(item: WatchItem, market: str) -> Optional[Offer]:
    if market == TAOBAO:
        if item.taobao_price_cny is None and not item.taobao_url:
            return None
        return Offer(
            market=TAOBAO,
            title=item.name,
            url=item.taobao_url or search_url(TAOBAO, item.name),
            price=item.taobao_price_cny,
            currency="CNY",
            weight_g=item.weight_g,
            source="manual",
        )
    if market == AMAZON:
        url = item.amazon_url or (
            f"https://www.amazon.co.jp/dp/{item.amazon_asin}" if item.amazon_asin else ""
        )
        note = None
        if not url:
            url = search_url(AMAZON, item.jp_keyword(AMAZON))
            note = "検索リンク(直リンク未取得)" if url else None
        if item.amazon_price_jpy is None and not url:
            return None
        return Offer(
            market=AMAZON,
            title=item.name,
            url=url,
            note=note,
            price=item.amazon_price_jpy,
            currency="JPY",
            weight_g=item.weight_g,
            rank=item.amazon_rank,
            rank_category="手入力" if item.amazon_rank else None,
            source="manual",
        )
    if market == RAKUTEN:
        url = item.rakuten_url or ""
        note = None
        if not url:
            url = search_url(RAKUTEN, item.jp_keyword(RAKUTEN))
            note = "検索リンク(直リンク未取得)" if url else None
        if item.rakuten_price_jpy is None and not url:
            return None
        return Offer(
            market=RAKUTEN,
            title=item.name,
            url=url,
            note=note,
            price=item.rakuten_price_jpy,
            currency="JPY",
            weight_g=item.weight_g,
            rank=item.rakuten_rank,
            rank_category="手入力" if item.rakuten_rank else None,
            source="manual",
        )
    return None


MERGEABLE_FIELDS = (
    "title",
    "url",
    "price",
    "weight_g",
    "rank",
    "rank_category",
    "shop",
    "image",
    "review_count",
    "review_average",
)


def merge_offers(primary: Optional[Offer], fallback: Optional[Offer]) -> Optional[Offer]:
    """primary(API)を優先し、欠けている項目だけ fallback(手入力)で埋める。"""
    if primary is None:
        return fallback
    if fallback is None:
        return primary
    filled: list[str] = []
    for field in MERGEABLE_FIELDS:
        if getattr(primary, field) in (None, "") and getattr(fallback, field) not in (None, ""):
            setattr(primary, field, getattr(fallback, field))
            filled.append(field)
    if filled:
        primary.source = "api+manual"
    return primary
