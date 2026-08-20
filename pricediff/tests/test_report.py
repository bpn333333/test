"""出力整形(全角幅・コンソール表・CSV/JSON/HTML)のテスト。"""

import csv
import json
import tempfile
import unittest
from pathlib import Path

from pricediff.fx import FxRate
from pricediff.models import AMAZON, RAKUTEN, TAOBAO, ComparisonRow, LandedCost, Offer
from pricediff.report import (
    display_width, fmt_rank, fmt_ratio, fmt_weight, fmt_yen, pad, render_console,
    render_html, render_summary, row_to_record, truncate, write_csv, write_html, write_json,
)


def sample_row(name="ステンレス保温タンブラー", diff=914):
    row = ComparisonRow(key="k", name=name, weight_g=320, weight_source="手入力", fx_rate=21.42)
    row.landed = LandedCost(item_jpy=1000, intl_shipping_jpy=566)
    row.offers[TAOBAO] = Offer(market=TAOBAO, title=name, price=38.5, currency="CNY",
                               url="https://item.taobao.com/item.htm?id=1")
    row.offers[AMAZON] = Offer(market=AMAZON, title=name, price=1566 + diff, currency="JPY",
                               url="https://www.amazon.co.jp/dp/B0SAMPLE01", rank=8420,
                               rank_category="ホーム&キッチン")
    row.offers[RAKUTEN] = Offer(market=RAKUTEN, title=name, price=2180, currency="JPY",
                                url="https://item.rakuten.co.jp/shop123/10000042/", rank=14)
    return row


class WidthTest(unittest.TestCase):
    def test_full_width_counts_as_two(self):
        self.assertEqual(display_width("あいう"), 6)
        self.assertEqual(display_width("abc"), 3)
        self.assertEqual(display_width("あa"), 3)

    def test_pad_aligns_by_display_width(self):
        self.assertEqual(display_width(pad("あa", 10)), 10)
        self.assertEqual(display_width(pad("123", 10, "right")), 10)

    def test_truncate_respects_width(self):
        self.assertLessEqual(display_width(truncate("とても長い日本語の商品名です", 12)), 12)
        self.assertEqual(truncate("短い", 10), "短い")
        self.assertTrue(truncate("とても長い日本語の商品名です", 12).endswith("…"))

    def test_truncate_handles_none(self):
        self.assertEqual(truncate(None, 10), "")


class FormatTest(unittest.TestCase):
    def test_yen(self):
        self.assertEqual(fmt_yen(12800), "12,800")
        self.assertEqual(fmt_yen(914, signed=True), "+914")
        self.assertEqual(fmt_yen(-100, signed=True), "-100")
        self.assertEqual(fmt_yen(None), "-")

    def test_ratio(self):
        self.assertEqual(fmt_ratio(0.58), "+58%")
        self.assertEqual(fmt_ratio(-0.2), "-20%")
        self.assertEqual(fmt_ratio(None), "-")

    def test_weight(self):
        self.assertEqual(fmt_weight(320), "320g")
        self.assertEqual(fmt_weight(1250), "1.25kg")
        self.assertEqual(fmt_weight(None), "-")

    def test_rank(self):
        self.assertEqual(fmt_rank(8420), "8,420位")
        self.assertEqual(fmt_rank(None), "圏外")


class RecordTest(unittest.TestCase):
    def test_record_contains_requested_columns(self):
        record = row_to_record(sample_row())
        for column in ("商品名", "淘宝リンク", "Amazonリンク", "楽天リンク", "価格差_円",
                       "重さ_g", "Amazonランキング", "楽天ランキング"):
            self.assertIn(column, record)
        self.assertEqual(record["価格差_円"], 914)
        self.assertEqual(record["重さ_g"], 320)
        self.assertEqual(record["Amazonランキング"], 8420)
        self.assertEqual(record["楽天ランキング"], 14)
        self.assertEqual(record["最高値モール"], "Amazon")

    def test_record_handles_empty_row(self):
        record = row_to_record(ComparisonRow(key="k", name="空"))
        self.assertIsNone(record["価格差_円"])
        self.assertEqual(record["淘宝リンク"], "")


