"""楽天市場(楽天ウェブサービス)からの取得。

- 商品検索API   : IchibaItem/Search/20220601   -> 価格・URL・ジャンルID
- ランキングAPI : IchibaItem/Ranking/20220601  -> ジャンル別の順位

楽天の商品検索APIは順位を返さないため、検索でヒットした商品のジャンルIDで
ランキングAPIを引き、同じ itemCode があればその順位を採用する
(ランキング圏外なら順位は None = 「圏外」表示)。
アプリID(無料)の取得: https://webservice.rakuten.co.jp/
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from ..models import RAKUTEN, Offer, WatchItem
from .base import first_number, now_iso
from .http import FetchError

log = logging.getLogger(__name__)

SEARCH_URL = "https://app.rakuten.co.jp/services/api/IchibaItem/Search/20220601"
RANKING_URL = "https://app.rakuten.co.jp/services/api/IchibaItem/Ranking/20220601"
RANKING_PERIODS = {"realtime", "daily", "weekly", "monthly"}


def _unwrap(entry: dict) -> dict:
    """API版によって Items の中身が {"Item": {...}} で包まれる場合に対応。"""
    return entry.get("Item", entry) if isinstance(entry, dict) else {}


class RakutenSource:
    market = RAKUTEN

    def __init__(self, config, client):
        self.config = config
        self.client = client
        self.app_id = config.get("rakuten", "application_id")
        self.affiliate_id = config.get("rakuten", "affiliate_id")
        self.hits = int(config.get("rakuten", "hits", default=5))
        period = str(config.get("rakuten", "ranking_period", default="realtime")).lower()
        self.period = period if period in RANKING_PERIODS else "realtime"
        self.ranking_pages = max(1, int(config.get("rakuten", "ranking_pages", default=1)))
        self._ranking_cache: dict[str, dict[str, int]] = {}

    def available(self) -> bool:
        return self.config.has_rakuten_api()

    # --- 取得 --------------------------------------------------------
    def fetch(self, item: WatchItem) -> Optional[Offer]:
        keyword = item.jp_keyword(RAKUTEN)
        if not keyword:
            return None

        params: dict[str, Any] = {
            "applicationId": self.app_id,
            "keyword": keyword,
            "hits": self.hits,
            "sort": "+itemPrice",
            "availability": 1,
            "format": "json",
            "formatVersion": 2,
        }
        if item.rakuten_genre_id:
            params["genreId"] = item.rakuten_genre_id
        if self.affiliate_id:
            params["affiliateId"] = self.affiliate_id

        payload = self.client.get_json(SEARCH_URL, params)
        offer = self.parse_search(payload)
        if offer is None:
            return None

        genre_id = item.rakuten_genre_id or offer.raw.get("genreId")
        if genre_id:
            try:
                rank_map = self.ranking_map(str(genre_id))
                item_code = offer.raw.get("itemCode")
                if item_code and item_code in rank_map:
                    offer.rank = rank_map[item_code]
                    offer.rank_category = f"ジャンル{genre_id}({self.period})"
                else:
                    offer.rank_category = f"ジャンル{genre_id}({self.period})・圏外"
            except FetchError as exc:
                log.warning("楽天ランキング取得に失敗 (genre=%s): %s", genre_id, exc)
                offer.note = "ランキング取得失敗"
        return offer

    def ranking_map(self, genre_id: str) -> dict[str, int]:
        """ジャンルIDごとの itemCode -> 順位。1ジャンル1回だけ取得してキャッシュ。"""
        if genre_id in self._ranking_cache:
            return self._ranking_cache[genre_id]

        rank_map: dict[str, int] = {}
        for page in range(1, self.ranking_pages + 1):
            params = {
                "applicationId": self.app_id,
                "genreId": genre_id,
                "period": self.period,
                "page": page,
                "format": "json",
                "formatVersion": 2,
            }
            if self.affiliate_id:
                params["affiliateId"] = self.affiliate_id
            payload = self.client.get_json(RANKING_URL, params)
            page_map = self.parse_ranking(payload)
            if not page_map:
                break
            rank_map.update(page_map)

        self._ranking_cache[genre_id] = rank_map
        return rank_map

    # --- パース(テストしやすいよう純関数として切り出す) --------------
    @staticmethod
    def parse_search(payload: dict) -> Optional[Offer]:
        items = (payload or {}).get("Items") or []
        if not items:
            return None
        raw = _unwrap(items[0])
        price = first_number(raw.get("itemPrice"))
        if price is None:
            return None
        return Offer(
            market=RAKUTEN,
            title=raw.get("itemName", ""),
            url=raw.get("itemUrl", ""),
            price=price,
            currency="JPY",
            shop=raw.get("shopName"),
            image=(raw.get("mediumImageUrls") or [None])[0]
            if isinstance(raw.get("mediumImageUrls"), list)
            else None,
            review_count=int(raw["reviewCount"]) if raw.get("reviewCount") is not None else None,
            review_average=first_number(raw.get("reviewAverage")),
            source="api",
            fetched_at=now_iso(),
            raw={
                "itemCode": raw.get("itemCode"),
                "genreId": raw.get("genreId"),
                "postageFlag": raw.get("postageFlag"),
            },
        )

    @staticmethod
    def parse_ranking(payload: dict) -> dict[str, int]:
        rank_map: dict[str, int] = {}
        for entry in (payload or {}).get("Items") or []:
            raw = _unwrap(entry)
            code, rank = raw.get("itemCode"), raw.get("rank")
            if code and rank:
                try:
                    rank_map[code] = int(rank)
                except (TypeError, ValueError):
                    continue
        return rank_map
