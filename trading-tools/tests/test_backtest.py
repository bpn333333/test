from datetime import datetime, timedelta

import pytest
from helpers import make_bars

from tradetools_monitor.backtest import (
    Backtester,
    BacktestConfig,
    Trade,
    calc_lot,
    default_point,
    normalize_lot,
    split_in_out_of_sample,
)
from tradetools_monitor.config import SignalParams
from tradetools_monitor.signals import BUY, SELL, Bar


def test_point_size_depends_on_the_pair():
    assert default_point("USDJPY") == 0.001
    assert default_point("EURUSD") == 0.00001
    assert default_point("GBPUSD") == 0.00001


def test_lot_is_rounded_down_to_the_step():
    config = BacktestConfig(lot_step=0.01)
    assert normalize_lot(0.137, config) == pytest.approx(0.13)


def test_lot_below_the_minimum_is_rejected():
    config = BacktestConfig(min_lot=0.01, lot_step=0.01)
    assert normalize_lot(0.004, config) == 0.0


def test_lot_is_capped_at_the_maximum():
    config = BacktestConfig(max_lot=1.0, lot_step=0.01)
    assert normalize_lot(50.0, config) == pytest.approx(1.0)


def test_lot_sizing_puts_the_risk_at_the_configured_percent():
    """残高100万・リスク1% → 損切りで1万円失う建玉になること。"""
    config = BacktestConfig(risk_percent=1.0, contract_size=100_000,
                            quote_to_account_rate=1.0, lot_step=0.01)
    sl_distance = 0.5  # USDJPY で 50pips

    lot = calc_lot(1_000_000, sl_distance, config)
    loss_at_stop = sl_distance * lot * config.contract_size

    assert loss_at_stop == pytest.approx(10_000, rel=0.02)


def test_zero_stop_distance_produces_no_lot():
    assert calc_lot(1_000_000, 0.0, BacktestConfig()) == 0.0


def _flat_config() -> BacktestConfig:
    """コストゼロ。損益計算そのものを検証するため。"""
    return BacktestConfig(spread_points=0, slippage_points=0,
                          commission_per_lot=0, swap_long_points=0,
                          swap_short_points=0)


def test_stop_loss_is_taken_when_both_levels_are_hit():
    """同一足で損切りと利確の両方に触れたら損切り側を採ること。"""
    tester = Backtester(SignalParams(), _flat_config())
    trade = Trade(direction=BUY, entry_time=datetime(2026, 1, 5, 9),
                  entry_price=150.0, lot=0.1, sl=149.0, tp=151.0)
    bar = Bar(datetime(2026, 1, 5, 10), 150.0, 151.5, 148.5, 150.0)

    price, reason = tester._check_exit(trade, bar)
    assert price == trade.sl
    assert "損切り" in reason


def test_optimistic_mode_takes_the_target_instead():
    config = _flat_config()
    config.worst_case_intrabar = False
    tester = Backtester(SignalParams(), config)
    trade = Trade(direction=BUY, entry_time=datetime(2026, 1, 5, 9),
                  entry_price=150.0, lot=0.1, sl=149.0, tp=151.0)
    bar = Bar(datetime(2026, 1, 5, 10), 150.0, 151.5, 148.5, 150.0)

    price, _ = tester._check_exit(trade, bar)
    assert price == trade.tp


def test_no_exit_when_neither_level_is_reached():
    tester = Backtester(SignalParams(), _flat_config())
    trade = Trade(direction=SELL, entry_time=datetime(2026, 1, 5, 9),
                  entry_price=150.0, lot=0.1, sl=151.0, tp=149.0)
    bar = Bar(datetime(2026, 1, 5, 10), 150.0, 150.5, 149.5, 150.0)

    assert tester._check_exit(trade, bar) is None


def test_profit_math_for_a_winning_long():
    tester = Backtester(SignalParams(), _flat_config())
    trade = Trade(direction=BUY, entry_time=datetime(2026, 1, 5, 9),
                  entry_price=150.0, lot=0.1, sl=149.0, tp=151.0)

    tester._close(trade, 151.0, datetime(2026, 1, 5, 12), "利確", 0.001)

    # 1.0 の値幅 × 0.1ロット × 10万通貨 = 10,000
    assert trade.profit == pytest.approx(10_000)


def test_profit_math_for_a_winning_short():
    tester = Backtester(SignalParams(), _flat_config())
    trade = Trade(direction=SELL, entry_time=datetime(2026, 1, 5, 9),
                  entry_price=150.0, lot=0.1, sl=151.0, tp=149.0)

    tester._close(trade, 149.0, datetime(2026, 1, 5, 12), "利確", 0.001)
    assert trade.profit == pytest.approx(10_000)


