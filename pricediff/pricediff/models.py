"""データモデル定義。

各モールから取得したオファー(Offer)と、それを1商品にまとめた
比較結果(ComparisonRow)の2階層で持つ。
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from typing import Any, Optional

TAOBAO = "taobao"
AMAZON = "amazon"
RAKUTEN = "rakuten"

MARKET_LABELS = {
    TAOBAO: "淘宝",
    AMAZON: "Amazon",
    RAKUTEN: "楽天",
}


@dataclass
class Offer:
    """1モール・1商品の取得結果。"""

    market: str
    title: str
    url: str
    price: Optional[float] = None
    currency: str = "JPY"
    weight_g: Optional[float] = None
    rank: Optional[int] = None
    rank_category: Optional[str] = None
    shop: Optional[str] = None
    image: Optional[str] = None
    review_count: Optional[int] = None
    review_average: Optional[float] = None
    source: str = "manual"  # api / manual / cache
    fetched_at: Optional[str] = None
    note: Optional[str] = None
    raw: dict[str, Any] = field(default_factory=dict, repr=False)

    @property
    def market_label(self) -> str:
        return MARKET_LABELS.get(self.market, self.market)

    def to_dict(self, include_raw: bool = False) -> dict[str, Any]:
        d = dataclasses.asdict(self)
        if not include_raw:
            d.pop("raw", None)
        return d


@dataclass
class WatchItem:
    """watchlist.csv の1行。追跡したい商品1件の定義。"""

    key: str
    name: str
    taobao_url: Optional[str] = None
    taobao_price_cny: Optional[float] = None
    weight_g: Optional[float] = None
    amazon_asin: Optional[str] = None
    amazon_keyword: Optional[str] = None
    rakuten_keyword: Optional[str] = None
    rakuten_genre_id: Optional[str] = None
    note: Optional[str] = None
    # 以下は任意。API未設定でも手入力だけで表を作れるようにするための欄
    amazon_price_jpy: Optional[float] = None
    amazon_url: Optional[str] = None
    amazon_rank: Optional[int] = None
    rakuten_price_jpy: Optional[float] = None
    rakuten_url: Optional[str] = None
    rakuten_rank: Optional[int] = None

    def jp_keyword(self, market: str) -> Optional[str]:
        if market == AMAZON:
            return self.amazon_keyword or self.name
        if market == RAKUTEN:
            return self.rakuten_keyword or self.name
        return self.name


@dataclass
class LandedCost:
    """淘宝価格を日本着の原価に積み上げた内訳(すべて円)。"""

    item_jpy: float = 0.0
    china_domestic_jpy: float = 0.0
    agent_fee_jpy: float = 0.0
    intl_shipping_jpy: float = 0.0
    import_tax_jpy: float = 0.0

    @property
    def total(self) -> float:
        return (
            self.item_jpy
            + self.china_domestic_jpy
            + self.agent_fee_jpy
            + self.intl_shipping_jpy
            + self.import_tax_jpy
        )

    def to_dict(self) -> dict[str, float]:
        d = dataclasses.asdict(self)
        d["total_jpy"] = round(self.total, 1)
        return {k: round(v, 1) for k, v in d.items()}


@dataclass
class ComparisonRow:
    """1商品ぶんの比較結果。出力テーブルの1行に対応する。"""

    key: str
    name: str
    offers: dict[str, Offer] = field(default_factory=dict)
    weight_g: Optional[float] = None
    weight_source: Optional[str] = None
    landed: Optional[LandedCost] = None
    fx_rate: Optional[float] = None
    errors: list[str] = field(default_factory=list)

    # --- 便利アクセサ ------------------------------------------------
    @property
    def taobao(self) -> Optional[Offer]:
        return self.offers.get(TAOBAO)

    @property
    def amazon(self) -> Optional[Offer]:
        return self.offers.get(AMAZON)

    @property
    def rakuten(self) -> Optional[Offer]:
        return self.offers.get(RAKUTEN)

    @property
    def cost_jpy(self) -> Optional[float]:
        return self.landed.total if self.landed else None

    @property
    def amazon_price(self) -> Optional[float]:
        return self.amazon.price if self.amazon else None

    @property
    def rakuten_price(self) -> Optional[float]:
        return self.rakuten.price if self.rakuten else None

    @property
    def amazon_rank(self) -> Optional[int]:
        return self.amazon.rank if self.amazon else None

    @property
    def rakuten_rank(self) -> Optional[int]:
        return self.rakuten.rank if self.rakuten else None

    def jp_price(self, market: str) -> Optional[float]:
        offer = self.offers.get(market)
        return offer.price if offer else None

    @property
    def best_jp(self) -> tuple[Optional[str], Optional[float]]:
        """日本側で最も高く売れているモールと価格(=売値の基準)。"""
        candidates = [
            (m, self.jp_price(m)) for m in (AMAZON, RAKUTEN) if self.jp_price(m)
        ]
        if not candidates:
            return None, None
        market, price = max(candidates, key=lambda x: x[1])
        return market, price

    def diff(self, market: str) -> Optional[float]:
        """そのモールの売値 - 日本着原価(円)。"""
        price = self.jp_price(market)
        if price is None or self.cost_jpy is None:
            return None
        return price - self.cost_jpy

    def diff_ratio(self, market: str) -> Optional[float]:
        """原価に対する価格差の倍率(0.5 = 50%上乗せで売れている)。"""
        d = self.diff(market)
        if d is None or not self.cost_jpy:
            return None
        return d / self.cost_jpy

    @property
    def best_diff(self) -> Optional[float]:
        market, _ = self.best_jp
        return self.diff(market) if market else None

    @property
    def best_diff_ratio(self) -> Optional[float]:
        market, _ = self.best_jp
        return self.diff_ratio(market) if market else None

    @property
    def best_rank(self) -> Optional[int]:
        """AmazonとRakutenのうち良い(小さい)方のランク。並べ替え用。"""
        ranks = [r for r in (self.amazon_rank, self.rakuten_rank) if r]
        return min(ranks) if ranks else None
