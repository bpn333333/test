import math

import pytest

from tradetools_monitor.indicators import adx, atr, ema, true_range


def test_ema_warmup_is_none_until_period():
    values = [float(i) for i in range(1, 21)]
    result = ema(values, 5)

    assert result[:4] == [None] * 4
    # 最初の確定値は SMA(5) = (1+2+3+4+5)/5
    assert result[4] == pytest.approx(3.0)


def test_ema_follows_recursive_formula():
    values = [float(i) for i in range(1, 21)]
    period = 5
    alpha = 2 / (period + 1)
    result = ema(values, period)

    expected = 3.0
    for value in values[period:]:
        expected = value * alpha + expected * (1 - alpha)
    assert result[-1] == pytest.approx(expected)


def test_ema_constant_series_equals_constant():
    result = ema([7.5] * 50, 10)
    assert result[-1] == pytest.approx(7.5)


def test_ema_too_short_returns_all_none():
    assert ema([1.0, 2.0], 10) == [None, None]


def test_true_range_uses_previous_close():
    highs = [10.0, 12.0]
    lows = [9.0, 11.5]
    closes = [9.5, 11.8]

    # max(12-11.5, |12-9.5|, |11.5-9.5|) = 2.5
    assert true_range(highs, lows, closes)[1] == pytest.approx(2.5)


def test_atr_constant_range_equals_range():
    count = 60
    closes = [100.0] * count
    highs = [100.5] * count
    lows = [99.5] * count

    result = atr(highs, lows, closes, 14)
    assert result[-1] == pytest.approx(1.0)


def test_atr_modes_agree_on_constant_input():
    count = 60
    closes = [100.0] * count
    highs = [101.0] * count
    lows = [99.0] * count

    mt5_mode = atr(highs, lows, closes, 14, "mt5")[-1]
    wilder_mode = atr(highs, lows, closes, 14, "wilder")[-1]
    assert mt5_mode == pytest.approx(wilder_mode)


def test_atr_rejects_unknown_mode():
    with pytest.raises(ValueError):
        atr([1.0], [1.0], [1.0], 14, "unknown")


def test_adx_is_high_on_a_clean_trend():
    count = 120
    closes = [100.0 + i for i in range(count)]
    highs = [c + 0.5 for c in closes]
    lows = [c - 0.5 for c in closes]

    value = adx(highs, lows, closes, 14)[-1]
    assert value is not None
    assert value > 60  # 一方向にしか動いていないので非常に高くなる


def test_adx_is_low_in_a_range():
    count = 300
    closes = [100.0 + math.sin(i / 2) for i in range(count)]
    highs = [c + 0.2 for c in closes]
    lows = [c - 0.2 for c in closes]

    value = adx(highs, lows, closes, 14)[-1]
    assert value is not None
    assert value < 30


def test_adx_returns_none_when_history_is_short():
    assert adx([1.0] * 10, [1.0] * 10, [1.0] * 10, 14) == [None] * 10
