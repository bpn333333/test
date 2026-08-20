"""比較エンジン(価格差計算・並べ替え・絞り込み・失敗時の扱い)のテスト。"""

import unittest

from pricediff.compare import build_sources, compare_item, filter_rows, resolve_weight, sort_rows
from pricediff.config import Config, DEFAULTS
from pricediff.fx import FxRate
from pricediff.models import AMAZON, RAKUTEN, TAOBAO, ComparisonRow, LandedCost, Offer, WatchItem
from pricediff.sources.http import FetchError

import copy


def make_config(**overrides):
    data = copy.deepcopy(DEFAULTS)
    for section, values in overrides.items():
        data[section].update(values)
    return Config(data)


FX = FxRate(20.0, "test")

COST = {
    "mode": "landed",
    "china_domestic_cny": 0.0,
    "agent_fee_pct": 0.0,
    "agent_fee_min_jpy": 0.0,
    "intl_shipping_jpy_per_kg": 1000.0,
    "intl_shipping_min_jpy": 0.0,
    "handling_jpy_per_item": 0.0,
    "volumetric_divisor": 6000.0,
    "import_tax_pct": 0.0,
    "default_weight_g": 500.0,
}


class StubSource:
    """テスト用の擬似APIソース。"""

    def __init__(self, market, offer=None, error=None):
        self.market = market
        self.offer = offer
        self.error = error
        self.calls = 0

    def available(self):
        return True

    def fetch(self, item):
        self.calls += 1
        if self.error:
            raise self.error
        return self.offer


class CompareItemTest(unittest.TestCase):
    def setUp(self):
        self.config = make_config(cost=COST)

    def test_manual_only_computes_diff(self):
        item = WatchItem(key="k", name="商品", taobao_price_cny=50, weight_g=400,
                         amazon_price_jpy=2480, rakuten_price_jpy=2180, amazon_rank=8420)
        row = compare_item(item, self.config, FX, {})
        self.assertEqual(row.cost_jpy, 1400.0)      # 50元x20 + 0.4kg x1000
        self.assertEqual(row.best_jp[0], AMAZON)     # 高く売れている方を基準にする
        self.assertEqual(row.best_diff, 1080.0)
        self.assertAlmostEqual(row.diff_ratio(AMAZON), 1080 / 1400)
        self.assertEqual(row.diff(RAKUTEN), 780.0)
        self.assertEqual(row.amazon_rank, 8420)
        self.assertEqual(row.errors, [])

    def test_api_offer_overrides_manual_price(self):
        api_offer = Offer(market=AMAZON, title="API名", url="https://api", price=3000,
                          rank=100, source="api")
        item = WatchItem(key="k", name="商品", taobao_price_cny=50, weight_g=400,
                         amazon_price_jpy=2480)
        row = compare_item(item, self.config, FX, {AMAZON: StubSource(AMAZON, api_offer)})
        self.assertEqual(row.amazon_price, 3000)
        self.assertEqual(row.amazon_rank, 100)

    def test_api_failure_is_recorded_and_manual_used(self):
        item = WatchItem(key="k", name="商品", taobao_price_cny=50, weight_g=400,
                         amazon_price_jpy=2480)
        row = compare_item(item, self.config, FX,
                           {AMAZON: StubSource(AMAZON, error=FetchError("429 too many"))})
        self.assertEqual(row.amazon_price, 2480)     # 手入力値で継続できる
        self.assertTrue(any("429" in e for e in row.errors))

    def test_unexpected_exception_does_not_abort(self):
        item = WatchItem(key="k", name="商品", taobao_price_cny=50, amazon_price_jpy=1000)
        row = compare_item(item, self.config, FX,
                           {AMAZON: StubSource(AMAZON, error=RuntimeError("boom"))})
        self.assertTrue(any("予期しないエラー" in e for e in row.errors))
        self.assertEqual(row.amazon_price, 1000)

    def test_missing_taobao_price_records_error(self):
        item = WatchItem(key="k", name="商品", amazon_price_jpy=2480)
        row = compare_item(item, self.config, FX, {})
        self.assertIsNone(row.cost_jpy)
        self.assertIsNone(row.best_diff)
        self.assertTrue(any("淘宝" in e for e in row.errors))

    def test_missing_jp_price_records_error(self):
        item = WatchItem(key="k", name="商品", taobao_price_cny=50)
        row = compare_item(item, self.config, FX, {})
        self.assertTrue(any("日本側" in e for e in row.errors))

    def test_default_weight_applied_when_unknown(self):
        item = WatchItem(key="k", name="商品", taobao_price_cny=50, amazon_price_jpy=2480)
        row = compare_item(item, self.config, FX, {})
        self.assertIsNone(row.weight_g)
        self.assertEqual(row.weight_source, "既定値")
        self.assertEqual(row.cost_jpy, 1500.0)       # 既定500g ぶんの送料が乗る

    def test_negative_diff_is_kept(self):
        item = WatchItem(key="k", name="赤字商品", taobao_price_cny=200, weight_g=100,
                         amazon_price_jpy=2000)
        row = compare_item(item, self.config, FX, {})
        self.assertLess(row.best_diff, 0)


