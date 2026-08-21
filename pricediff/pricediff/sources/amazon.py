"""Amazon.co.jp(Product Advertising API 5.0)からの取得。

取得するもの: 価格 / 商品重量 / 売れ筋ランキング(WebsiteSalesRank) / 商品URL。
PA-API はアソシエイト審査を通したアカウントが必要。未設定の場合、このソースは
自動的に無効化され、watchlist.csv に手入力した値があればそちらが使われる。

署名は AWS Signature V4(service=ProductAdvertisingAPI, region=us-west-2)。
"""

from __future__ import annotations

import datetime as dt
import hashlib
import hmac
import json
import logging
from typing import Any, Optional

from ..models import AMAZON, Offer, WatchItem
from .base import now_iso
from .http import FetchError

log = logging.getLogger(__name__)

SERVICE = "ProductAdvertisingAPI"
RESOURCES = [
    "ItemInfo.Title",
    "ItemInfo.ProductInfo",
    "ItemInfo.ExternalIds",
    "Offers.Listings.Price",
    "BrowseNodeInfo.WebsiteSalesRank",
    "Images.Primary.Medium",
]

# PA-API が返す重量単位 -> グラム換算
WEIGHT_UNITS_G = {
    "grams": 1.0,
    "gram": 1.0,
    "g": 1.0,
    "kilograms": 1000.0,
    "kilogram": 1000.0,
    "kg": 1000.0,
    "pounds": 453.59237,
    "pound": 453.59237,
    "lb": 453.59237,
    "lbs": 453.59237,
    "hundredthspounds": 4.5359237,
    "ounces": 28.349523125,
    "ounce": 28.349523125,
    "oz": 28.349523125,
    "hundredthsounces": 0.28349523125,
    "milligrams": 0.001,
}

# 長さ単位 -> センチ換算(容積重量の計算に使う)
LENGTH_UNITS_CM = {
    "inches": 2.54,
    "inch": 2.54,
    "hundredthsinches": 0.0254,
    "centimeters": 1.0,
    "centimeter": 1.0,
    "cm": 1.0,
    "millimeters": 0.1,
    "meters": 100.0,
    "feet": 30.48,
}


def _norm_unit(unit: Optional[str]) -> str:
    return "".join(ch for ch in (unit or "").lower() if ch.isalpha())


def to_grams(weight: Optional[dict]) -> Optional[float]:
    """PA-API の Weight オブジェクトをグラムに変換する。"""
    if not isinstance(weight, dict):
        return None
    value = weight.get("DisplayValue")
    factor = WEIGHT_UNITS_G.get(_norm_unit(weight.get("Unit")))
    if value is None or factor is None:
        return None
    try:
        return float(value) * factor
    except (TypeError, ValueError):
        return None


def to_cm(length: Optional[dict]) -> Optional[float]:
    if not isinstance(length, dict):
        return None
    value = length.get("DisplayValue")
    factor = LENGTH_UNITS_CM.get(_norm_unit(length.get("Unit")))
    if value is None or factor is None:
        return None
    try:
        return float(value) * factor
    except (TypeError, ValueError):
        return None


def _sign(key: bytes, message: str) -> bytes:
    return hmac.new(key, message.encode("utf-8"), hashlib.sha256).digest()


