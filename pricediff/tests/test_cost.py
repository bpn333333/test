"""原価計算(為替・重量・手数料)のテスト。"""

import unittest

from pricediff.cost import calc_landed_cost, chargeable_weight_g
from pricediff.fx import FxRate


class ChargeableWeightTest(unittest.TestCase):
    def test_actual_weight_is_used(self):
        self.assertEqual(chargeable_weight_g(320), 320)

    def test_missing_weight_falls_back_to_default(self):
        self.assertEqual(chargeable_weight_g(None, default_weight_g=500), 500)
        self.assertEqual(chargeable_weight_g(0, default_weight_g=500), 500)

    def test_volumetric_weight_wins_when_bulky(self):
        # 30x20x20cm / 6000 = 2.0kg > 実重量 400g
        weight = chargeable_weight_g(400, dimensions_cm=(30, 20, 20), volumetric_divisor=6000)
        self.assertEqual(weight, 2000)

    def test_actual_weight_wins_when_dense(self):
        weight = chargeable_weight_g(3000, dimensions_cm=(10, 10, 10), volumetric_divisor=6000)
        self.assertEqual(weight, 3000)


class LandedCostTest(unittest.TestCase):
    def setUp(self):
        self.fx = FxRate(20.0, "test")
        self.cost_config = {
            "mode": "landed",
            "china_domestic_cny": 5.0,
            "agent_fee_pct": 10.0,
            "agent_fee_min_jpy": 100.0,
            "intl_shipping_jpy_per_kg": 1000.0,
            "intl_shipping_min_jpy": 150.0,
            "handling_jpy_per_item": 50.0,
            "volumetric_divisor": 6000.0,
            "import_tax_pct": 0.0,
            "default_weight_g": 500.0,
        }

    def test_breakdown(self):
        landed = calc_landed_cost(50.0, 400, self.fx, self.cost_config)
        self.assertEqual(landed.item_jpy, 1000.0)          # 50元 x 20
        self.assertEqual(landed.china_domestic_jpy, 100.0)  # 5元 x 20
        self.assertEqual(landed.agent_fee_jpy, 110.0)       # (1000+100) x 10%
        self.assertEqual(landed.intl_shipping_jpy, 450.0)   # 0.4kg x 1000 + 50
        self.assertEqual(landed.total, 1660.0)

    def test_agent_fee_uses_minimum_when_larger(self):
        landed = calc_landed_cost(5.0, 100, self.fx, self.cost_config)
        # (100+100) x 10% = 20円 < 最低100円 -> 100円が採用される
        self.assertEqual(landed.agent_fee_jpy, 100.0)

    def test_intl_shipping_has_floor(self):
        landed = calc_landed_cost(10.0, 20, self.fx, self.cost_config)
        # 0.02kg x 1000 = 20円 だが最低150円 + 固定50円
        self.assertEqual(landed.intl_shipping_jpy, 200.0)

    def test_import_tax_applies_to_goods_and_shipping(self):
        config = dict(self.cost_config, import_tax_pct=10.0)
        landed = calc_landed_cost(50.0, 400, self.fx, config)
        self.assertAlmostEqual(landed.import_tax_jpy, (1000 + 100 + 450) * 0.1)

    def test_returns_none_without_taobao_price(self):
        self.assertIsNone(calc_landed_cost(None, 400, self.fx, self.cost_config))

    def test_missing_weight_uses_default(self):
        landed = calc_landed_cost(50.0, None, self.fx, self.cost_config)
        self.assertEqual(landed.intl_shipping_jpy, 550.0)  # 0.5kg 既定


class ItemOnlyModeTest(unittest.TestCase):
    """既定の item モードは商品代だけを円換算する。"""

    def setUp(self):
        self.fx = FxRate(20.0, "test")
        self.landed_config = {
            "mode": "landed", "china_domestic_cny": 5.0, "agent_fee_pct": 10.0,
            "agent_fee_min_jpy": 100.0, "intl_shipping_jpy_per_kg": 1000.0,
            "intl_shipping_min_jpy": 150.0, "handling_jpy_per_item": 50.0,
            "import_tax_pct": 10.0, "default_weight_g": 500.0,
        }

    def test_item_mode_ignores_shipping_and_fees(self):
        config = dict(self.landed_config, mode="item")
        landed = calc_landed_cost(50.0, 400, self.fx, config)
        self.assertEqual(landed.item_jpy, 1000.0)
        self.assertEqual(landed.china_domestic_jpy, 0.0)
        self.assertEqual(landed.agent_fee_jpy, 0.0)
        self.assertEqual(landed.intl_shipping_jpy, 0.0)
        self.assertEqual(landed.import_tax_jpy, 0.0)
        self.assertEqual(landed.total, 1000.0)

    def test_item_is_the_default_mode(self):
        config = dict(self.landed_config)
        config.pop("mode")
        self.assertEqual(calc_landed_cost(50.0, 400, self.fx, config).total, 1000.0)

    def test_unknown_mode_falls_back_to_item(self):
        config = dict(self.landed_config, mode="なにか")
        self.assertEqual(calc_landed_cost(50.0, 400, self.fx, config).total, 1000.0)

    def test_weight_does_not_affect_item_mode(self):
        config = dict(self.landed_config, mode="item")
        light = calc_landed_cost(50.0, 10, self.fx, config).total
        heavy = calc_landed_cost(50.0, 5000, self.fx, config).total
        self.assertEqual(light, heavy)

    def test_item_mode_without_price(self):
        self.assertIsNone(calc_landed_cost(None, 400, self.fx, {"mode": "item"}))


class FxRateTest(unittest.TestCase):
    def test_buffer_is_applied(self):
        fx = FxRate(20.0, "test", buffer_pct=5.0)
        self.assertEqual(fx.rate, 21.0)
        self.assertEqual(fx.to_jpy(10), 210.0)

    def test_none_passes_through(self):
        self.assertIsNone(FxRate(20.0, "test").to_jpy(None))

    def test_describe_mentions_buffer(self):
        self.assertIn("バッファ", FxRate(20.0, "test", buffer_pct=2.0).describe())


if __name__ == "__main__":
    unittest.main()


class FxOverrideTest(unittest.TestCase):
    """--fx-rate で指定したレートには安全マージンを乗せない。"""

    def test_override_ignores_buffer(self):
        import copy

        from pricediff.config import Config, DEFAULTS
        from pricediff.fx import get_fx_rate

        config = Config(copy.deepcopy(DEFAULTS))
        fx = get_fx_rate(config, None, override=20.5)
        self.assertEqual(fx.rate, 20.5)
        self.assertEqual(fx.source, "指定値")

    def test_configured_rate_keeps_buffer(self):
        import copy

        from pricediff.config import Config, DEFAULTS
        from pricediff.fx import get_fx_rate

        config = Config(copy.deepcopy(DEFAULTS))
        fx = get_fx_rate(config, None)
        self.assertAlmostEqual(fx.rate, 21.0 * 1.02)
