"""各モールのレスポンス解析・署名・マージ処理のテスト。"""

import datetime as dt
import json
import unittest
from pathlib import Path

from pricediff.models import AMAZON, RAKUTEN, TAOBAO, Offer, WatchItem
from pricediff.sources.amazon import AmazonSource, sigv4_headers, to_cm, to_grams
from pricediff.sources.manual import build_manual_offer, merge_offers, search_url
from pricediff.sources.rakuten import RakutenSource
from pricediff.sources.taobao import TaobaoSource, extract_item_id, sign_params

FIXTURES = Path(__file__).parent / "fixtures"


def fixture(name: str):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


class RakutenParseTest(unittest.TestCase):
    def test_parse_search_flat_format(self):
        offer = RakutenSource.parse_search(fixture("rakuten_search.json"))
        self.assertEqual(offer.market, RAKUTEN)
        self.assertEqual(offer.price, 2180.0)
        self.assertEqual(offer.raw["itemCode"], "shop123:10000042")
        self.assertEqual(offer.raw["genreId"], "558885")
        self.assertEqual(offer.review_count, 128)
        self.assertEqual(offer.review_average, 4.42)

    def test_parse_search_nested_format(self):
        """古い formatVersion では Items が {"Item": {...}} で包まれる。"""
        payload = {"Items": [{"Item": {"itemName": "包まれた商品", "itemPrice": 1000,
                                       "itemUrl": "https://item.rakuten.co.jp/a/b/"}}]}
        offer = RakutenSource.parse_search(payload)
        self.assertEqual(offer.title, "包まれた商品")
        self.assertEqual(offer.price, 1000.0)

    def test_parse_search_empty(self):
        self.assertIsNone(RakutenSource.parse_search({"Items": []}))
        self.assertIsNone(RakutenSource.parse_search({}))

    def test_parse_search_without_price(self):
        self.assertIsNone(RakutenSource.parse_search({"Items": [{"itemName": "x"}]}))

    def test_parse_ranking(self):
        rank_map = RakutenSource.parse_ranking(fixture("rakuten_ranking.json"))
        self.assertEqual(rank_map["shop123:10000042"], 14)
        self.assertEqual(rank_map["other:9"], 2)
        self.assertNotIn(None, rank_map)

    def test_parse_ranking_skips_broken_rows(self):
        payload = {"Items": [{"rank": "x", "itemCode": "a:1"}, {"itemCode": "b:2"}, {"rank": 3}]}
        self.assertEqual(RakutenSource.parse_ranking(payload), {})


class AmazonParseTest(unittest.TestCase):
    def test_parse_search_result(self):
        offer = AmazonSource.parse(fixture("amazon_searchitems.json"))
        self.assertEqual(offer.market, AMAZON)
        self.assertEqual(offer.price, 2480.0)
        self.assertEqual(offer.rank, 8420)
        self.assertEqual(offer.rank_category, "ホーム&キッチン")
        self.assertAlmostEqual(offer.weight_g, 299.4, places=1)
        self.assertEqual(offer.raw["asin"], "B0SAMPLE01")

    def test_parse_falls_back_to_browse_node_rank(self):
        payload = {"ItemsResult": {"Items": [{
            "ASIN": "B1", "DetailPageURL": "https://x",
            "ItemInfo": {"Title": {"DisplayValue": "商品"}},
            "BrowseNodeInfo": {"BrowseNodes": [
                {"SalesRank": 900, "DisplayName": "キッチン"},
                {"SalesRank": 300, "DisplayName": "食器"}]},
        }]}}
        offer = AmazonSource.parse(payload)
        self.assertEqual(offer.rank, 300)
        self.assertEqual(offer.rank_category, "食器")

    def test_parse_without_offer_records_note(self):
        payload = {"SearchResult": {"Items": [{
            "ASIN": "B2", "DetailPageURL": "https://x",
            "ItemInfo": {"Title": {"DisplayValue": "在庫切れ商品"}}}]}}
        offer = AmazonSource.parse(payload)
        self.assertIsNone(offer.price)
        self.assertIn("価格取得不可", offer.note)

    def test_parse_empty(self):
        self.assertIsNone(AmazonSource.parse({"SearchResult": {"Items": []}}))
        self.assertIsNone(AmazonSource.parse({}))

    def test_weight_unit_conversion(self):
        self.assertAlmostEqual(to_grams({"DisplayValue": 1, "Unit": "Pounds"}), 453.59237)
        self.assertEqual(to_grams({"DisplayValue": 250, "Unit": "Grams"}), 250)
        self.assertEqual(to_grams({"DisplayValue": 1.2, "Unit": "Kilograms"}), 1200)
        self.assertAlmostEqual(to_grams({"DisplayValue": 100, "Unit": "Hundredths Pounds"}), 453.59237)
        self.assertIsNone(to_grams({"DisplayValue": 1, "Unit": "Stones"}))
        self.assertIsNone(to_grams(None))

    def test_length_unit_conversion(self):
        self.assertAlmostEqual(to_cm({"DisplayValue": 10, "Unit": "Inches"}), 25.4)
        self.assertAlmostEqual(to_cm({"DisplayValue": 500, "Unit": "Hundredths Inches"}), 12.7)


