//+------------------------------------------------------------------+
//| TradeToolsEA.mq5 — 自動売買EA                                     |
//| サインツールと完全に同じ判定(SignalCore.mqh)を使う。              |
//| ここが持つ責務は「発注・決済・保護」だけ。                          |
//+------------------------------------------------------------------+
#property copyright "TradeTools"
#property version   "1.00"

#include <Trade/Trade.mqh>
#include <TradeTools/SignalCore.mqh>
#include <TradeTools/RiskManager.mqh>
#include <TradeTools/SignalFile.mqh>

input group "シグナル判定(サインツールと同じ値にすること)"
input int    InpEmaFast      = 12;
input int    InpEmaSlow      = 48;
input int    InpEmaTrend     = 200;
input int    InpAdxPeriod    = 14;
input double InpAdxMin       = 20.0;
input int    InpAtrPeriod    = 14;
input double InpSlAtrMult    = 1.5;
input double InpRrRatio      = 1.8;

input group "時間帯フィルタ(サーバー時間)"
input int    InpSessionStart = 8;
input int    InpSessionEnd   = 22;
input bool   InpBlockFriday  = true;
input int    InpFridayCutoff = 20;

input group "資金管理"
input double InpRiskPercent  = 1.0;   // 1トレードのリスク(残高比%)
input double InpMaxLot       = 1.0;   // 上限ロット
input int    InpMaxPositions = 1;     // 同時保有数
input double InpMaxDailyLoss = 3.0;   // 当日損失の上限(%)。超えたら新規停止
input int    InpMaxSpread    = 30;    // 上限スプレッド(point)
input int    InpSlippage     = 20;    // 許容スリッページ(point)

input group "決済"
input bool   InpUseBreakEven = true;  // 含み益が損切り幅に達したら建値に移動
input bool   InpUseTrailing  = true;  // ATRトレーリング
input double InpTrailAtrMult = 2.0;   // トレール幅 = ATR × 倍率
input bool   InpCloseOnFlip  = true;  // 逆シグナルで決済する

input group "運用"
input long   InpMagic        = 20260819;  // マジックナンバー
input bool   InpWriteFile    = true;      // 約定シグナルをCSVに残す(配信・検証用)

CTrade         g_trade;
CTTSignalCore  g_core;
CTTRiskManager g_risk;
datetime       g_last_bar_time = 0;

int OnInit(void)
  {
   if(InpEmaFast >= InpEmaSlow)
     {
      Print("設定エラー: 短期EMAは長期EMAより小さくしてください");
      return(INIT_PARAMETERS_INCORRECT);
     }
   if(InpRiskPercent <= 0.0 || InpRiskPercent > 5.0)
     {
      Print("設定エラー: リスクは0より大きく5%以下にしてください(実際は1%前後を推奨)");
      return(INIT_PARAMETERS_INCORRECT);
     }

   TTSignalParams p;
   p.ema_fast           = InpEmaFast;
   p.ema_slow           = InpEmaSlow;
   p.ema_trend          = InpEmaTrend;
   p.adx_period         = InpAdxPeriod;
   p.adx_min            = InpAdxMin;
   p.atr_period         = InpAtrPeriod;
   p.sl_atr_mult        = InpSlAtrMult;
   p.rr_ratio           = InpRrRatio;
   p.session_start_hour = InpSessionStart;
   p.session_end_hour   = InpSessionEnd;
   p.block_friday_late  = InpBlockFriday;
   p.friday_cutoff_hour = InpFridayCutoff;

   if(!g_core.Init(_Symbol, (ENUM_TIMEFRAMES)_Period, p))
      return(INIT_FAILED);

   TTRiskParams r;
   r.risk_percent       = InpRiskPercent;
   r.max_lot            = InpMaxLot;
   r.max_positions      = InpMaxPositions;
   r.max_daily_loss_pct = InpMaxDailyLoss;
   r.max_spread_points  = InpMaxSpread;
   r.slippage_points    = InpSlippage;
   g_risk.Init(_Symbol, InpMagic, r);

   g_trade.SetExpertMagicNumber(InpMagic);
   g_trade.SetDeviationInPoints(InpSlippage);
   g_trade.SetTypeFillingBySymbol(_Symbol);
   g_trade.SetAsyncMode(false);

   return(INIT_SUCCEEDED);
  }

void OnDeinit(const int reason)
  {
   g_core.Deinit();
  }