class ConsoleTest(unittest.TestCase):
    def test_table_columns_are_aligned(self):
        output = render_console([sample_row(), sample_row("短い", 100)], show_links=False)
        lines = [line for line in output.splitlines() if line.strip()]
        widths = {display_width(line) for line in lines[:4]}
        self.assertEqual(len(widths), 1, f"行の表示幅が揃っていない: {widths}")

    def test_links_section(self):
        output = render_console([sample_row()])
        self.assertIn("商品リンク:", output)
        self.assertIn("https://item.taobao.com/item.htm?id=1", output)
        self.assertIn("https://www.amazon.co.jp/dp/B0SAMPLE01", output)

    def test_warnings_section(self):
        row = sample_row()
        row.errors.append("楽天: HTTP 429")
        self.assertIn("警告:", render_console([row]))
        self.assertIn("HTTP 429", render_console([row]))

    def test_empty_input(self):
        self.assertIn("商品名", render_console([]))

    def test_summary(self):
        summary = render_summary([sample_row()], FxRate(21.0, "設定値", 2.0), elapsed=1.2)
        self.assertIn("対象 1件", summary)
        self.assertIn("1 CNY", summary)
        self.assertIn("1.2秒", summary)


class CostLabelTest(unittest.TestCase):
    """列見出しは仕入値の取り方に合わせて変わる。"""

    def test_console_header_says_item_price_by_default(self):
        output = render_console([sample_row()], show_links=False)
        self.assertIn("商品代", output)
        self.assertNotIn("原価", output)

    def test_console_header_says_landed_cost_in_landed_mode(self):
        output = render_console([sample_row()], show_links=False, mode="landed")
        self.assertIn("原価", output)

    def test_header_change_keeps_columns_aligned(self):
        for mode in ("item", "landed"):
            output = render_console([sample_row()], show_links=False, mode=mode)
            lines = [line for line in output.splitlines() if line.strip()]
            self.assertEqual(len({display_width(line) for line in lines[:3]}), 1, mode)

    def test_html_header_and_note_follow_mode(self):
        item_html = render_html([sample_row()])
        self.assertIn("商品代(円)", item_html)
        self.assertIn("商品代(淘宝価格の円換算)", item_html)
        landed_html = render_html([sample_row()], mode="landed")
        self.assertIn("原価(円)", landed_html)
        self.assertIn("国際送料", landed_html)


class FileOutputTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)

    def test_csv_is_excel_readable(self):
        path = write_csv([sample_row()], self.dir / "out.csv")
        raw = path.read_bytes()
        self.assertTrue(raw.startswith(b"\xef\xbb\xbf"), "Excel向けのBOMが無い")
        with path.open(encoding="utf-8-sig", newline="") as fh:
            rows = list(csv.DictReader(fh))
        self.assertEqual(rows[0]["Amazonランキング"], "8420")
        self.assertEqual(rows[0]["楽天ランキング"], "14")
        self.assertEqual(rows[0]["重さ_g"], "320")
        self.assertEqual(rows[0]["仕入値_円"], "1566")
        self.assertTrue(rows[0]["淘宝リンク"].startswith("https://"))

    def test_json_has_meta_and_items(self):
        path = write_json([sample_row()], self.dir / "out.json", meta={"fx_rate": 21.42})
        payload = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(payload["meta"]["fx_rate"], 21.42)
        self.assertEqual(len(payload["items"]), 1)
        self.assertIn("仕入値内訳", payload["items"][0])

    def test_html_contains_table_and_links(self):
        html_text = render_html([sample_row()], fx=FxRate(21.0, "test"))
        self.assertIn("<table>", html_text)
        self.assertIn("8,420位", html_text)
        self.assertIn("14位", html_text)
        self.assertIn("https://item.rakuten.co.jp/shop123/10000042/", html_text)
        self.assertIn("prefers-color-scheme", html_text)

    def test_html_escapes_markup_in_names(self):
        row = sample_row(name='<script>alert("x")</script>')
        html_text = render_html([row])
        self.assertNotIn("<script>alert", html_text)
        self.assertIn("&lt;script&gt;", html_text)

    def test_html_file_written(self):
        path = write_html([sample_row()], self.dir / "out.html", fx=FxRate(21.0, "t"))
        self.assertTrue(path.is_file())
        self.assertIn("<!DOCTYPE html>", path.read_text(encoding="utf-8"))

    def test_html_handles_missing_values(self):
        html_text = render_html([ComparisonRow(key="k", name="価格不明")])
        self.assertIn("圏外", html_text)
        self.assertIn("価格不明", html_text)


if __name__ == "__main__":
    unittest.main()
