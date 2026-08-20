"""淘宝(タオバオ)からの取得。

淘宝開放平台(TOP API)の taobao.tbk.item.info.get を叩いて価格を取得する。
app_key / app_secret が未設定の場合は API を呼ばず、watchlist.csv に手入力した
価格(taobao_price_cny)をそのまま使う。

補足: 淘宝の商品ページを HTML スクレイピングする実装は入れていない。
利用規約で禁じられているうえ、ログイン・地域判定・ボット対策があり実務上も安定
しないため。API 権限が取れない場合は Chrome で価格を見て CSV に書く運用が前提。
"""

from __future__ import annotations

import datetime as dt
import hashlib
import logging
import re
from typing import Any, Optional
from urllib.parse import parse_qs, urlparse

from ..models import TAOBAO, Offer, WatchItem
from .base import first_number, now_iso
from .http import FetchError

log = logging.getLogger(__name__)

ITEM_ID_RE = re.compile(r"(?:^|[?&/=])id[=/](\d{6,})")


def extract_item_id(url: Optional[str]) -> Optional[str]:
    """淘宝/天猫の商品URLから数値の商品IDを取り出す。"""
    if not url:
        return None
    try:
        query = parse_qs(urlparse(url).query)
    except ValueError:
        return None
    for key in ("id", "itemId", "item_id"):
        values = query.get(key)
        if values and values[0].isdigit():
            return values[0]
    match = ITEM_ID_RE.search(url)
    if match:
        return match.group(1)
    digits = re.findall(r"\d{9,}", url)
    return digits[0] if digits else None


def sign_params(params: dict[str, Any], app_secret: str) -> str:
    """TOP API の署名(MD5): secret + 昇順に連結した key+value + secret を大文字16進で。"""
    concatenated = "".join(
        f"{key}{params[key]}" for key in sorted(params) if params[key] is not None
    )
    payload = f"{app_secret}{concatenated}{app_secret}"
    return hashlib.md5(payload.encode("utf-8")).hexdigest().upper()


class TaobaoSource:
    market = TAOBAO

    def __init__(self, config, client):
        self.config = config
        self.client = client
        self.app_key = config.get("taobao", "app_key")
        self.app_secret = config.get("taobao", "app_secret")
        self.endpoint = config.get("taobao", "endpoint", default="https://eco.taobao.com/router/rest")

    def available(self) -> bool:
        return self.config.has_taobao_api()

    def fetch(self, item: WatchItem) -> Optional[Offer]:
        item_id = extract_item_id(item.taobao_url)
        if not item_id:
            return None
        payload = self._call("taobao.tbk.item.info.get", {"num_iids": item_id})
        offer = self.parse(payload, fallback_url=item.taobao_url)
        return offer

    def _call(self, method: str, business_params: dict[str, Any]) -> dict:
        params: dict[str, Any] = {
            "method": method,
            "app_key": self.app_key,
            "sign_method": "md5",
            "format": "json",
            "v": "2.0",
            # TOP API のタイムスタンプは北京時間(UTC+8)
            "timestamp": (
                dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=8)
            ).strftime("%Y-%m-%d %H:%M:%S"),
            **business_params,
        }
        params["sign"] = sign_params(params, self.app_secret)
        payload = self.client.post_json(
            self.endpoint,
            data="&".join(f"{k}={v}" for k, v in params.items()),
            headers={"Content-Type": "application/x-www-form-urlencoded; charset=utf-8"},
            cache_key=f"taobao:{method}:{business_params}",
        )
        if isinstance(payload, dict) and "error_response" in payload:
            error = payload["error_response"]
            raise FetchError(
                f"淘宝API エラー {error.get('code')}: {error.get('sub_msg') or error.get('msg')}"
            )
        return payload

    @staticmethod
    def parse(payload: dict, fallback_url: Optional[str] = None) -> Optional[Offer]:
        response = (payload or {}).get("tbk_item_info_get_response") or {}
        results = (response.get("results") or {}).get("n_tbk_item") or []
        if not results:
            return None
        raw = results[0]
        # zk_final_price = 割引後価格。無ければ定価(reserve_price)
        price = first_number(raw.get("zk_final_price"), raw.get("reserve_price"))
        url = raw.get("item_url") or fallback_url or ""
        if url.startswith("//"):
            url = f"https:{url}"
        return Offer(
            market=TAOBAO,
            title=raw.get("title", ""),
            url=url,
            price=price,
            currency="CNY",
            shop=raw.get("nick"),
            image=raw.get("pict_url"),
            source="api",
            fetched_at=now_iso(),
            raw={"num_iid": raw.get("num_iid"), "volume": raw.get("volume")},
        )
