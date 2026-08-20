"""CLI の結合テスト(APIを呼ばないオフライン経路)。"""

import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from pricediff.cli import main

WATCHLIST = (
    "key,name,taobao_url,taobao_price_cny,weight_g,amazon_price_jpy,amazon_rank,"
    "rakuten_price_jpy,rakuten_rank\n"
    "a,保温タンブラー,https://item.taobao.com/item.htm?id=1,38.5,320,2480,8420,2180,14\n"
    "b,スマホリング,https://item.taobao.com/item.htm?id=2,6.8,25,980,3150,880,\n"
    "c,価格不明の商品,https://item.taobao.com/item.htm?id=3,10,,,,,\n"
)


class CliTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)
        self.watchlist = self.dir / "watchlist.csv"
        self.watchlist.write_text(WATCHLIST, encoding="utf-8")
        self.cwd = os.getcwd()
        os.chdir(self.dir)  # ./config.yaml や ./.env を拾わせないため
        self.addCleanup(os.chdir, self.cwd)

    def run_cli(self, argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = main(argv)
        return code, out.getvalue(), err.getvalue()

    def test_run_offline_console(self):
        code, out, _ = self.run_cli(["run", "-w", str(self.watchlist), "--offline"])
        self.assertEqual(code, 0)
        self.assertIn("保温タンブラー", out)
        self.assertIn("8,420位", out)
        self.assertIn("14位", out)
        self.assertIn("商品リンク:", out)
        self.assertIn("価格差", out)

    def test_run_writes_all_formats(self):
        code, out, _ = self.run_cli([
            "run", "-w", str(self.watchlist), "--offline",
            "-f", "csv,html,json", "-o", str(self.dir / "out"),
        ])
        self.assertEqual(code, 0)
        files = list((self.dir / "out").iterdir())
        self.assertEqual(len(files), 3)
        suffixes = {f.suffix for f in files}
        self.assertEqual(suffixes, {".csv", ".html", ".json"})
        payload = json.loads(next(f for f in files if f.suffix == ".json").read_text(encoding="utf-8"))
        self.assertEqual(len(payload["items"]), 3)

    def test_sort_and_top(self):
        code, out, _ = self.run_cli([
            "run", "-w", str(self.watchlist), "--offline", "--sort", "diff", "--top", "1",
            "--no-links",
        ])
        self.assertEqual(code, 0)
        self.assertIn("保温タンブラー", out)
        self.assertNotIn("スマホリング", out)

    def test_min_diff_filter(self):
        _, out, _ = self.run_cli([
            "run", "-w", str(self.watchlist), "--offline", "--min-diff", "10000", "--no-links",
        ])
        self.assertIn("対象 0件", out)

    def test_fx_rate_override_changes_cost(self):
        _, cheap, _ = self.run_cli(["run", "-w", str(self.watchlist), "--offline",
                                    "--fx-rate", "10", "--no-links"])
        _, pricey, _ = self.run_cli(["run", "-w", str(self.watchlist), "--offline",
                                     "--fx-rate", "30", "--no-links"])
        self.assertIn("1 CNY = 10.000 JPY", cheap)
        self.assertIn("1 CNY = 30.000 JPY", pricey)
        self.assertNotEqual(cheap, pricey)

    def test_row_without_jp_price_is_warned_not_fatal(self):
        _, out, _ = self.run_cli(["run", "-w", str(self.watchlist), "--offline", "--no-links"])
        self.assertIn("価格不明の商品", out)
        self.assertIn("日本側の価格が取得できませんでした", out)

    def test_missing_watchlist_returns_error_code(self):
        code, _, err = self.run_cli(["run", "-w", str(self.dir / "none.csv"), "--offline"])
        self.assertEqual(code, 2)
        self.assertIn("見つかりません", err)

    def test_unknown_format_returns_error_code(self):
        code, _, err = self.run_cli(["run", "-w", str(self.watchlist), "--offline", "-f", "pdf"])
        self.assertEqual(code, 2)
        self.assertIn("未知の出力形式", err)

    def test_exit_code_1_when_nothing_computable(self):
        empty = self.dir / "nojp.csv"
        empty.write_text("name,taobao_price_cny\n商品,10\n", encoding="utf-8")
        code, _, _ = self.run_cli(["run", "-w", str(empty), "--offline"])
        self.assertEqual(code, 1)

    def test_init_creates_templates(self):
        target = self.dir / "new"
        code, out, _ = self.run_cli(["init", "-d", str(target)])
        self.assertEqual(code, 0)
        self.assertTrue((target / "config.yaml").is_file())
        self.assertTrue((target / "watchlist.csv").is_file())
        self.assertIn("作成", out)

    def test_init_does_not_overwrite_without_force(self):
        target = self.dir / "new2"
        self.run_cli(["init", "-d", str(target)])
        (target / "watchlist.csv").write_text("name\n自分の一覧\n", encoding="utf-8")
        _, out, _ = self.run_cli(["init", "-d", str(target)])
        self.assertIn("skip", out)
        self.assertIn("自分の一覧", (target / "watchlist.csv").read_text(encoding="utf-8"))

    def test_demo_runs_without_arguments(self):
        code, out, err = self.run_cli(["run", "--demo", "--no-links"])
        self.assertEqual(code, 0)
        self.assertIn("デモ", err)
        self.assertIn("ダミー", err)
        self.assertIn("価格差", out)

    def test_doctor_reports_missing_keys(self):
        code, out, _ = self.run_cli(["doctor"])
        self.assertEqual(code, 0)
        self.assertIn("楽天市場", out)
        self.assertIn("APIキーが1つも設定されていません", out)

    def test_no_args_prints_help(self):
        code, out, _ = self.run_cli([])
        self.assertEqual(code, 0)
        self.assertIn("usage:", out)


if __name__ == "__main__":
    unittest.main()
