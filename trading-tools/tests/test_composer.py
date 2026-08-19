from datetime import datetime

import pytest

from tradetools_monitor.signals import Signal
from tradetools_x.composer import (
    DEFAULT_DISCLAIMER,
    MAX_WEIGHTED_LENGTH,
    Post,
    compose_daily_summary,
    compose_signal_post,
    find_prohibited,
    weighted_length,
)


def make_signal(direction="BUY", symbol="USDJPY", reason="EMA12/48 上抜け・ADX 30.0"):
    return Signal(
        direction=direction,
        time=datetime(2026, 2, 11, 18, 0),
        symbol=symbol,
        timeframe="PERIOD_H1",
        price=157.533,
        sl=156.900 if direction == "BUY" else 158.200,
        tp=158.700 if direction == "BUY" else 156.400,
        atr=0.42,
        adx=30.0,
        reason=reason,
    )


def test_weighted_length_counts_ascii_as_one():
    assert weighted_length("abcde") == 5


def test_weighted_length_counts_japanese_as_two():
    assert weighted_length("あいう") == 6


def test_weighted_length_counts_url_as_fixed_23():
    assert weighted_length("https://example.com/very/long/path/indeed") == 23


def test_prohibited_expressions_are_detected():
    assert find_prohibited("必ず儲かります")
    assert find_prohibited("元本保証です")
    assert find_prohibited("勝率100%")
    assert find_prohibited("これは絶対に勝てる") 


def test_neutral_text_passes_the_filter():
    assert find_prohibited("シグナルが出ました。判断はご自身で。") == []


def test_signal_post_contains_the_essentials():
    post = compose_signal_post(make_signal())

    assert "USD/JPY" in post.text
    assert "1時間足" in post.text
    assert "買い" in post.text
    assert "157.533" in post.text
    assert DEFAULT_DISCLAIMER in post.text


def test_signal_post_fits_the_character_limit():
    long_reason = "非常に長い根拠テキスト" * 20
    post = compose_signal_post(make_signal(reason=long_reason))

    assert weighted_length(post.text) <= MAX_WEIGHTED_LENGTH
    assert DEFAULT_DISCLAIMER in post.text  # 削るのは根拠であって免責ではない


def test_sell_post_uses_sell_wording():
    post = compose_signal_post(make_signal(direction="SELL"))
    assert "売り" in post.text


def test_levels_can_be_hidden():
    post = compose_signal_post(make_signal(), show_levels=False)
    assert "損切" not in post.text


def test_non_jpy_pairs_use_five_decimals():
    signal = make_signal(symbol="EURUSD")
    signal.price = 1.08421
    signal.sl = 1.08100
    signal.tp = 1.09000
    post = compose_signal_post(signal)
    assert "1.08421" in post.text


def test_post_without_disclaimer_is_rejected():
    post = Post(text="USD/JPY 買いシグナル", signal_id="x")
    with pytest.raises(ValueError, match="免責"):
        post.validate()


def test_post_with_prohibited_expression_is_rejected():
    post = Post(text=f"必ず儲かります\n{DEFAULT_DISCLAIMER}", signal_id="x")
    with pytest.raises(ValueError, match="禁止表現"):
        post.validate()


def test_overlong_post_is_rejected():
    post = Post(text="あ" * 300 + DEFAULT_DISCLAIMER, signal_id="x")
    with pytest.raises(ValueError, match="文字数超過"):
        post.validate()


def test_empty_summary_returns_none():
    assert compose_daily_summary([], "2026-02-11") is None


def test_summary_counts_directions():
    signals = [make_signal("BUY"), make_signal("SELL"), make_signal("BUY", "EURUSD")]
    post = compose_daily_summary(signals, "2026-02-11")

    assert post is not None
    assert "検出 3件" in post.text
    assert "買い 2" in post.text
    assert DEFAULT_DISCLAIMER in post.text