//--- 建値移動とトレーリング。毎ティック回すが、実際の変更は必要なときだけ
void ManageOpenPositions(void)
  {
   if(!InpUseBreakEven && !InpUseTrailing)
      return;

   TTSignal current;
   if(!g_core.Evaluate(1, current) || current.atr <= 0.0)
      return;

   int    digits = (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS);
   double point  = SymbolInfoDouble(_Symbol, SYMBOL_POINT);
   long   stops_level = SymbolInfoInteger(_Symbol, SYMBOL_TRADE_STOPS_LEVEL);
   double min_distance = stops_level * point;

   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      ulong ticket = PositionGetTicket(i);
      if(ticket == 0)
         continue;
      if(PositionGetString(POSITION_SYMBOL) != _Symbol)
         continue;
      if(PositionGetInteger(POSITION_MAGIC) != InpMagic)
         continue;

      long   type       = PositionGetInteger(POSITION_TYPE);
      double open_price = PositionGetDouble(POSITION_PRICE_OPEN);
      double cur_sl     = PositionGetDouble(POSITION_SL);
      double cur_tp     = PositionGetDouble(POSITION_TP);
      double bid        = SymbolInfoDouble(_Symbol, SYMBOL_BID);
      double ask        = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
      double new_sl     = cur_sl;

      double risk_distance = current.atr * InpSlAtrMult;

      if(type == POSITION_TYPE_BUY)
        {
         if(InpUseBreakEven && bid - open_price >= risk_distance && cur_sl < open_price)
            new_sl = open_price;
         if(InpUseTrailing)
           {
            double trail = bid - current.atr * InpTrailAtrMult;
            if(trail > new_sl)
               new_sl = trail;
           }
         if(new_sl > cur_sl && bid - new_sl > min_distance)
            g_trade.PositionModify(ticket, NormalizeDouble(new_sl, digits), cur_tp);
        }
      else
         if(type == POSITION_TYPE_SELL)
           {
            if(InpUseBreakEven && open_price - ask >= risk_distance && (cur_sl > open_price || cur_sl == 0.0))
               new_sl = open_price;
            if(InpUseTrailing)
              {
               double trail = ask + current.atr * InpTrailAtrMult;
               if(new_sl == 0.0 || trail < new_sl)
                  new_sl = trail;
              }
            if((cur_sl == 0.0 || new_sl < cur_sl) && new_sl - ask > min_distance)
               g_trade.PositionModify(ticket, NormalizeDouble(new_sl, digits), cur_tp);
           }
     }
  }

//--- 逆シグナルで手仕舞う
void CloseOnOppositeSignal(const ENUM_TT_SIGNAL dir)
  {
   if(!InpCloseOnFlip || dir == TT_SIGNAL_NONE)
      return;

   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      ulong ticket = PositionGetTicket(i);
      if(ticket == 0)
         continue;
      if(PositionGetString(POSITION_SYMBOL) != _Symbol)
         continue;
      if(PositionGetInteger(POSITION_MAGIC) != InpMagic)
         continue;

      long type = PositionGetInteger(POSITION_TYPE);
      if((dir == TT_SIGNAL_BUY  && type == POSITION_TYPE_SELL) ||
         (dir == TT_SIGNAL_SELL && type == POSITION_TYPE_BUY))
        {
         if(!g_trade.PositionClose(ticket))
            PrintFormat("逆シグナル決済に失敗 ticket=%I64u retcode=%d", ticket, g_trade.ResultRetcode());
        }
     }
  }

void OpenFromSignal(const TTSignal &sig)
  {
   string why = "";
   if(!g_risk.CanOpen(why))
     {
      PrintFormat("新規見送り: %s", why);
      return;
     }

   int    digits = (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS);
   double price  = (sig.direction == TT_SIGNAL_BUY)
                   ? SymbolInfoDouble(_Symbol, SYMBOL_ASK)
                   : SymbolInfoDouble(_Symbol, SYMBOL_BID);

   //--- 損切り幅はシグナル足のATRで決めた距離を、実際の約定価格から引き直す
   double sl_distance = MathAbs(sig.price - sig.sl);
   double tp_distance = sl_distance * InpRrRatio;
   double sl, tp;
   if(sig.direction == TT_SIGNAL_BUY)
     {
      sl = NormalizeDouble(price - sl_distance, digits);
      tp = NormalizeDouble(price + tp_distance, digits);
     }
   else
     {
      sl = NormalizeDouble(price + sl_distance, digits);
      tp = NormalizeDouble(price - tp_distance, digits);
     }

   //--- ブローカーの最小ストップ距離を満たさない場合は発注しない
   double point        = SymbolInfoDouble(_Symbol, SYMBOL_POINT);
   long   stops_level  = SymbolInfoInteger(_Symbol, SYMBOL_TRADE_STOPS_LEVEL);
   double min_distance = stops_level * point;
   if(MathAbs(price - sl) <= min_distance || MathAbs(tp - price) <= min_distance)
     {
      PrintFormat("新規見送り: 損切り/利確がブローカーの最小距離(%d point)に収まりません", (int)stops_level);
      return;
     }

   double lot = g_risk.CalcLot(price, sl);
   if(lot <= 0.0)
     {
      Print("新規見送り: リスクに見合うロットが最小ロットを下回ります");
      return;
     }

   bool ok = (sig.direction == TT_SIGNAL_BUY)
             ? g_trade.Buy(lot, _Symbol, price, sl, tp, "TradeToolsEA")
             : g_trade.Sell(lot, _Symbol, price, sl, tp, "TradeToolsEA");

   if(!ok)
     {
      PrintFormat("発注失敗 retcode=%d (%s)", g_trade.ResultRetcode(), g_trade.ResultRetcodeDescription());
      return;
     }

   PrintFormat("発注 %s lot=%.2f price=%s sl=%s tp=%s — %s",
               TTSignalDirectionToString(sig.direction), lot,
               DoubleToString(price, digits), DoubleToString(sl, digits),
               DoubleToString(tp, digits), sig.reason);

   if(InpWriteFile)
      TTAppendSignal(sig, _Symbol, (ENUM_TIMEFRAMES)_Period, "ea");
  }

void OnTick(void)
  {
   ManageOpenPositions();

   //--- 判定は足の確定時に1回だけ
   datetime bar_time = iTime(_Symbol, (ENUM_TIMEFRAMES)_Period, 0);
   if(bar_time == g_last_bar_time)
      return;
   bool first_run = (g_last_bar_time == 0);
   g_last_bar_time = bar_time;
   if(first_run)
      return;

   TTSignal sig;
   if(!g_core.Evaluate(1, sig))
      return;
   if(sig.direction == TT_SIGNAL_NONE)
      return;

   CloseOnOppositeSignal(sig.direction);
   OpenFromSignal(sig);
  }