def sigv4_headers(
    *,
    access_key: str,
    secret_key: str,
    host: str,
    region: str,
    path: str,
    target: str,
    payload: str,
    timestamp: Optional[dt.datetime] = None,
) -> dict[str, str]:
    """PA-API 用の AWS SigV4 署名ヘッダを組み立てる。"""
    now = timestamp or dt.datetime.now(dt.timezone.utc)
    amz_date = now.strftime("%Y%m%dT%H%M%SZ")
    datestamp = now.strftime("%Y%m%d")

    headers = {
        "content-encoding": "amz-1.0",
        "content-type": "application/json; charset=utf-8",
        "host": host,
        "x-amz-date": amz_date,
        "x-amz-target": target,
    }
    signed_headers = ";".join(sorted(headers))
    canonical_headers = "".join(f"{k}:{headers[k]}\n" for k in sorted(headers))
    payload_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    canonical_request = "\n".join(
        ["POST", path, "", canonical_headers, signed_headers, payload_hash]
    )

    scope = f"{datestamp}/{region}/{SERVICE}/aws4_request"
    string_to_sign = "\n".join(
        [
            "AWS4-HMAC-SHA256",
            amz_date,
            scope,
            hashlib.sha256(canonical_request.encode("utf-8")).hexdigest(),
        ]
    )

    key = _sign(f"AWS4{secret_key}".encode("utf-8"), datestamp)
    key = _sign(key, region)
    key = _sign(key, SERVICE)
    key = _sign(key, "aws4_request")
    signature = hmac.new(key, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()

    headers["Authorization"] = (
        f"AWS4-HMAC-SHA256 Credential={access_key}/{scope}, "
        f"SignedHeaders={signed_headers}, Signature={signature}"
    )
    return headers


class AmazonSource:
    market = AMAZON

    def __init__(self, config, client):
        self.config = config
        self.client = client
        self.access_key = config.get("amazon", "access_key")
        self.secret_key = config.get("amazon", "secret_key")
        self.partner_tag = config.get("amazon", "partner_tag")
        self.host = config.get("amazon", "host", default="webservices.amazon.co.jp")
        self.region = config.get("amazon", "region", default="us-west-2")
        self.marketplace = config.get("amazon", "marketplace", default="www.amazon.co.jp")

    def available(self) -> bool:
        return self.config.has_amazon_api()

    def fetch(self, item: WatchItem) -> Optional[Offer]:
        if item.amazon_asin:
            payload = self._call(
                "GetItems",
                {
                    "ItemIds": [item.amazon_asin],
                    "ItemIdType": "ASIN",
                    "Condition": "New",
                },
            )
        else:
            keyword = item.jp_keyword(AMAZON)
            if not keyword:
                return None
            payload = self._call(
                "SearchItems",
                {
                    "Keywords": keyword,
                    "SearchIndex": "All",
                    "ItemCount": 3,
                    "SortBy": "Relevance",
                },
            )
        return self.parse(payload)

    def _call(self, operation: str, body: dict[str, Any]) -> dict:
        body = {
            **body,
            "PartnerTag": self.partner_tag,
            "PartnerType": "Associates",
            "Marketplace": self.marketplace,
            "Resources": RESOURCES,
        }
        path = f"/paapi5/{operation.lower()}"
        payload = json.dumps(body, ensure_ascii=False)
        headers = sigv4_headers(
            access_key=self.access_key,
            secret_key=self.secret_key,
            host=self.host,
            region=self.region,
            path=path,
            target=f"com.amazon.paapi5.v1.ProductAdvertisingAPIv1.{operation}",
            payload=payload,
        )
        try:
            return self.client.post_json(
                f"https://{self.host}{path}",
                data=payload.encode("utf-8"),
                headers=headers,
                cache_key=f"paapi:{operation}:{payload}",
            )
        except FetchError as exc:
            raise FetchError(f"Amazon PA-API ({operation}): {exc}") from exc

    # --- パース ------------------------------------------------------
    @staticmethod
    def parse(payload: dict) -> Optional[Offer]:
        result = (payload or {}).get("SearchResult") or (payload or {}).get("ItemsResult") or {}
        items = result.get("Items") or []
        if not items:
            return None
        raw = items[0]

        info = raw.get("ItemInfo") or {}
        title = ((info.get("Title") or {}).get("DisplayValue")) or ""

        listings = ((raw.get("Offers") or {}).get("Listings")) or []
        price = None
        if listings:
            amount = ((listings[0].get("Price") or {}).get("Amount"))
            if amount is not None:
                try:
                    price = float(amount)
                except (TypeError, ValueError):
                    price = None

        dimensions = ((info.get("ProductInfo") or {}).get("ItemDimensions")) or {}
        weight_g = to_grams(dimensions.get("Weight"))
        dims_cm = [
            to_cm(dimensions.get(k)) for k in ("Length", "Width", "Height")
        ]

        browse = raw.get("BrowseNodeInfo") or {}
        website_rank = (browse.get("WebsiteSalesRank") or {})
        rank = website_rank.get("SalesRank")
        rank_category = website_rank.get("DisplayName") or website_rank.get("ContextFreeName")
        if rank is None:
            # 全体順位が無い場合はブラウズノード単位の順位で代用する
            node_ranks = [
                (node.get("SalesRank"), node.get("DisplayName"))
                for node in (browse.get("BrowseNodes") or [])
                if node.get("SalesRank")
            ]
            if node_ranks:
                rank, rank_category = min(node_ranks, key=lambda x: x[0])
        try:
            rank = int(rank) if rank is not None else None
        except (TypeError, ValueError):
            rank = None

        return Offer(
            market=AMAZON,
            title=title,
            url=raw.get("DetailPageURL", ""),
            price=price,
            currency="JPY",
            weight_g=weight_g,
            rank=rank,
            rank_category=rank_category,
            image=(((raw.get("Images") or {}).get("Primary") or {}).get("Medium") or {}).get("URL"),
            source="api",
            fetched_at=now_iso(),
            note=None if price is not None else "価格取得不可(在庫切れ/出品なしの可能性)",
            raw={
                "asin": raw.get("ASIN"),
                "dimensions_cm": dims_cm if any(dims_cm) else None,
            },
        )
