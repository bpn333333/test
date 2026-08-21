"""ブラウザで調べた行の貼り付け追加(parse_rows / append_items / pricediff add)。"""

import csv
import io
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

from pricediff.cli import main
from pricediff.watchlist import (
    CANONICAL_COLUMNS, WatchlistError, append_items, load_watchlist, parse_rows,
)

HEADER = "name,taobao_url,taobao_price_cny,weight_g,amazon_price_jpy,amazon_rank"
ROW = "保温タンブラー,https://item.taobao.com/item.htm?id=1,38.5,320,2480,8420"


class ParseRowsTest(unittest.TestCase):
    def test_with_header(self):
        items = parse_rows(f"{HEADER}\n{ROW}\n")
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].name, "保温タンブラー")
        self.assertEqual(items[0].taobao_price_cny, 38.5)
        self.assertEqual(items[0].amazon_rank, 8420)

    def test_without_header_uses_canonical_order(self):
        items = parse_rows("k1,保温タンブラー,https://item.taobao.com/item.htm?id=1,38.5,320\n")
        self.assertEqual(items[0].key, "k1")
        self.assertEqual(items[0].weight_g, 320.0)

    def test_japanese_header(self):
        items = parse_rows("商品名,淘宝価格,重さ,Amazonランキング\nヨガマット,55,1050,12800\n")
        self.assertEqual(items[0].name, "ヨガマット")
        self.assertEqual(items[0].taobao_price_cny, 55.0)
        self.assertEqual(items[0].amazon_rank, 12800)

    def test_multiple_rows_and_blank_lines(self):
        text = f"{HEADER}\n{ROW}\n\nスマホリング,https://item.taobao.com/item.htm?id=2,6.8,25,980,3150\n"
        self.assertEqual(len(parse_rows(text)), 2)

    def test_quoted_comma_in_name(self):
        items = parse_rows(f'{HEADER}\n"タンブラー, 480ml",https://x,38.5,320,2480,8420\n')
        self.assertEqual(items[0].name, "タンブラー, 480ml")

    def test_too_many_columns_raises(self):
        with self.assertRaises(WatchlistError) as ctx:
            parse_rows("name,taobao_price_cny\nタンブラー, 480ml,38.5\n")
        self.assertIn("列が多すぎます", str(ctx.exception))

    def test_empty_input_raises(self):
        with self.assertRaises(WatchlistError):
            parse_rows("\n  \n")

    def test_header_only_raises(self):
        with self.assertRaises(WatchlistError) as ctx:
            parse_rows(HEADER + "\n")
        self.assertIn("ヘッダ行だけ", str(ctx.exception))


class AppendItemsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "watchlist.csv"

    def add(self, text, **kwargs):
        return append_items(self.path, parse_rows(text), **kwargs)

    def test_creates_file_with_canonical_columns(self):
        added, skipped = self.add(f"{HEADER}\n{ROW}\n")
        self.assertEqual(len(added), 1)
        self.assertEqual(skipped, [])
        with self.path.open(encoding="utf-8-sig", newline="") as fh:
            reader = csv.DictReader(fh)
            self.assertEqual(reader.fieldnames, CANONICAL_COLUMNS)

    def test_numbers_are_written_without_trailing_zero(self):
        self.add(f"{HEADER}\n{ROW}\n")
        text = self.path.read_text(encoding="utf-8-sig")
        self.assertIn(",320,", text)
        self.assertNotIn("320.0", text)

    def test_duplicate_by_name_is_skipped(self):
        self.add(f"{HEADER}\n{ROW}\n")
        added, skipped = self.add("name,taobao_price_cny\n保温タンブラー,39.9\n")
        self.assertEqual(added, [])
        self.assertEqual(len(skipped), 1)
        self.assertEqual(len(load_watchlist(self.path)), 1)

    def test_duplicate_by_taobao_url_is_skipped(self):
        self.add(f"{HEADER}\n{ROW}\n")
        added, skipped = self.add(
            "name,taobao_url,taobao_price_cny\n別名で登録,https://item.taobao.com/item.htm?id=1,39.9\n")
        self.assertEqual(added, [])
        self.assertEqual(len(skipped), 1)

    def test_update_merges_only_given_columns(self):
        self.add(f"{HEADER},rakuten_price_jpy,rakuten_rank\n{ROW},2180,14\n")
        self.add("name,taobao_price_cny\n保温タンブラー,39.9\n", update=True)
        item = load_watchlist(self.path)[0]
        self.assertEqual(item.taobao_price_cny, 39.9)     # 貼り付けた列は更新
        self.assertEqual(item.rakuten_price_jpy, 2180.0)  # 貼らなかった列は残る
        self.assertEqual(item.rakuten_rank, 14)
        self.assertEqual(item.weight_g, 320.0)

    def test_update_keeps_row_count_and_key(self):
        self.add(f"{HEADER}\n{ROW}\n")
        original_key = load_watchlist(self.path)[0].key
        self.add("name,taobao_price_cny\n保温タンブラー,39.9\n", update=True)
        items = load_watchlist(self.path)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].key, original_key)

    def test_auto_keys_continue_from_existing(self):
        self.add(f"{HEADER}\n{ROW}\n")
        self.add("name,taobao_price_cny\nスマホリング,6.8\n")
        self.assertEqual([i.key for i in load_watchlist(self.path)], ["item001", "item002"])

    def test_explicit_key_duplicate_is_skipped(self):
        self.add("key,name,taobao_price_cny\nmug01,保温タンブラー,38.5\n")
        added, skipped = self.add("key,name,taobao_price_cny\nmug01,別の商品,10\n")
        self.assertEqual(added, [])
        self.assertEqual(len(skipped), 1)

    def test_existing_rows_are_preserved_in_order(self):
        self.add("name,taobao_price_cny\nA,1\n")
        self.add("name,taobao_price_cny\nB,2\n")
        self.add("name,taobao_price_cny\nC,3\n")
        self.assertEqual([i.name for i in load_watchlist(self.path)], ["A", "B", "C"])

    def test_broken_existing_file_raises(self):
        self.path.write_text("name,taobao_price_cny\n商品,やすい\n", encoding="utf-8")
        with self.assertRaises(WatchlistError):
            self.add("name,taobao_price_cny\nA,1\n")


class CliAddTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "watchlist.csv"

    def run_cli(self, argv, stdin_text):
        out, err = io.StringIO(), io.StringIO()
        stdin = io.StringIO(stdin_text)
        stdin.isatty = lambda: False
        with mock.patch("sys.stdin", stdin), redirect_stdout(out), redirect_stderr(err):
            code = main(argv)
        return code, out.getvalue(), err.getvalue()

    def test_add_from_stdin(self):
        code, out, _ = self.run_cli(["add", "-w", str(self.path)], f"{HEADER}\n{ROW}\n")
        self.assertEqual(code, 0)
        self.assertIn("保温タンブラー", out)
        self.assertIn("1件", out)
        self.assertTrue(self.path.is_file())

    def test_duplicate_is_reported_not_failed(self):
        self.run_cli(["add", "-w", str(self.path)], f"{HEADER}\n{ROW}\n")
        code, out, _ = self.run_cli(["add", "-w", str(self.path)], f"{HEADER}\n{ROW}\n")
        self.assertEqual(code, 0)
        self.assertIn("--update", out)
        self.assertEqual(len(load_watchlist(self.path)), 1)

    def test_dry_run_does_not_write(self):
        code, out, _ = self.run_cli(["add", "-w", str(self.path), "--dry-run"], f"{HEADER}\n{ROW}\n")
        self.assertEqual(code, 0)
        self.assertIn("書き込んでいません", out)
        self.assertFalse(self.path.exists())

    def test_bad_input_returns_error_code(self):
        code, _, err = self.run_cli(["add", "-w", str(self.path)], "")
        self.assertEqual(code, 2)
        self.assertIn("エラー", err)

    def test_added_rows_are_usable_by_run(self):
        self.run_cli(["add", "-w", str(self.path)],
                     f"{HEADER},rakuten_price_jpy\n{ROW},2180\n")
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = main(["run", "-w", str(self.path), "--offline", "--no-links"])
        self.assertEqual(code, 0)
        self.assertIn("保温タンブラー", out.getvalue())
        self.assertIn("8,420位", out.getvalue())


if __name__ == "__main__":
    unittest.main()