class SigV4Test(unittest.TestCase):
    def headers(self, payload='{"Keywords":"test"}'):
        return sigv4_headers(
            access_key="AKIAEXAMPLE", secret_key="SECRETEXAMPLE",
            host="webservices.amazon.co.jp", region="us-west-2",
            path="/paapi5/searchitems",
            target="com.amazon.paapi5.v1.ProductAdvertisingAPIv1.SearchItems",
            payload=payload,
            timestamp=dt.datetime(2026, 8, 20, 12, 0, 0, tzinfo=dt.timezone.utc),
        )

    def test_required_headers_present(self):
        headers = self.headers()
        self.assertEqual(headers["x-amz-date"], "20260820T120000Z")
        self.assertEqual(headers["content-encoding"], "amz-1.0")
        self.assertIn("SignedHeaders=content-encoding;content-type;host;x-amz-date;x-amz-target",
                      headers["Authorization"])
        self.assertIn("Credential=AKIAEXAMPLE/20260820/us-west-2/ProductAdvertisingAPI/aws4_request",
                      headers["Authorization"])

    def test_signature_is_deterministic(self):
        self.assertEqual(self.headers()["Authorization"], self.headers()["Authorization"])

    def test_signature_changes_with_payload(self):
        self.assertNotEqual(
            self.headers('{"Keywords":"a"}')["Authorization"],
            self.headers('{"Keywords":"b"}')["Authorization"],
        )

    def test_signature_regression(self):
        """署名生成の手順が変わっていないことを固定値で確認する。"""
        signature = self.headers()["Authorization"].split("Signature=")[-1]
        self.assertEqual(len(signature), 64)
        self.assertEqual(
            signature,
            "6d4d2ee09a3cfe458965c2446ca60769b1cbcc5cf38ef14b91586c7ab98bcdb7",
        )


