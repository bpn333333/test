from datetime import datetime, timedelta

import pytest

from tradetools_monitor import runner as runner_module
from tradetools_monitor.config import MonitorConfig
from tradetools_monitor.runner import Monitor
from tradetools_monitor.signals import Signal
from tradetools_x.client import PostResult
from tradetools_x.publisher import Publisher, PublisherConfig


class RecordingClient:
    def __init__(self) -> None:
        self.sent = []

    def post(self, text: str) -> PostResult:
        self.sent.append(text)
        return PostResult(ok=True, tweet_id=str(len(self.sent)))


class FakeClock:
    def __init__(self, start: datetime) -> None:
        self.now = start

    def __call__(self) -> datetime:
        return self.now

    def advance(self, **kwargs) -> None:
        self.now += timedelta(**kwargs)


def make_signal(minutes_ago: int, symbol: str = "USDJPY", direction: str = "BUY") -> Signal:
    return Signal(
        direction=direction,
        time=datetime.now() - timedelta(minutes=minutes_ago),
        symbol=symbol,
        timeframe="PERIOD_H1",
        price=157.533,
        sl=156.900,
        tp=158.700,
        atr=0.42,
        adx=30.0,
        reason="EMA12/48 上抜け・ADX 30.0",
    )


@pytest.fixture
def monitor_factory(tmp_path, monkeypatch):
    def build(signals, *, min_interval_seconds=300, max_age=180, clock=None):
        monkeypatch.setattr(runner_module, "collect", lambda config: list(signals))

        config = MonitorConfig(
            notify_console=False,
            notify_file=str(tmp_path / "alerts.log"),
            state_file=str(tmp_path / "monitor_state.json"),
            publish_to_x=False,
            publish_max_age_minutes=max_age,
        )
        monitor = Monitor(config)

        client = RecordingClient()
        monitor.publisher = Publisher(
            client=client,
            config=PublisherConfig(
                state_file=str(tmp_path / "publisher_state.json"),
                min_interval_seconds=min_interval_seconds,
            ),
            now_provider=clock or datetime.now,
        )
        return monitor, client

    return build


def test_signal_is_notified_only_once(monitor_factory, tmp_path):
    monitor, _ = monitor_factory([make_signal(5)])

    assert monitor.run_once() == 1
    assert monitor.run_once() == 0

    log = (tmp_path / "alerts.log").read_text(encoding="utf-8")
    assert log.count("USDJPY") == 1


def test_rate_limited_signal_is_retried_on_the_next_cycle(monitor_factory):
    """レート制限で見送った分が失われないこと(実行時に見つかった不具合)。"""
    clock = FakeClock(datetime.now())
    signals = [make_signal(5, "USDJPY"), make_signal(4, "EURUSD", "SELL")]
    monitor, client = monitor_factory(signals, min_interval_seconds=600, clock=clock)

    monitor.run_once()
    assert len(client.sent) == 1  # 2件目は投稿間隔で見送られる

    # 通知としては処理済みでも、配信は次の巡回で拾い直せること
    assert monitor.run_once() == 0
    clock.advance(seconds=601)
    monitor.run_once()

    assert len(client.sent) == 2


def test_published_signals_are_never_sent_twice(monitor_factory):
    clock = FakeClock(datetime.now())
    monitor, client = monitor_factory([make_signal(5)], min_interval_seconds=0, clock=clock)

    for _ in range(5):
        monitor.run_once()

    assert len(client.sent) == 1


def test_stale_signals_are_not_published(monitor_factory):
    """監視を止めていた間に溜まった古いシグナルを一斉に流さないこと。"""
    monitor, client = monitor_factory(
        [make_signal(minutes_ago=600)], min_interval_seconds=0, max_age=180
    )

    assert monitor.run_once() == 1  # 通知はする
    assert client.sent == []        # 配信はしない


def test_age_limit_of_zero_disables_the_filter(monitor_factory):
    monitor, client = monitor_factory(
        [make_signal(minutes_ago=6000)], min_interval_seconds=0, max_age=0
    )

    monitor.run_once()
    assert len(client.sent) == 1


def test_notifier_failure_does_not_stop_the_loop(monitor_factory):
    class ExplodingNotifier:
        def send(self, signal):
            raise RuntimeError("通知先が落ちている")

    monitor, client = monitor_factory([make_signal(5)], min_interval_seconds=0)
    monitor.notifiers = [ExplodingNotifier()]

    assert monitor.run_once() == 1   # 例外を飲み込んで続行する
    assert len(client.sent) == 1     # 配信は行われる
