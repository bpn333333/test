"""淘宝の商品価格を、比較の基準になる仕入値(円)に換算する。

モードは2つ。

  item(既定) : 商品代金だけを円換算する
      仕入値 = 商品代金(元) x 為替

  landed     : 日本に着くまでの費用を積み上げる
      仕入値 = 商品代金(元→円)
             + 中国国内送料
             + 代行手数料(率 or 最低額の大きい方)
             + 国際送料(課金重量 x 単価 + 固定費)
             + 輸入時の税(概算)

landed は送料で利益が消える商品を弾きたいときに使う。重さは
どちらのモードでも一覧に表示される(landed のときだけ計算にも効く)。
"""

from __future__ import annotations

from typing import Optional

from .models import LandedCost


def chargeable_weight_g(
    weight_g: Optional[float],
    *,
    dimensions_cm: Optional[tuple[float, float, float]] = None,
    volumetric_divisor: float = 6000.0,
    default_weight_g: float = 500.0,
) -> float:
    """課金重量(g)。実重量と容積重量の重い方を採用する。"""
    actual = weight_g if weight_g and weight_g > 0 else default_weight_g
    if dimensions_cm and all(d and d > 0 for d in dimensions_cm) and volumetric_divisor > 0:
        w, d, h = dimensions_cm
        volumetric = (w * d * h) / volumetric_divisor * 1000  # kg -> g
        return max(actual, volumetric)
    return actual


ITEM_ONLY = "item"
LANDED = "landed"
MODES = (ITEM_ONLY, LANDED)


def calc_landed_cost(
    price_cny: Optional[float],
    weight_g: Optional[float],
    fx,
    cost_config: dict,
    *,
    dimensions_cm: Optional[tuple[float, float, float]] = None,
) -> Optional[LandedCost]:
    """仕入値の内訳を返す。淘宝価格が無ければ None。"""
    if price_cny is None:
        return None

    mode = str(cost_config.get("mode") or ITEM_ONLY).lower()
    if mode not in MODES:
        mode = ITEM_ONLY
    if mode == ITEM_ONLY:
        # 商品代金だけ。送料・手数料・税は乗せない
        return LandedCost(item_jpy=fx.to_jpy(price_cny) or 0.0)

    def cfg(key: str, default: float) -> float:
        value = cost_config.get(key, default)
        return float(default if value is None else value)

    item_jpy = fx.to_jpy(price_cny) or 0.0
    china_domestic_jpy = fx.to_jpy(cfg("china_domestic_cny", 0.0)) or 0.0

    goods_subtotal = item_jpy + china_domestic_jpy
    agent_fee = max(
        goods_subtotal * cfg("agent_fee_pct", 0.0) / 100,
        cfg("agent_fee_min_jpy", 0.0),
    )

    weight = chargeable_weight_g(
        weight_g,
        dimensions_cm=dimensions_cm,
        volumetric_divisor=cfg("volumetric_divisor", 6000.0),
        default_weight_g=cfg("default_weight_g", 500.0),
    )
    intl = max(
        weight / 1000 * cfg("intl_shipping_jpy_per_kg", 0.0),
        cfg("intl_shipping_min_jpy", 0.0),
    ) + cfg("handling_jpy_per_item", 0.0)

    taxable = goods_subtotal + intl
    import_tax = taxable * cfg("import_tax_pct", 0.0) / 100

    return LandedCost(
        item_jpy=item_jpy,
        china_domestic_jpy=china_domestic_jpy,
        agent_fee_jpy=agent_fee,
        intl_shipping_jpy=intl,
        import_tax_jpy=import_tax,
    )
