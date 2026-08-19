from datetime import datetime, timedelta

import pytest
from helpers import make_bars, make_flat_bars

from tradetools_monitor.config import SignalParams
from tradetools_monitor.signals import BUY, NONE, SELL, Bar, evaluate, in_session, scan


def test_params_validate_rejects_inverted_emas():
    params = SignalParams(ema_fast=50, ema_slow=20)
    with pytest.raises(ValueError):
        params.validate()


def test_params_validate_rejects_inverted_session():
    with pytest.raises(ValueError):
        SignalParams(session_start_hour=22, session_end_hour=8).validate()


def test_warmup_matches_mql_formula():
    params = SignalParams()
    assert params.warmup_bars == max(200, 48, 14, 14) * 3 + 10


def test_in_session_blocks_weekend():
    params = SignalParams()
    saturday = datetime(2026, 1, 10, 10, 0)
    ok, why = in_session(saturday, params)
    assert not ok
    assert "週末" in why


def test_in_session_blocks_outside_hours():
    params = SignalParams()
    ok, why = in_session(datetime(2026, 1, 5, 3, 0), params)
    assert not ok
    assert "時間帯外" in why


def test_in_session_blocks_friday_evening():
    params = SignalParams()
    friday_late = datetime(2026, 1, 9, 21, 0)
    ok, why = in_session(friday_late, params)
    assert not ok
    assert "金曜" in why


def test_in_session_allows_friday_before_cutoff():
    params = SignalParams()
    ok, why = in_session(datetime(2026, 1, 9, 15, 0), params)
    assert ok
    assert why == ""


def test_evaluate_returns_none_before_warmup():
    params = SignalParams()
    bars = make_bars(100)
    assert evaluate(bars, params, "USDJPY", "PERIOD_H1") is None


def test_evaluate_reports_range_market_as_no_signal():
    params = SignalParams()
    bars = make_flat_bars(params.warmup_bars + 50)
    signal = evaluate(bars, params, "USDJPY", "PERIOD_H1")

    assert signal is not None
    assert signal.direction == NONE
    assert "ATR" in signal.reason or "ADX" in signal.reason


def test_scan_finds_signals_on_trending_data():
    params = SignalParams()
    signals = scan(make_bars(2000), params, "USDJPY", "PERIOD_H1")

    assert signals, "トレンドのある合成データでシグナルが1件も出ないのはおかしい"
    assert all(s.direction in (BUY, SELL) for s in signals)


def test_signal_levels_respect_risk_reward():
    params = SignalParams()
    signals = scan(make_bars(2000), params, "USDJPY", "PERIOD_H1")

    for signal in signals:
        assert signal.risk_reward == pytest.approx(params.rr_ratio, abs=1e-6)
        risk = abs(signal.price - signal.sl)
        assert risk == pytest.approx(signal.atr * params.sl_atr_mult, abs=1e-9)


def test_buy_places_stop_below_and_target_above():
    params = SignalParams()
    for signal in scan(make_bars(2000), params, "USDJPY", "PERIOD_H1"):
        if signal.direction == BUY:
            assert signal.sl < signal.price < signal.tp
        else:
            assert signal.tp < signal.price < signal.sl


def test_all_signals_land_inside_the_session():
    params = SignalParams()
    for signal in scan(make_bars(2000), params, "USDJPY", "PERIOD_H1"):
        ok, _ = in_session(signal.time, params)
        assert ok, f"時間帯外のシグナルが出ています: {signal.time}"


def test_signal_id_matches_mql_format():
    params = SignalParams()
    signals = scan(make_bars(2000), params, "USDJPY", "PERIOD_H1")
    signal = signals[0]

    expected = (
        f"USDJPY-PERIOD_H1-{signal.time:%Y.%m.%d %H:%M}-{signal.direction}"
    )
    assert signal.signal_id == expected


def test_raising_adx_threshold_reduces_signals():
    loose = scan(make_bars(2000), SignalParams(adx_min=0.0), "USDJPY", "PERIOD_H1")
    strict = scan(make_bars(2000), SignalParams(adx_min=60.0), "USDJPY", "PERIOD_H1")
    assert len(strict) <= len(loose)


def test_trend_filter_blocks_counter_trend_cross():
    """下降トレンド中の上抜けは見送られること。"""
    params = SignalParams()
    count = params.warmup_bars + 200
    start = datetime(2026, 1, 5, 9, 0)

    bars = []
    for i in range(count):
        # 一貫した下降。最後の数本だけ跳ね上げてクロスを作る
        close = 200.0 - i * 0.05
        if i >= count - 6:
            close += (i - (count - 7)) * 0.9
        bars.append(Bar(start + timedelta(hours=i), close, close + 0.2, close - 0.2, close))

    signal = evaluate(bars, params, "USDJPY", "PERIOD_H1")
    assert signal is not None
    assert signal.direction == NONE
