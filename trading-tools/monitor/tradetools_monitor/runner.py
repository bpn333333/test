"""市場モニタリングの本体。

  MT5(サイン・EA) → signals.csv → ここ → 通知(コンソール/ファイル/Webhook)
                                        → X配信(任意)

配信済み判定は state_file に残るので、再起動しても同じシグナルは流れない。
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Sequence

from .config import MonitorConfig
from .notifier import Notifier, build_notifiers, format_signal
from .signals import Signal
from .sources import collect


def _load_seen(path: Path) -> set[str]:
    if not path.exists():
        return set()
    try:
        return set(json.loads(path.read_text(encoding="utf-8")).get("seen", []))
    except (json.JSONDecodeError, OSError):
        return set()


def _save_seen(path: Path, seen: Sequence[str], keep: int = 5000) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    trimmed = list(seen)[-keep:]
    path.write_text(
        json.dumps({"seen": trimmed}, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _build_publisher(config: MonitorConfig, dry_run: bool):
    """X配信は任意機能。使わないなら import もしない。"""
    if not config.publish_to_x:
        return None

    # distribution/ は別ディレクトリなのでパスを通す
    distribution_dir = Path(__file__).resolve().parents[2] / "distribution"
    if str(distribution_dir) not in sys.path:
        sys.path.insert(0, str(distribution_dir))

    try:
        from tradetools_x.client import build_client
        from tradetools_x.publisher import Publisher, PublisherConfig
    except ImportError as error:
        print(f"X配信を初期化できません: {error}", flush=True)
        return None

    return Publisher(client=build_client(dry_run=dry_run), config=PublisherConfig())


class Monitor:
    def __init__(self, config: MonitorConfig, dry_run: bool = True) -> None:
        self.config = config
        self.state_path = Path(config.state_file).expanduser()
        self.seen = _load_seen(self.state_path)
        self.notifiers: List[Notifier] = build_notifiers(config)
        self.publisher = _build_publisher(config, dry_run)

    def collect_all(self) -> List[Signal]:
        return list(collect(self.config))

    def new_signals(self, signals: Optional[Sequence[Signal]] = None) -> List[Signal]:
        """まだ通知していないシグナルだけを返す。"""
        source = self.collect_all() if signals is None else signals
        return [s for s in source if s.signal_id not in self.seen]

    def publishable(self, signals: Sequence[Signal]) -> List[Signal]:
        """配信対象。古すぎるシグナルは流さない。

        通知済みかどうかとは無関係に毎回渡す。投稿間隔や1日上限で見送られた分を
        次の巡回で拾い直すため(重複は Publisher 側が signal_id で防ぐ)。
        古い足のエントリーを今さら配信しても読み手を誤らせるだけなので、
        publish_max_age_minutes を過ぎたものは捨てる。
        """
        limit = self.config.publish_max_age_minutes
        if limit <= 0:
            return list(signals)

        now = datetime.now()
        return [
            s for s in signals
            if (now - s.time).total_seconds() <= limit * 60
        ]

    def notify(self, signals: Sequence[Signal]) -> None:
        for signal in signals:
            for notifier in self.notifiers:
                try:
                    notifier.send(signal)
                except Exception as error:  # 通知の失敗で監視を止めない
                    print(f"通知に失敗: {error}", flush=True)
            self.seen.add(signal.signal_id)

        if signals:
            _save_seen(self.state_path, sorted(self.seen))

    def publish(self, signals: Sequence[Signal]) -> None:
        if self.publisher is None:
            return

        targets = self.publishable(signals)
        if not targets:
            return

        for outcome in self.publisher.publish_signals(targets):
            if outcome.posted:
                print(f"X: {outcome.signal_id} → 配信", flush=True)
            elif outcome.reason != "配信済み":  # 毎巡回で同じ行を出さない
                print(f"X: {outcome.signal_id} → 見送り({outcome.reason})", flush=True)

    def run_once(self) -> int:
        collected = self.collect_all()
        fresh = self.new_signals(collected)
        self.notify(fresh)
        # 配信は「新規かどうか」ではなく Publisher の記録で判断する
        self.publish(collected)
        return len(fresh)

    def run_forever(self) -> None:
        print(
            f"監視開始: source={self.config.source} "
            f"symbols={','.join(self.config.symbols)} "
            f"interval={self.config.poll_seconds}s",
            flush=True,
        )
        while True:
            try:
                self.run_once()
            except KeyboardInterrupt:
                print("停止しました", flush=True)
                return
            except Exception as error:  # 一時的な失敗でループを落とさない
                print(f"監視中にエラー: {error}", flush=True)
            time.sleep(self.config.poll_seconds)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="TradeTools 市場モニタリング")
    parser.add_argument("--config", help="設定JSONのパス(省略時は既定値)")
    parser.add_argument("--once", action="store_true", help="1回だけ実行して終了")
    parser.add_argument(
        "--live", action="store_true",
        help="X に実際に投稿する(既定はドライラン)",
    )
    parser.add_argument(
        "--dump-config", metavar="PATH", help="既定設定を書き出して終了",
    )
    args = parser.parse_args(argv)

    if args.dump_config:
        MonitorConfig().dump(args.dump_config)
        print(f"設定を書き出しました: {args.dump_config}")
        return 0

    try:
        config = MonitorConfig.load(args.config)
        config.params.validate()
    except (OSError, ValueError, TypeError) as error:
        print(f"設定の読み込みに失敗: {error}", file=sys.stderr)
        return 2

    monitor = Monitor(config, dry_run=not args.live)

    if args.once:
        count = monitor.run_once()
        print(f"新規シグナル {count} 件", flush=True)
        return 0

    monitor.run_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