class TaobaoTest(unittest.TestCase):
    def test_extract_item_id(self):
        cases = {
            "https://item.taobao.com/item.htm?id=654321098765&ns=1": "654321098765",
            "https://detail.tmall.com/item.htm?spm=a230r.1&id=712345678901": "712345678901",
            "https://m.intl.taobao.com/detail/detail.html?id=555555555": "555555555",
            "https://world.taobao.com/item/600000000001.htm": "600000000001",
        }
        for url, expected in cases.items():
            self.assertEqual(extract_item_id(url), expected, url)

    def test_extract_item_id_missing(self):
        self.assertIsNone(extract_item_id(None))
        self.assertIsNone(extract_item_id("https://example.com/none"))

    def test_sign_params_is_uppercase_md5(self):
        signature = sign_params({"b": "2", "a": "1"}, "secret")
        self.assertEqual(len(signature), 32)
        self.assertEqual(signature, signature.upper())
        # 並び順に依存しない(キー昇順で連結される)
        self.assertEqual(signature, sign_params({"a": "1", "b": "2"}, "secret"))

    def test_sign_params_skips_none(self):
        self.assertEqual(sign_params({"a": "1", "b": None}, "s"), sign_params({"a": "1"}, "s"))

    def test_parse(self):
        offer = TaobaoSource.parse(fixture("taobao_item.json"))
        self.assertEqual(offer.price, 38.5)
        self.assertEqual(offer.currency, "CNY")
        self.assertTrue(offer.url.startswith("https://"))

    def test_parse_uses_reserve_price_when_no_discount(self):
        payload = {"tbk_item_info_get_response": {"results": {"n_tbk_item": [
            {"title": "商品", "reserve_price": "59.00"}]}}}
        self.assertEqual(TaobaoSource.parse(payload).price, 59.0)

    def test_parse_empty(self):
        self.assertIsNone(TaobaoSource.parse({}))


class ManualSourceTest(unittest.TestCase):
    def test_builds_offer_from_watchlist(self):
        item = WatchItem(key="k", name="商品", taobao_price_cny=38.5, weight_g=300,
                         amazon_price_jpy=2480, amazon_rank=8420)
        taobao = build_manual_offer(item, TAOBAO)
        amazon = build_manual_offer(item, AMAZON)
        self.assertEqual(taobao.price, 38.5)
        self.assertEqual(taobao.currency, "CNY")
        self.assertEqual(amazon.rank, 8420)
        self.assertEqual(amazon.source, "manual")

    def test_asin_becomes_direct_url(self):
        item = WatchItem(key="k", name="商品", amazon_asin="B0SAMPLE01", amazon_price_jpy=100)
        self.assertEqual(build_manual_offer(item, AMAZON).url,
                         "https://www.amazon.co.jp/dp/B0SAMPLE01")

    def test_search_url_fallback(self):
        item = WatchItem(key="k", name="ヨガマット", rakuten_price_jpy=2980)
        offer = build_manual_offer(item, RAKUTEN)
        self.assertTrue(offer.url.startswith("https://search.rakuten.co.jp/"))
        self.assertIn("検索リンク", offer.note)

    def test_search_url_encodes_japanese(self):
        self.assertIn("%E3%83%A8", search_url(AMAZON, "ヨガマット"))
        self.assertEqual(search_url(AMAZON, None), "")

    def test_no_offer_without_any_information(self):
        self.assertIsNone(build_manual_offer(WatchItem(key="k", name="商品"), TAOBAO))


class MergeOffersTest(unittest.TestCase):
    def test_api_wins_manual_fills_gaps(self):
        api = Offer(market=AMAZON, title="APIの名前", url="https://api", price=2480, source="api")
        manual = Offer(market=AMAZON, title="手入力", url="https://manual", price=9999,
                       rank=8420, weight_g=300, source="manual")
        merged = merge_offers(api, manual)
        self.assertEqual(merged.price, 2480)       # API優先
        self.assertEqual(merged.url, "https://api")
        self.assertEqual(merged.rank, 8420)         # 欠けていた項目は手入力で補完
        self.assertEqual(merged.weight_g, 300)
        self.assertEqual(merged.source, "api+manual")

    def test_source_untouched_when_nothing_filled(self):
        api = Offer(market=AMAZON, title="t", url="u", price=1, rank=2, weight_g=3, source="api")
        merged = merge_offers(api, Offer(market=AMAZON, title="m", url="mu", price=9, source="manual"))
        self.assertEqual(merged.source, "api")

    def test_none_handling(self):
        manual = Offer(market=AMAZON, title="m", url="u", price=1, source="manual")
        self.assertIs(merge_offers(None, manual), manual)
        self.assertIs(merge_offers(manual, None), manual)
        self.assertIsNone(merge_offers(None, None))


if __name__ == "__main__":
    unittest.main()
