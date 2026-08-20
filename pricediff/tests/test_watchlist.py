"""追跡リスト読み込みのテスト。"""

import tempfile
import unittest
from pathlib import Path

from pricediff.watchlist import WatchlistError, load_watchlist


class WatchlistTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)

    def write(self, name: str, content: str) -> Path:
        path = self.dir / name
        path.write_text(content, encoding="utf-8")
        return path

    def test_reads_basic_csv(self):
        path = self.write("w.csv", (
            "key,name,taobao_url,taobao_price_cny,weight_g,amazon_rank\n"
            "a1,保温タンブラー,https://item.taobao.com/item.htm?id=1,38.5,320,8420\n"
        ))
        items = load_watchlist(path)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].key, "a1")
        self.assertEqual(items[0].taobao_price_cny, 38.5)
        self.assertEqual(items[0].weight_g, 320.0)
        self.assertEqual(items[0].amazon_rank, 8420)

    def test_japanese_headers(self):
        path = self.write("jp.csv", "商品名,淘宝価格,重さ,楽天ランキング\nヨガマット,55,1050,31\n")
        item = load_watchlist(path)[0]
        self.assertEqual(item.name, "ヨガマット")
        self.assertEqual(item.taobao_price_cny, 55.0)
        self.assertEqual(item.weight_g, 1050.0)
        self.assertEqual(item.rakuten_rank, 31)

    def test_auto_key_when_missing(self):
        path = self.write("k.csv", "name,taobao_price_cny\n商品A,10\n商品B,20\n")
        self.assertEqual([i.key for i in load_watchlist(path)], ["item001", "item002"])

    def test_strips_currency_symbols_and_commas(self):
        path = self.write("c.csv", "name,amazon_price_jpy,rakuten_rank\n商品,\"¥12,800\",14位\n")
        item = load_watchlist(path)[0]
        self.assertEqual(item.amazon_price_jpy, 12800.0)
        self.assertEqual(item.rakuten_rank, 14)

    def test_blank_rows_are_skipped(self):
        path = self.write("b.csv", "name,taobao_price_cny\n商品A,10\n,\n")
        self.assertEqual(len(load_watchlist(path)), 1)

    def test_unknown_columns_are_ignored(self):
        path = self.write("u.csv", "name,taobao_price_cny,担当者\n商品,10,自分\n")
        self.assertEqual(load_watchlist(path)[0].name, "商品")

    def test_utf8_bom_is_handled(self):
        path = self.dir / "bom.csv"
        path.write_text("name,taobao_price_cny\n商品,10\n", encoding="utf-8-sig")
        self.assertEqual(load_watchlist(path)[0].name, "商品")

    def test_yaml(self):
        path = self.write("w.yaml", (
            "items:\n"
            "  - name: 商品A\n"
            "    taobao_price_cny: 12.5\n"
            "    weight_g: 100\n"
        ))
        self.assertEqual(load_watchlist(path)[0].taobao_price_cny, 12.5)

    def test_missing_name_raises(self):
        path = self.write("n.csv", "name,taobao_price_cny\n,10\n")
        with self.assertRaises(WatchlistError):
            load_watchlist(path)

    def test_duplicate_key_raises(self):
        path = self.write("d.csv", "key,name\nx,商品A\nx,商品B\n")
        with self.assertRaises(WatchlistError):
            load_watchlist(path)

    def test_bad_number_raises(self):
        path = self.write("e.csv", "name,taobao_price_cny\n商品,やすい\n")
        with self.assertRaises(WatchlistError):
            load_watchlist(path)

    def test_missing_file_raises(self):
        with self.assertRaises(WatchlistError):
            load_watchlist(self.dir / "none.csv")

    def test_empty_file_raises(self):
        path = self.write("empty.csv", "name,taobao_price_cny\n")
        with self.assertRaises(WatchlistError):
            load_watchlist(path)

    def test_sample_watchlist_loads(self):
        sample = Path(__file__).resolve().parent.parent / "pricediff" / "templates" / "watchlist.csv"
        items = load_watchlist(sample)
        self.assertEqual(len(items), 10)
        self.assertTrue(all(i.taobao_price_cny for i in items))


if __name__ == "__main__":
    unittest.main()