class ResolveWeightTest(unittest.TestCase):
    def test_manual_wins(self):
        item = WatchItem(key="k", name="商品", weight_g=250)
        offers = {AMAZON: Offer(market=AMAZON, title="t", url="u", weight_g=999)}
        self.assertEqual(resolve_weight(item, offers), (250, "手入力"))

    def test_amazon_is_preferred_over_taobao(self):
        item = WatchItem(key="k", name="商品")
        offers = {
            AMAZON: Offer(market=AMAZON, title="t", url="u", weight_g=300),
            TAOBAO: Offer(market=TAOBAO, title="t", url="u", weight_g=500),
        }
        self.assertEqual(resolve_weight(item, offers), (300, "Amazon"))

    def test_falls_back_to_default_label(self):
        self.assertEqual(resolve_weight(WatchItem(key="k", name="商品"), {}), (None, "既定値"))


def row_with(diff, rank=None, name="商品", cost=1000):
    """原価 cost・価格差 diff・指定順位を持つ行を組み立てる。"""
    row = ComparisonRow(key=name, name=name)
    row.offers[AMAZON] = Offer(market=AMAZON, title=name, url="u", price=cost + diff, rank=rank)
    row.landed = LandedCost(item_jpy=cost)
    return row


class SortFilterTest(unittest.TestCase):
    def setUp(self):
        self.rows = [row_with(300, rank=50, name="A"), row_with(1200, rank=9000, name="B"),
                     row_with(700, rank=None, name="C")]
        self.no_price = ComparisonRow(key="D", name="D")

    def test_sort_by_diff_descending(self):
        self.assertEqual([r.name for r in sort_rows(self.rows, "diff")], ["B", "C", "A"])

    def test_rows_without_diff_go_last(self):
        rows = sort_rows(self.rows + [self.no_price], "diff")
        self.assertEqual(rows[-1].name, "D")

    def test_sort_by_rank(self):
        self.assertEqual([r.name for r in sort_rows(self.rows, "rank")], ["A", "B", "C"])

    def test_sort_by_name(self):
        self.assertEqual([r.name for r in sort_rows(self.rows, "name")], ["A", "B", "C"])

    def test_sort_by_ratio(self):
        rows = sort_rows(self.rows, "ratio")
        self.assertEqual(rows[0].name, "B")

    def test_filter_by_min_diff(self):
        rows = filter_rows(self.rows, min_diff_jpy=500)
        self.assertEqual({r.name for r in rows}, {"B", "C"})

    def test_filter_by_max_rank_drops_unranked(self):
        rows = filter_rows(self.rows, max_rank=1000)
        self.assertEqual([r.name for r in rows], ["A"])

    def test_filter_top(self):
        self.assertEqual(len(filter_rows(self.rows, top=2)), 2)


class BuildSourcesTest(unittest.TestCase):
    def test_only_configured_sources_are_built(self):
        config = make_config(rakuten={"application_id": "dummy"})
        sources = build_sources(config, client=None)
        self.assertEqual(set(sources), {RAKUTEN})

    def test_no_credentials_means_no_sources(self):
        self.assertEqual(build_sources(make_config(), client=None), {})

    def test_disabled_source_is_skipped(self):
        config = make_config(rakuten={"application_id": "dummy", "enabled": False})
        self.assertEqual(build_sources(config, client=None), {})


if __name__ == "__main__":
    unittest.main()
