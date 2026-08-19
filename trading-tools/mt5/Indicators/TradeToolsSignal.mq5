//+------------------------------------------------------------------+
//| TradeToolsSignal.mq5 — サインツール                               |
//| 判定は SignalCore.mqh に委譲する。ここは「描画・通知・記録」だけ。  |
//| 確定足でのみ判定するためリペイントしない(矢印は後から消えない)。   |
//+------------------------------------------------------------------+
#property copyright "TradeTools"
#property version   "1.00"
#property indicator_chart_window
#property indicator_buffers 2
#property indicator_plots   2

#property indicator_label1  "BUY"
#property indicator_type1   DRAW_ARROW
#property indicator_color1  clrDodgerBlue
#property indicator_width1  2

#property indicator_label2  "SELL"
#property indicator_type2   DRAW_ARROW
#property indicator_color2  clrOrangeRed
#property indicator_width2  2

#include <TradeTools/SignalCore.mqh>
#include <TradeTools/SignalFile.mqh>

input group "シグナル判定"
input int    InpEmaFast      = 12;    // 短期EMA
input int    InpEmaSlow      = 48;    // 長期EMA
input int    InpEmaTrend     = 200;   // トレンドEMA
input int    InpAdxPeriod    = 14;    // ADX期間
input double InpAdxMin       = 20.0;  // ADX下限(未満は見送り)
input int    InpAtrPeriod    = 14;    // ATR期間
input double InpSlAtrMult    = 1.5;   // 損切り = ATR × 倍率
input double InpRrRatio      = 1.8;   // 利確 = 損切り幅 × 倍率

input group "時間帯フィルタ(サーバー時間)"
input int    InpSessionStart = 8;     // 開始時
input int    InpSessionEnd   = 22;    // 終了時
input bool   InpBlockFriday  = true;  // 金曜終盤を止める
input int    InpFridayCutoff = 20;    // 金曜の停止時刻

input group "通知"
input bool   InpAlertPopup   = true;  // ポップアップ
input bool   InpAlertPush    = false; // スマホ通知(MT5側でMetaQuotes IDの設定が必要)
input bool   InpWriteFile    = true;  // Python連携用CSVに書き出す

double        g_buy[];
double        g_sell[];
CTTSignalCore g_core;
TTSignalParams g_params;
datetime      g_last_bar_time = 0;

int OnInit(void)
  {
   SetIndexBuffer(0, g_buy,  INDICATOR_DATA);
   SetIndexBuffer(1, g_sell, INDICATOR_DATA);
   PlotIndexSetInteger(0, PLOT_ARROW, 233);   // 上向き矢印
   PlotIndexSetInteger(1, PLOT_ARROW, 234);   // 下向き矢印
   PlotIndexSetDouble(0, PLOT_EMPTY_VALUE, EMPTY_VALUE);
   PlotIndexSetDouble(1, PLOT_EMPTY_VALUE, EMPTY_VALUE);
   ArraySetAsSeries(g_buy,  true);
   ArraySetAsSeries(g_sell, true);

   g_params.ema_fast           = InpEmaFast;
   g_params.ema_slow           = InpEmaSlow;
   g_params.ema_trend          = InpEmaTrend;
   g_params.adx_period         = InpAdxPeriod;
   g_params.adx_min            = InpAdxMin;
   g_params.atr_period         = InpAtrPeriod;
   g_params.sl_atr_mult        = InpSlAtrMult;
   g_params.rr_ratio           = InpRrRatio;
   g_params.session_start_hour = InpSessionStart;
   g_params.session_end_hour   = InpSessionEnd;
   g_params.block_friday_late  = InpBlockFriday;
   g_params.friday_cutoff_hour = InpFridayCutoff;

   if(InpEmaFast >= InpEmaSlow)
     {
      Print("設定エラー: 短期EMAは長期EMAより小さくしてください");
      return(INIT_PARAMETERS_INCORRECT);
     }
   if(!g_core.Init(_Symbol, (ENUM_TIMEFRAMES)_Period, g_params))
      return(INIT_FAILED);

   IndicatorSetString(INDICATOR_SHORTNAME, StringFormat("TradeToolsSignal(%d,%d,%d)", InpEmaFast, InpEmaSlow, InpEmaTrend));
   return(INIT_SUCCEEDED);
  }

void OnDeinit(const int reason)
  {
   g_core.Deinit();
  }

//--- 過去分をまとめて描画する。判定は毎回 shift 指定で確定足のみ
void PaintHistory(const int rates_total, const int prev_calculated)
  {
   int limit = rates_total - prev_calculated;
   if(prev_calculated == 0)
      limit = rates_total - g_core.WarmupBars();
   if(limit < 1)
      limit = 1;
   if(limit > rates_total - g_core.WarmupBars())
      limit = rates_total - g_core.WarmupBars();
   if(limit < 1)
      return;

   for(int shift = limit; shift >= 1; shift--)
     {
      g_buy[shift]  = EMPTY_VALUE;
      g_sell[shift] = EMPTY_VALUE;

      TTSignal sig;
      if(!g_core.Evaluate(shift, sig))
         continue;
      if(sig.direction == TT_SIGNAL_BUY)
         g_buy[shift]  = sig.price - sig.atr * 0.5;
      else
         if(sig.direction == TT_SIGNAL_SELL)
            g_sell[shift] = sig.price + sig.atr * 0.5;
     }
  }

//--- 新しい足が確定した瞬間だけ通知する(同じ足で鳴り続けるのを防ぐ)
void NotifyOnClosedBar(void)
  {
   datetime bar_time = iTime(_Symbol, (ENUM_TIMEFRAMES)_Period, 0);
   if(bar_time == g_last_bar_time)
      return;
   bool first_run = (g_last_bar_time == 0);
   g_last_bar_time = bar_time;
   if(first_run)
      return;   // 起動直後に過去のシグナルで鳴らさない

   TTSignal sig;
   if(!g_core.Evaluate(1, sig) || sig.direction == TT_SIGNAL_NONE)
      return;

   int    digits = (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS);
   string text = StringFormat("[%s %s] %s  価格 %s / 損切 %s / 利確 %s  — %s",
                              _Symbol,
                              EnumToString((ENUM_TIMEFRAMES)_Period),
                              TTSignalDirectionToString(sig.direction),
                              DoubleToString(sig.price, digits),
                              DoubleToString(sig.sl, digits),
                              DoubleToString(sig.tp, digits),
                              sig.reason);

   if(InpAlertPopup)
      Alert(text);
   if(InpAlertPush)
      SendNotification(text);
   if(InpWriteFile)
      TTAppendSignal(sig, _Symbol, (ENUM_TIMEFRAMES)_Period, "indicator");

   Print(text);
  }

int OnCalculate(const int rates_total,
                const int prev_calculated,
                const datetime &time[],
                const double &open[],
                const double &high[],
                const double &low[],
                const double &close[],
                const long &tick_volume[],
                const long &volume[],
                const int &spread[])
  {
   if(rates_total <= g_core.WarmupBars())
      return(0);

   PaintHistory(rates_total, prev_calculated);
   NotifyOnClosedBar();

   return(rates_total);
  }
