"""APIソースの取得フロー(リクエスト組み立て〜順位の紐付け)のテスト。

実際の通信はせず、HttpClient をスタブに差し替えて検証する。
"""

import copy
import json
import unittest
from pathlib import Path

from pricediff.config import Config, DEFAULTS
from pricediff.models import WatchItem
from pricediff.sources.amazon import AmazonSource
from pricediff.sources.http import FetchError
from pricediff.sources.rakuten import RakutenSource
from pricediff.sources.taobao import TaobaoSource

FIXTURES = Path(__file__).parent / "fixtures"


def fixture(name):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def make_config(**overrides):
    data = copy.deepcopy(DEFAULTS)
    for section, values in overrides.items():
        data[section].update(values)
    return Config(data)


class StubClient:
    """URL の一部をキーにして応答を返すスタブ。"""

    def __init__(self, routes):
        self.routes = routes
        self.calls = []

    def _respond(self, url, params=None, **kwargs):
        self.calls.append({"url": url, "params": params, **kwargs})
        for fragment, payload in self.routes.items():
            if fragment in url:
                if isinstance(payload, Exception):
                    raise payload
                return payload
        raise AssertionError(f"想定外のURL: {url}")

    def get_json(self, url, params=None, **kwargs):
        return self._respond(url, params, **kwargs)

    def post_json(self, url, **kwargs):
        return self._respond(url, None, **kwargs)


class RakutenFetchTest(unittest.TestCase):
    def setUp(self):
        self.config = make_config(rakuten={"application_id": "APPID", "ranking_period": "daily"})
        self.client = StubClient({
            "IchibaItem/Search": fixture("rakuten_search.json"),
            "IchibaItem/Ranking": fixture("rakuten_ranking.json"),
        })
        self.source = RakutenSource(self.config, self.client)

    def test_available(self):
        self.assertTrue(self.source.available())
        self.assertFalse(RakutenSource(make_config(), self.client).available())

    def test_search_params(self):
        self.source.fetch(WatchItem(key="k", name="タンブラー", rakuten_keyword="タンブラー 480ml"))
        params = self.client.calls[0]["params"]
        self.assertEqual(params["applicationId"], "APPID")
        self.assertEqual(params["keyword"], "タンブラー 480ml")
        self.assertEqual(params["format"], "json")

    def test_rank_is_attached_from_ranking_api(self):
        offer = self.source.fetch(WatchItem(key="k", name="タンブラー"))
        self.assertEqual(offer.price, 2180.0)
        self.assertEqual(offer.rank, 14)             # ランキングAPI の 14位が紐づく
        self.assertIn("558885", offer.rank_category)  # 検索結果のジャンルIDを使う
        self.assertEqual(self.client.calls[1]["params"]["period"], "daily")

    def test_out_of_ranking_is_marked(self):
        client = StubClient({
            "IchibaItem/Search": fixture("rakuten_search.json"),
            "IchibaItem/Ranking": {"Items": [{"rank": 1, "itemCode": "someone:else"}]},
        })
        offer = RakutenSource(self.config, client).fetch(WatchItem(key="k", name="タンブラー"))
        self.assertIsNone(offer.rank)
        self.assertIn("圏外", offer.rank_category)

    def test_ranking_is_fetched_once_per_genre(self):
        item = WatchItem(key="k", name="タンブラー")
        self.source.fetch(item)
        self.source.fetch(item)
        ranking_calls = [c for c in self.client.calls if "Ranking" in c["url"]]
        self.assertEqual(len(ranking_calls), 1)  # 2商品目以降はキャッシュを使う

    def test_ranking_failure_does_not_lose_price(self):
        client = StubClient({
            "IchibaItem/Search": fixture("rakuten_search.json"),
            "IchibaItem/Ranking": FetchError("HTTP 500"),
        })
        with self.assertLogs("pricediff.sources.rakuten", level="WARNING"):
            offer = RakutenSource(self.config, client).fetch(WatchItem(key="k", name="タンブラー"))
        self.assertEqual(offer.price, 2180.0)
        self.assertEqual(offer.note, "ランキング取得失敗")

    def test_explicit_genre_id_is_used(self):
        self.source.fetch(WatchItem(key="k", name="商品", rakuten_genre_id="101070"))
        self.assertEqual(self.client.calls[0]["params"]["genreId"], "101070")
        self.assertEqual(self.client.calls[1]["params"]["genreId"], "101070")

    def test_no_keyword_returns_none(self):
        self.assertIsNone(self.source.fetch(WatchItem(key="k", name="")))