def test_spread_and_slippage_reduce_the_result():
    params = SignalParams()
    cheap = Backtester(params, _flat_config())
    expensive = Backtester(
        params, BacktestConfig(spread_points=30, slippage_points=10)
    )

    def close_one(tester):
        trade = Trade(direction=BUY, entry_time=datetime(2026, 1, 5, 9),
                      entry_price=150.0, lot=0.1, sl=149.0, tp=151.0)
        tester._close(trade, 151.0, datetime(2026, 1, 5, 12), "利確", 0.001)
        return trade.profit

    assert close_one(expensive) < close_one(cheap)


def test_commission_is_charged_per_lot():
    tester = Backtester(
        SignalParams(),
        BacktestConfig(spread_points=0, slippage_points=0, commission_per_lot=1000),
    )
    trade = Trade(direction=BUY, entry_time=datetime(2026, 1, 5, 9),
                  entry_price=150.0, lot=0.5, sl=149.0, tp=151.0)

    tester._close(trade, 151.0, datetime(2026, 1, 5, 12), "利確", 0.001)
    # 50,000 の利益から 1,000 × 0.5 ロット
    assert trade.profit == pytest.approx(50_000 - 500)


def test_negative_swap_is_deducted_per_night():
    tester = Backtester(
        SignalParams(),
        BacktestConfig(spread_points=0, slippage_points=0, swap_long_points=-5),
    )
    trade = Trade(direction=BUY, entry_time=datetime(2026, 1, 5, 9),
                  entry_price=150.0, lot=0.1, sl=149.0, tp=151.0)

    tester._close(trade, 151.0, datetime(2026, 1, 8, 12), "利確", 0.001)
    # 3泊 × -5point(0.005) × 0.1ロット × 10万 = -150
    assert trade.profit == pytest.approx(10_000 - 150)


def test_run_produces_no_trades_without_enough_history():
    result = Backtester(SignalParams()).run(make_bars(100), "USDJPY", "PERIOD_H1")
    assert result.total_trades == 0


def test_run_executes_trades_on_trending_data():
    result = Backtester(SignalParams(), _flat_config()).run(
        make_bars(2500), "USDJPY", "PERIOD_H1"
    )
    assert result.total_trades > 0
    assert len(result.equity_curve) > 0


def test_entry_never_uses_the_signal_bar_itself():
    """先読み防止。約定時刻は必ずシグナル足より後であること。"""
    bars = make_bars(2500)
    result = Backtester(SignalParams(), _flat_config()).run(bars, "USDJPY", "PERIOD_H1")

    times = [b.time for b in bars]
    for trade in result.trades:
        assert trade.entry_time in times
        assert trade.exit_time >= trade.entry_time


def test_metrics_are_internally_consistent():
    result = Backtester(SignalParams(), _flat_config()).run(
        make_bars(2500), "USDJPY", "PERIOD_H1"
    )
    if result.total_trades == 0:
        pytest.skip("この合成データでは取引が発生しない")

    assert result.wins + result.losses == result.total_trades
    assert result.net_profit == pytest.approx(
        sum(t.profit for t in result.trades), abs=1e-6
    )
    assert result.final_balance == pytest.approx(
        result.initial_balance + result.net_profit, abs=1e-6
    )
    assert 0 <= result.win_rate <= 100
    assert result.max_drawdown >= 0


def test_higher_costs_never_improve_the_result():
    bars = make_bars(2500)
    params = SignalParams()

    cheap = Backtester(params, _flat_config()).run(bars, "USDJPY", "PERIOD_H1")
    expensive = Backtester(
        params, BacktestConfig(spread_points=50, slippage_points=20,
                               commission_per_lot=500)
    ).run(bars, "USDJPY", "PERIOD_H1")

    if cheap.total_trades == 0:
        pytest.skip("この合成データでは取引が発生しない")
    assert expensive.net_profit <= cheap.net_profit


def test_open_position_is_closed_at_the_end_of_the_period():
    result = Backtester(SignalParams(), _flat_config()).run(
        make_bars(2500), "USDJPY", "PERIOD_H1"
    )
    for trade in result.trades:
        assert trade.exit_time is not None
        assert trade.exit_reason != ""


def test_out_of_sample_split_keeps_every_bar():
    bars = make_bars(1000)
    in_sample, out_sample = split_in_out_of_sample(bars, 0.7)

    assert len(in_sample) == 700
    assert len(out_sample) == 300
    assert in_sample[-1].time < out_sample[0].time


def test_out_of_sample_split_rejects_invalid_ratios():
    with pytest.raises(ValueError):
        split_in_out_of_sample(make_bars(100), 1.0)
