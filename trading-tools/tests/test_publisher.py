from datetime import datetime, timedelta

from tradetools_monitor.signals import Signal
from tradetools_x.client import PostResult
from tradetools_x.publisher import Publisher, PublisherConfig


class FakeClock:
    def __init__(self, start: datetime) -> None:
        self.now = start

    def __call__(self) -> datetime:
        return self.now

    def advance(self, **kwargs) -> None:
        self.now += timedelta(**kwargs)


class RecordingClient:
    def __init__(self, ok: bool = True) -> None:
        self.sent = []
        self.ok = ok

    def post(self, text: str) -> PostResult:
        self.sent.append(text)
        if not self.ok:
            return PostResult(ok=False, error="HTTP 429: rate limited")
        return PostResult(ok=True, tweet_id=str(len(self.sent)))


def make_signal(hour: int = 18, direction: str = "BUY") -> Signal:
    return Signal(
        direction=direction,
        time=datetime(2026, 2, 11, hour, 0),
        symbol="USDJPY",
        timeframe="PERIOD_H1",
        price=157.533,
        sl=156.900,
        tp=158.700,
        atr=0.42,
        adx=30.0,
        reason="EMA12/48 上抜け・ADX 30.0",
    )


def build(tmp_path, clock, client=None, **overrides):
    config = PublisherConfig(
        state_file=str(tmp_path / "state.json"),
        min_interval_seconds=overrides.pop("min_interval_seconds", 300),
        max_posts_per_day=overrides.pop("max_posts_per_day", 12),
        **overrides,
    )
    return Publisher(client=client or RecordingClient(), config=config, now_provider=clock)


def test_first_signal_is_published(tmp_path):
    clock = FakeClock(datetime(2026, 2, 11, 19, 0))
    client = RecordingClient()
    publisher = build(tmp_path, clock, client)

    outcomes = publisher.publish_signals([make_signal()])

    assert outcomes[0].posted
    assert len(client.sent) == 1


def test_same_signal_is_not_published_twice(tmp_path):
    clock = FakeClock(datetime(2026, 2, 11, 19, 0))
    client = RecordingClient()
    publisher = build(tmp_path, clock, client)

    publisher.publish_signals([make_signal()])
    clock.advance(hours=1)
    outcomes = publisher.publish_signals([make_signal()])

    assert not outcomes[0].posted
    assert outcomes[0].reason == "配信済み"
    assert len(client.sent) == 1


def test_dedupe_survives_restart(tmp_path):
    clock = FakeClock(datetime(2026, 2, 11, 19, 0))
    client = RecordingClient()
    build(tmp_path, clock, client).publish_signals([make_signal()])

    clock.advance(hours=2)
    reloaded = build(tmp_path, clock, client)
    outcomes = reloaded.publish_signals([make_signal()])

    assert not outcomes[0].posted
    assert len(client.sent) == 1


def test_minimum_interval_is_enforced(tmp_path):
    clock = FakeClock(datetime(2026, 2, 11, 19, 0))
    client = RecordingClient()
    publisher = build(tmp_path, clock, client, min_interval_seconds=600)

    publisher.publish_signals([make_signal(hour=18)])
    clock.advance(seconds=60)
    outcomes = publisher.publish_signals([make_signal(hour=19)])

    assert not outcomes[0].posted
    assert "待機" in outcomes[0].reason
    assert len(client.sent) == 1


def test_posting_resumes_after_the_interval(tmp_path):
    clock = FakeClock(datetime(2026, 2, 11, 19, 0))
    client = RecordingClient()
    publisher = build(tmp_path, clock, client, min_interval_seconds=600)

    publisher.publish_signals([make_signal(hour=18)])
    clock.advance(seconds=601)
    outcomes = publisher.publish_signals([make_signal(hour=19)])

    assert outcomes[0].posted
    assert len(client.sent) == 2


def test_daily_cap_stops_further_posts(tmp_path):
    clock = FakeClock(datetime(2026, 2, 11, 9, 0))
    client = RecordingClient()
    publisher = build(tmp_path, clock, client, min_interval_seconds=0, max_posts_per_day=2)

    for hour in (9, 10, 11):
        publisher.publish_signals([make_signal(hour=hour)])

    assert len(client.sent) == 2


def test_daily_cap_resets_the_next_day(tmp_path):
    clock = FakeClock(datetime(2026, 2, 11, 9, 0))
    client = RecordingClient()
    publisher = build(tmp_path, clock, client, min_interval_seconds=0, max_posts_per_day=1)

    publisher.publish_signals([make_signal(hour=9)])
    clock.advance(days=1)
    publisher.publish_signals([make_signal(hour=10)])

    assert len(client.sent) == 2


def test_send_failure_is_not_recorded_as_posted(tmp_path):
    clock = FakeClock(datetime(2026, 2, 11, 19, 0))
    failing = RecordingClient(ok=False)
    publisher = build(tmp_path, clock, failing)

    outcomes = publisher.publish_signals([make_signal()])
    assert not outcomes[0].posted
    assert "送信失敗" in outcomes[0].reason

    # 失敗した分は次回に再試行できること
    working = RecordingClient()
    retry = build(tmp_path, clock, working)
    assert retry.publish_signals([make_signal()])[0].posted


def test_dry_run_client_writes_to_file(tmp_path):
    from tradetools_x.client import DryRunClient

    log = tmp_path / "dryrun.log"
    result = DryRunClient(log).post("テスト投稿")

    assert result.ok
    assert result.dry_run
    assert "テスト投稿" in log.read_text(encoding="utf-8")