class AmazonFetchTest(unittest.TestCase):
    def setUp(self):
        self.config = make_config(amazon={
            "access_key": "AK", "secret_key": "SK", "partner_tag": "tag-22"})
        self.client = StubClient({"paapi5": fixture("amazon_searchitems.json")})
        self.source = AmazonSource(self.config, self.client)

    def test_available_requires_all_three_keys(self):
        self.assertTrue(self.source.available())
        partial = make_config(amazon={"access_key": "AK", "secret_key": "SK"})
        self.assertFalse(AmazonSource(partial, self.client).available())

    def test_search_by_keyword(self):
        offer = self.source.fetch(WatchItem(key="k", name="タンブラー"))
        call = self.client.calls[0]
        self.assertIn("/paapi5/searchitems", call["url"])
        body = json.loads(call["data"].decode("utf-8"))
        self.assertEqual(body["Keywords"], "タンブラー")
        self.assertEqual(body["PartnerTag"], "tag-22")
        self.assertIn("BrowseNodeInfo.WebsiteSalesRank", body["Resources"])
        self.assertEqual(offer.rank, 8420)

    def test_getitems_when_asin_given(self):
        self.source.fetch(WatchItem(key="k", name="商品", amazon_asin="B0SAMPLE01"))
        call = self.client.calls[0]
        self.assertIn("/paapi5/getitems", call["url"])
        body = json.loads(call["data"].decode("utf-8"))
        self.assertEqual(body["ItemIds"], ["B0SAMPLE01"])
        self.assertEqual(call["headers"]["x-amz-target"],
                         "com.amazon.paapi5.v1.ProductAdvertisingAPIv1.GetItems")

    def test_signed_headers_are_sent(self):
        self.source.fetch(WatchItem(key="k", name="商品"))
        headers = self.client.calls[0]["headers"]
        self.assertTrue(headers["Authorization"].startswith("AWS4-HMAC-SHA256 "))
        self.assertEqual(headers["content-encoding"], "amz-1.0")

    def test_error_is_wrapped_with_context(self):
        client = StubClient({"paapi5": FetchError("HTTP 429")})
        with self.assertRaises(FetchError) as ctx:
            AmazonSource(self.config, client).fetch(WatchItem(key="k", name="商品"))
        self.assertIn("PA-API", str(ctx.exception))


class TaobaoFetchTest(unittest.TestCase):
    def setUp(self):
        self.config = make_config(taobao={"app_key": "AK", "app_secret": "SECRET"})
        self.client = StubClient({"router/rest": fixture("taobao_item.json")})
        self.source = TaobaoSource(self.config, self.client)

    def test_fetch_uses_item_id_from_url(self):
        offer = self.source.fetch(WatchItem(
            key="k", name="商品", taobao_url="https://item.taobao.com/item.htm?id=600000000001"))
        body = self.client.calls[0]["data"]
        self.assertIn("num_iids=600000000001", body)
        self.assertIn("sign=", body)
        self.assertIn("sign_method=md5", body)
        self.assertEqual(offer.price, 38.5)

    def test_no_url_means_no_call(self):
        self.assertIsNone(self.source.fetch(WatchItem(key="k", name="商品")))
        self.assertEqual(self.client.calls, [])

    def test_api_error_response_raises(self):
        client = StubClient({"router/rest": {
            "error_response": {"code": 27, "msg": "Invalid session", "sub_msg": "権限がありません"}}})
        with self.assertRaises(FetchError) as ctx:
            TaobaoSource(self.config, client).fetch(WatchItem(
                key="k", name="商品", taobao_url="https://item.taobao.com/item.htm?id=1"))
        self.assertIn("権限がありません", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
