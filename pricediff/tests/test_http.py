"""HTTPクライアント(キャッシュ・リトライ・レート制限)のテスト。"""

import tempfile
import unittest
from pathlib import Path
from unittest import mock

import requests

from pricediff.sources.http import DiskCache, FetchError, HttpClient


class FakeResponse:
    def __init__(self, status_code=200, payload=None, text=""):
        self.status_code = status_code
        self._payload = payload if payload is not None else {"ok": True}
        self.text = text

    def json(self):
        return self._payload


class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []
        self.headers = {}

    def request(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        result = self.responses.pop(0)
        if isinstance(result, Exception):
            raise result
        return result


def make_client(responses, **kwargs):
    client = HttpClient(interval=0, backoff=0, **kwargs)
    client.session = FakeSession(responses)
    return client


class HttpClientTest(unittest.TestCase):
    def test_returns_json(self):
        client = make_client([FakeResponse(payload={"Items": [1]})])
        self.assertEqual(client.get_json("https://x"), {"Items": [1]})
        self.assertEqual(client.stats["requests"], 1)

    def test_retries_on_500_then_succeeds(self):
        client = make_client([FakeResponse(500, text="boom"), FakeResponse(payload={"ok": 1})])
        self.assertEqual(client.get_json("https://x"), {"ok": 1})
        self.assertEqual(len(client.session.calls), 2)

    def test_retries_on_429(self):
        client = make_client([FakeResponse(429), FakeResponse(payload={"ok": 1})])
        self.assertEqual(client.get_json("https://x"), {"ok": 1})

    def test_does_not_retry_on_400(self):
        client = make_client([FakeResponse(400, text="bad request"), FakeResponse()])
        with self.assertRaises(FetchError):
            client.get_json("https://x")
        self.assertEqual(len(client.session.calls), 1)

    def test_retries_on_network_error(self):
        client = make_client([requests.ConnectionError("down"), FakeResponse(payload={"ok": 1})])
        self.assertEqual(client.get_json("https://x"), {"ok": 1})

    def test_raises_after_exhausting_retries(self):
        client = make_client([FakeResponse(500)] * 3, retries=3)
        with self.assertRaises(FetchError):
            client.get_json("https://x")
        self.assertEqual(client.stats["errors"], 1)

    def test_throttle_sleeps_between_requests(self):
        client = HttpClient(interval=1.0, backoff=0)
        client.session = FakeSession([FakeResponse(), FakeResponse()])
        with mock.patch("pricediff.sources.http.time.sleep") as sleep:
            client.get_json("https://x")
            client.get_json("https://y")
        self.assertTrue(sleep.called)


class DiskCacheTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)

    def test_roundtrip(self):
        cache = DiskCache(str(self.dir), ttl_seconds=60)
        cache.set("key", {"a": 1})
        self.assertEqual(cache.get("key"), {"a": 1})

    def test_expired_entry_returns_none(self):
        cache = DiskCache(str(self.dir), ttl_seconds=0)
        cache.set("key", {"a": 1})
        self.assertIsNone(cache.get("key"))

    def test_disabled_cache_stores_nothing(self):
        cache = DiskCache(str(self.dir), ttl_seconds=60, enabled=False)
        cache.set("key", {"a": 1})
        self.assertIsNone(cache.get("key"))

    def test_corrupted_file_is_ignored(self):
        cache = DiskCache(str(self.dir), ttl_seconds=60)
        cache.set("key", {"a": 1})
        next(self.dir.iterdir()).write_text("これはJSONではない", encoding="utf-8")
        self.assertIsNone(cache.get("key"))

    def test_client_uses_cache_on_second_call(self):
        cache = DiskCache(str(self.dir), ttl_seconds=60)
        client = make_client([FakeResponse(payload={"v": 1})], cache=cache)
        self.assertEqual(client.get_json("https://x"), {"v": 1})
        self.assertEqual(client.get_json("https://x"), {"v": 1})  # 2回目はAPIを叩かない
        self.assertEqual(len(client.session.calls), 1)
        self.assertEqual(client.stats["cache_hits"], 1)

    def test_different_params_are_cached_separately(self):
        cache = DiskCache(str(self.dir), ttl_seconds=60)
        client = make_client([FakeResponse(payload={"v": 1}), FakeResponse(payload={"v": 2})],
                             cache=cache)
        self.assertEqual(client.get_json("https://x", {"q": "a"}), {"v": 1})
        self.assertEqual(client.get_json("https://x", {"q": "b"}), {"v": 2})


if __name__ == "__main__":
    unittest.main()
