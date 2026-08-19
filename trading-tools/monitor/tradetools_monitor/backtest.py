"""バックテストエンジン。

ロジックの採否を判定するための検証。EA と同じ判定(signals.evaluate)を使い、
取引コストを明示的に差し引く。

設計上の約束:
 - **先読みをしない。** 確定足 i の終値で判定し、エントリーは足 i+1 の始値。
 - **同一足で損切りと利確の両方に触れた場合は損切りを優先する**(最悪ケース)。
   OHLC しか無い以上どちらが先か判定できないため、悲観側に倒す。
 - スプレッド・スリッページ・手数料・スワップをすべて差し引く。
   コストを入れない検証結果は使わない。
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import List, Optional, Sequence

from .config import SignalParams
from .signals import BUY, NONE, SELL, Bar, compute_indicators, evaluate


def default_point(symbol: str) -> float:
    """1 point の価格幅。円絡みは3桁、それ以外は5桁が一般的。"""
    return 0.001 if "JPY" in symbol.upper() else 0.00001


@dataclass
class BacktestConfig:
    """取引条件。ブローカーの実際の条件に合わせること。"""

    initial_balance: float = 1_000_000.0   # 口座通貨での初期残高
    risk_percent: float = 1.0              # 1トレードのリスク(残高比%)

    spread_points: float = 10.0            # 平均スプレッド(point)
    slippage_points: float = 2.0           # 片道スリッページ(point)
    commission_per_lot: float = 0.0        # 往復手数料(口座通貨 / 1ロット)
    swap_long_points: float = 0.0          # 買い建ての1泊あたりスワップ(point)
    swap_short_points: float = 0.0         # 売り建ての1泊あたりスワップ(point)

    contract_size: float = 100_000.0       # 1ロットの通貨単位
    point: Optional[float] = None          # 省略時は銘柄名から決める
    quote_to_account_rate: float = 1.0     # 決済通貨→口座通貨の換算レート

    min_lot: float = 0.01
    max_lot: float = 100.0
    lot_step: float = 0.01

    close_on_opposite: bool = True         # 逆シグナルで決済(EAの既定と同じ)
    worst_case_intrabar: bool = True       # 同一足で両方に触れたら損切り優先

    def resolved_point(self, symbol: str) -> float:
        return self.point if self.point is not None else default_point(symbol)


@dataclass
class Trade:
    direction: str
    entry_time: datetime
    entry_price: float
    exit_time: Optional[datetime] = None
    exit_price: float = 0.0
    lot: float = 0.0
    sl: float = 0.0
    tp: float = 0.0
    profit: float = 0.0        # 手数料・スワップ込みの口座通貨建て損益
    exit_reason: str = ""
    bars_held: int = 0

    @property
    def is_win(self) -> bool:
        return self.profit > 0


@dataclass
class BacktestResult:
    symbol: str
    timeframe: str
    period_start: Optional[datetime]
    period_end: Optional[datetime]
    initial_balance: float
    final_balance: float
    trades: List[Trade] = field(default_factory=list)
    equity_curve: List[float] = field(default_factory=list)

    # 集計
    total_trades: int = 0
    wins: int = 0
    losses: int = 0
    win_rate: float = 0.0
    gross_profit: float = 0.0
    gross_loss: float = 0.0
    net_profit: float = 0.0
    profit_factor: float = 0.0
    expectancy: float = 0.0
    max_drawdown: float = 0.0
    max_drawdown_percent: float = 0.0
    recovery_factor: float = 0.0
    return_percent: float = 0.0
    max_consecutive_losses: int = 0
    average_win: float = 0.0
    average_loss: float = 0.0
    largest_win: float = 0.0
    largest_loss: float = 0.0

    def summary(self) -> str:
        period = "—"
        if self.period_start and self.period_end:
            period = f"{self.period_start:%Y-%m-%d} 〜 {self.period_end:%Y-%m-%d}"
        return "\n".join([
            f"銘柄:            {self.symbol} {self.timeframe}",
            f"期間:            {period}",
            f"取引数:          {self.total_trades}",
            f"勝率:            {self.win_rate:.1f}%  ({self.wins}勝 {self.losses}敗)",
            f"純損益:          {self.net_profit:,.0f}",
            f"収益率:          {self.return_percent:.1f}%",
            f"プロフィットファクター: {self.profit_factor:.2f}",
            f"期待値/取引:     {self.expectancy:,.0f}",
            f"最大ドローダウン: {self.max_drawdown:,.0f} ({self.max_drawdown_percent:.1f}%)",
            f"リカバリーファクター: {self.recovery_factor:.2f}",
            f"最大連敗:        {self.max_consecutive_losses}",
            f"平均利益/平均損失: {self.average_win:,.0f} / {self.average_loss:,.0f}",
            f"最大利益/最大損失: {self.largest_win:,.0f} / {self.largest_loss:,.0f}",
            f"最終残高:        {self.final_balance:,.0f}",
        ])

    def to_dict(self) -> dict:
        data = asdict(self)
        data["trades"] = [
            {
                **{k: v for k, v in asdict(t).items()
                   if k not in ("entry_time", "exit_time")},
                "entry_time": t.entry_time.isoformat() if t.entry_time else None,
                "exit_time": t.exit_time.isoformat() if t.exit_time else None,
            }
            for t in self.trades
        ]
        data["period_start"] = self.period_start.isoformat() if self.period_start else None
        data["period_end"] = self.period_end.isoformat() if self.period_end else None
        return data


def normalize_lot(lot: float, config: BacktestConfig) -> float:
    """ロットステップに丸める。最小ロット未満は0(=発注しない)。"""
    if config.lot_step <= 0:
        return 0.0
    steps = int(lot / config.lot_step)
    normalized = steps * config.lot_step
    if normalized < config.min_lot:
        return 0.0
    return round(min(normalized, config.max_lot), 8)


def calc_lot(balance: float, sl_distance: float, config: BacktestConfig) -> float:
    """損切り距離とリスク%からロットを逆算する。EA の RiskManager と同じ考え方。"""
    if sl_distance <= 0:
        return 0.0
    value_per_price_unit = config.contract_size * config.quote_to_account_rate
    if value_per_price_unit <= 0:
        return 0.0
    risk_amount = balance * config.risk_percent / 100.0
    return normalize_lot(risk_amount / (sl_distance * value_per_price_unit), config)


class Backtester:
    def __init__(self, params: SignalParams, config: Optional[BacktestConfig] = None) -> None:
        self.params = params
        self.config = config or BacktestConfig()

    # --- 内部計算 -------------------------------------------------------

    def _money(self, price_diff: float, lot: float) -> float:
        return price_diff * lot * self.config.contract_size * self.config.quote_to_account_rate

    def _costs(self, trade: Trade, point: float) -> float:
        """手数料とスワップ。いずれも損失側に効く。"""
        commission = self.config.commission_per_lot * trade.lot

        nights = 0
        if trade.exit_time and trade.entry_time:
            nights = max(0, (trade.exit_time.date() - trade.entry_time.date()).days)
        swap_points = (self.config.swap_long_points if trade.direction == BUY
                       else self.config.swap_short_points)
        swap = self._money(swap_points * point * nights, trade.lot)

        return commission - swap  # swap は符号付き。プラスなら受取

    def _close(self, trade: Trade, price: float, when: datetime, reason: str,
               point: float) -> None:
        slip = self.config.slippage_points * point
        spread = self.config.spread_points * point

        if trade.direction == BUY:
            # 決済は Bid。約定は不利側にずれる
            exit_price = price - slip
            gross = self._money(exit_price - trade.entry_price, trade.lot)
        else:
            # 売りの決済は Ask = Bid + スプレッド
            exit_price = price + spread + slip
            gross = self._money(trade.entry_price - exit_price, trade.lot)

        trade.exit_price = exit_price
        trade.exit_time = when
        trade.exit_reason = reason
        trade.profit = gross - self._costs(trade, point)

    def _open(self, direction: str, bar: Bar, sl_distance: float, balance: float,
              point: float) -> Optional[Trade]:
        spread = self.config.spread_points * point
        slip = self.config.slippage_points * point

        if direction == BUY:
            entry = bar.open + spread + slip   # 買いは Ask で入る
            sl = entry - sl_distance
            tp = entry + sl_distance * self.params.rr_ratio
        else:
            entry = bar.open - slip            # 売りは Bid で入る
            sl = entry + sl_distance
            tp = entry - sl_distance * self.params.rr_ratio

        lot = calc_lot(balance, sl_distance, self.config)
        if lot <= 0:
            return None

        return Trade(direction=direction, entry_time=bar.time, entry_price=entry,
                     lot=lot, sl=sl, tp=tp)

    def _check_exit(self, trade: Trade, bar: Bar) -> Optional[tuple[float, str]]:
        """この足で決済されるか。決済価格と理由を返す。"""
        hit_sl = bar.low <= trade.sl if trade.direction == BUY else bar.high >= trade.sl
        hit_tp = bar.high >= trade.tp if trade.direction == BUY else bar.low <= trade.tp

        if hit_sl and hit_tp:
            # どちらが先か OHLC からは判定できない。悲観側に倒す
            if self.config.worst_case_intrabar:
                return trade.sl, "損切り(同一足で両方到達)"
            return trade.tp, "利確(同一足で両方到達)"
        if hit_sl:
            return trade.sl, "損切り"
        if hit_tp:
            return trade.tp, "利確"
        return None

    # --- 実行 -----------------------------------------------------------

    def run(self, bars: Sequence[Bar], symbol: str, timeframe: str) -> BacktestResult:
        point = self.config.resolved_point(symbol)
        balance = self.config.initial_balance

        result = BacktestResult(
            symbol=symbol,
            timeframe=timeframe,
            period_start=bars[0].time if bars else None,
            period_end=bars[-1].time if bars else None,
            initial_balance=balance,
            final_balance=balance,
        )

        if len(bars) <= self.params.warmup_bars + 1:
            return _finalize(result, balance)

        indicators = compute_indicators(bars, self.params)
        open_trade: Optional[Trade] = None
        pending: Optional[tuple[str, float]] = None  # 次の足の始値で建てる指示

        for i in range(self.params.warmup_bars, len(bars)):
            bar = bars[i]

            # 1) 保有中なら、まずこの足で決済されるかを見る
            if open_trade is not None:
                exit_info = self._check_exit(open_trade, bar)
                if exit_info is not None:
                    price, reason = exit_info
                    self._close(open_trade, price, bar.time, reason, point)
                    open_trade.bars_held = i - _index_of(bars, open_trade.entry_time, i)
                    balance += open_trade.profit
                    result.trades.append(open_trade)
                    open_trade = None

            # 2) 前の足で出した指示をこの足の始値で執行する(先読み防止)
            if pending is not None and open_trade is None:
                direction, sl_distance = pending
                open_trade = self._open(direction, bar, sl_distance, balance, point)
            pending = None

            result.equity_curve.append(balance)

            # 3) この足の終値で判定し、指示は次の足へ回す
            signal = evaluate(bars, self.params, symbol, timeframe, i, indicators)
            if signal is None or signal.direction == NONE:
                continue

            if open_trade is not None:
                opposite = (
                    (signal.direction == BUY and open_trade.direction == SELL)
                    or (signal.direction == SELL and open_trade.direction == BUY)
                )
                if opposite and self.config.close_on_opposite and i + 1 < len(bars):
                    next_bar = bars[i + 1]
                    self._close(open_trade, next_bar.open, next_bar.time, "逆シグナル", point)
                    open_trade.bars_held = i + 1 - _index_of(bars, open_trade.entry_time, i)
                    balance += open_trade.profit
                    result.trades.append(open_trade)
                    open_trade = None
                else:
                    continue

            pending = (signal.direction, abs(signal.price - signal.sl))

        # 期間末に残っているポジションは最終足の終値で強制決済する
        if open_trade is not None:
            last = bars[-1]
            self._close(open_trade, last.close, last.time, "期間終了", point)
            balance += open_trade.profit
            result.trades.append(open_trade)

        return _finalize(result, balance)


def _index_of(bars: Sequence[Bar], when: datetime, upper: int) -> int:
    for i in range(upper, -1, -1):
        if bars[i].time == when:
            return i
    return upper


def _finalize(result: BacktestResult, balance: float) -> BacktestResult:
    result.final_balance = balance
    trades = result.trades
    result.total_trades = len(trades)

    if not trades:
        return result

    wins = [t for t in trades if t.is_win]
    losses = [t for t in trades if not t.is_win]

    result.wins = len(wins)
    result.losses = len(losses)
    result.win_rate = 100.0 * len(wins) / len(trades)
    result.gross_profit = sum(t.profit for t in wins)
    result.gross_loss = abs(sum(t.profit for t in losses))
    result.net_profit = result.gross_profit - result.gross_loss
    result.profit_factor = (result.gross_profit / result.gross_loss
                            if result.gross_loss > 0 else float("inf"))
    result.expectancy = result.net_profit / len(trades)
    result.average_win = result.gross_profit / len(wins) if wins else 0.0
    result.average_loss = result.gross_loss / len(losses) if losses else 0.0
    result.largest_win = max((t.profit for t in wins), default=0.0)
    result.largest_loss = min((t.profit for t in losses), default=0.0)
    result.return_percent = (100.0 * result.net_profit / result.initial_balance
                             if result.initial_balance else 0.0)

    # 最大ドローダウンは確定損益ベースの残高推移から取る
    equity = result.initial_balance
    peak = equity
    max_dd = 0.0
    max_dd_pct = 0.0
    streak = 0
    worst_streak = 0

    for trade in trades:
        equity += trade.profit
        peak = max(peak, equity)
        drawdown = peak - equity
        if drawdown > max_dd:
            max_dd = drawdown
            max_dd_pct = 100.0 * drawdown / peak if peak else 0.0

        if trade.is_win:
            streak = 0
        else:
            streak += 1
            worst_streak = max(worst_streak, streak)

    result.max_drawdown = max_dd
    result.max_drawdown_percent = max_dd_pct
    result.max_consecutive_losses = worst_streak
    result.recovery_factor = result.net_profit / max_dd if max_dd > 0 else float("inf")
    return result


def split_in_out_of_sample(bars: Sequence[Bar], in_sample_ratio: float = 0.7
                           ) -> tuple[List[Bar], List[Bar]]:
    """最適化に使う期間と、使わない期間に分ける。

    アウトオブサンプル側の成績が崩れるロジックは過剰最適化。
    """
    if not 0 < in_sample_ratio < 1:
        raise ValueError("in_sample_ratio は0と1の間です")
    cut = int(len(bars) * in_sample_ratio)
    return list(bars[:cut]), list(bars[cut:])


# --- CLI ---------------------------------------------------------------

DEFAULT_SYMBOLS = ("USDJPY", "EURUSD", "GBPUSD")


def _load_config_file(path: Optional[str]) -> tuple[SignalParams, BacktestConfig]:
    if not path:
        return SignalParams(), BacktestConfig()

    from pathlib import Path
    raw = json.loads(Path(path).expanduser().read_text(encoding="utf-8"))
    params = SignalParams(**raw.get("params", {}))
    config = BacktestConfig(**raw.get("backtest", {}))
    params.validate()
    return params, config


def main(argv: Optional[Sequence[str]] = None) -> int:
    import argparse
    from pathlib import Path

    from .sources import read_ohlc_csv

    parser = argparse.ArgumentParser(description="TradeTools バックテスト")
    parser.add_argument("--data-dir", default="data",
                        help="OHLC CSV の置き場(既定: data)")
    parser.add_argument("--symbols", nargs="+", default=list(DEFAULT_SYMBOLS),
                        help=f"対象銘柄(既定: {' '.join(DEFAULT_SYMBOLS)})")
    parser.add_argument("--timeframe", default="PERIOD_H1",
                        help="時間軸。<SYMBOL>_<TIMEFRAME>.csv を読む")
    parser.add_argument("--config", help="params と backtest を含む設定JSON")
    parser.add_argument("--oos", type=float, default=0.0,
                        help="アウトオブサンプル検証。イン側の比率(例 0.7)")
    parser.add_argument("--json", dest="json_out",
                        help="結果をJSONで書き出すパス")
    args = parser.parse_args(argv)

    try:
        params, config = _load_config_file(args.config)
    except (OSError, ValueError, TypeError) as error:
        print(f"設定の読み込みに失敗: {error}")
        return 2

    data_dir = Path(args.data_dir).expanduser()
    reports: dict = {}
    missing: List[str] = []

    for symbol in args.symbols:
        path = data_dir / f"{symbol}_{args.timeframe}.csv"
        if not path.exists():
            missing.append(str(path))
            continue

        bars = read_ohlc_csv(path)
        tester = Backtester(params, config)

        if args.oos > 0:
            in_sample, out_sample = split_in_out_of_sample(bars, args.oos)
            runs = {"in_sample": in_sample, "out_of_sample": out_sample}
        else:
            runs = {"full": list(bars)}

        reports[symbol] = {}
        for label, subset in runs.items():
            result = tester.run(subset, symbol, args.timeframe)
            reports[symbol][label] = result
            print(f"\n===== {symbol} / {label} =====")
            print(result.summary())

    if missing:
        print("\nデータが見つかりません:")
        for path in missing:
            print(f"  {path}")
        print("MT5 から time,open,high,low,close 形式で書き出してください。")

    if args.json_out and reports:
        payload = {
            symbol: {label: result.to_dict() for label, result in runs.items()}
            for symbol, runs in reports.items()
        }
        Path(args.json_out).expanduser().write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"\nJSON を書き出しました: {args.json_out}")

    return 0 if reports else 1


if __name__ == "__main__":
    raise SystemExit(main())
