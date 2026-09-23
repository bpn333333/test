//+------------------------------------------------------------------+
//|                                        TradeToolsRangeRSI.mq5    |
//|  直近高安への逆張り + RSI(14) 70/30 決済                          |
//|                                                                  |
//|  検証条件: GBPUSD / M5 / ルックバック20本 / オフセット5pips        |
//|            2026-02-18〜2026-08-19 で 8,509回 勝率70.6%            |
//|                                                                  |
//|  v1.01: 利確 150pips を追加(利確ルール45通りの比較で最良)         |
//|  v1.02: RSIシグナルが出ても「含み損なら決済しない」を追加         |
//|                                                                  |
//|  検証比較 (GBPUSD M5 / 2026-02-18〜08-19 / エントリー8,509件)     |
//|    v1.01  勝率 70.62%  控除後 +31,383.5pips  PF 1.541            |
//|    v1.02  勝率 97.81%  控除後 +94,026.7pips  PF 5.256            |
//|                                                                  |
//|  *** v1.02 の数字は「負けを確定させない」ことで作られている。     |
//|      期間末に 199件・評価損 -24,036.9pips が未決済で残った。      |
//|      リスク指標は v1.01 比で以下のとおり悪化する:                 |
//|        最大逆行     235.0 → 502.9 pips                          |
//|        最大の負け  -152.0 → -375.6 pips                          |
//|        最長保有      2.4 →  71.1 日                             |
//|        最大同時保有  117 →  299 ポジション                       |
//|      損切りは置いていない。スワップは検証に含まれていない。       |
//|      実口座で使う前に必ずデモで検証すること。投資助言ではない。***|
//+------------------------------------------------------------------+
#property copyright "TradeTools"
#property link      ""
#property version   "1.02"
#property description "直近高安への逆張り指値 + RSI(14) 70/30 決済(含み益時のみ) + 利確150pips"
#property description "損切りは置かない。ヘッジング口座が必要。"

#include <Trade\Trade.mqh>
#include <Trade\PositionInfo.mqh>
#include <Trade\OrderInfo.mqh>

//--- 戦略パラメータ ------------------------------------------------
input group             "=== 戦略(検証時の値) ==="
input int      InpLookback       = 20;        // 直近高安のルックバック本数
input double   InpOffsetPips     = 5.0;       // 高安からのオフセット(pips)
input int      InpRSIPeriod      = 14;        // RSI 期間
input double   InpRSIUpper       = 70.0;      // 買いポジションの決済しきい値
input double   InpRSILower       = 30.0;      // 売りポジションの決済しきい値
input double   InpTakeProfitPips = 150.0;     // 利確(pips)。0=利確なし
input bool     InpHoldLosingPos  = true;      // 含み損ならRSI決済を見送る(v1.02)
input bool     InpAllowBuy       = true;      // 買いエントリーを行う
input bool     InpAllowSell      = true;      // 売りエントリーを行う

//--- 資金管理・保護 ------------------------------------------------
input group             "=== 資金管理・保護 ==="
input double   InpLots           = 0.01;      // 1ポジションのロット
input int      InpMaxPositions   = 0;         // 同時保有の上限(0=無制限。検証と同じ)
input int      InpMaxSpreadPts   = 0;         // 発注を許すスプレッド上限(point。0=制限なし)
input bool     InpMarketIfBreached = false;   // 水準を既に抜けていたら成行で入る(既定=見送り)

//--- その他 --------------------------------------------------------
input group             "=== その他 ==="
input long     InpMagic          = 20260819;  // マジックナンバー
input bool     InpVerboseLog     = true;      // 動作ログを出す

//--- 内部状態 ------------------------------------------------------
CTrade         g_trade;
CPositionInfo  g_pos;
COrderInfo     g_ord;

int      g_rsi_handle = INVALID_HANDLE;
datetime g_last_bar   = 0;
double   g_pip        = 0.0;

//+------------------------------------------------------------------+
//| pip の大きさ(5桁/3桁業者は point の10倍)                          |
//+------------------------------------------------------------------+
double PipSize()
  {
   int digits = (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS);
   double point = SymbolInfoDouble(_Symbol, SYMBOL_POINT);
   if(digits == 3 || digits == 5)
      return point * 10.0;
   return point;
  }

//+------------------------------------------------------------------+
//| 価格をティックサイズに丸める                                      |
//+------------------------------------------------------------------+
double NormPrice(const double price)
  {
   double ts = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
   if(ts <= 0.0)
      return NormalizeDouble(price, (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS));
   return NormalizeDouble(MathRound(price / ts) * ts,
                          (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS));
  }

//+------------------------------------------------------------------+
//| 初期化                                                            |
//+------------------------------------------------------------------+
int OnInit()
  {
//--- ヘッジング口座でなければ動かさない
//    ネッティング口座では同一銘柄のポジションが合算され、
//    「複数ポジションを個別に保有する」という検証の前提が崩れる
   if((ENUM_ACCOUNT_MARGIN_MODE)AccountInfoInteger(ACCOUNT_MARGIN_MODE)
      != ACCOUNT_MARGIN_MODE_RETAIL_HEDGING)
     {
      Print("[TradeToolsRangeRSI] このEAはヘッジング口座専用。"
            "ネッティング口座ではポジションが合算され検証と挙動が変わる。");
      return(INIT_FAILED);
     }

   if(InpLookback < 2)
     {
      Print("[TradeToolsRangeRSI] InpLookback は 2 以上にすること。");
      return(INIT_PARAMETERS_INCORRECT);
     }

   if(_Period != PERIOD_M5)
      PrintFormat("[TradeToolsRangeRSI] 注意: 検証は M5 で行った。現在のチャートは %s。",
                  EnumToString(_Period));

   g_rsi_handle = iRSI(_Symbol, PERIOD_CURRENT, InpRSIPeriod, PRICE_CLOSE);
   if(g_rsi_handle == INVALID_HANDLE)
     {
      Print("[TradeToolsRangeRSI] iRSI の作成に失敗: ", GetLastError());
      return(INIT_FAILED);
     }

   g_pip = PipSize();
   g_trade.SetExpertMagicNumber(InpMagic);
   g_trade.SetDeviationInPoints(20);
   g_trade.SetTypeFillingBySymbol(_Symbol);
   g_trade.LogLevel(LOG_LEVEL_ERRORS);

   PrintFormat("[TradeToolsRangeRSI] 起動 %s %s  pip=%.5f  lookback=%d  offset=%.1fpips  RSI(%d) %.0f/%.0f  利確=%.0fpips",
               _Symbol, EnumToString(_Period), g_pip, InpLookback,
               InpOffsetPips, InpRSIPeriod, InpRSIUpper, InpRSILower,
               InpTakeProfitPips);
   if(InpHoldLosingPos)
      Print("[TradeToolsRangeRSI] 含み損のRSIシグナルは見送る設定。"
            "検証時の最大逆行502.9pips / 最長保有71.1日 / 最大同時保有299。損切りは無し。");
   else
      Print("[TradeToolsRangeRSI] 含み損でもRSIで決済する設定。"
            "検証時の最大逆行235.0pips / 最大同時保有117。損切りは無し。");

   g_last_bar = iTime(_Symbol, PERIOD_CURRENT, 0);
   return(INIT_SUCCEEDED);
  }

//+------------------------------------------------------------------+
//| 終了                                                              |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
  {
   if(g_rsi_handle != INVALID_HANDLE)
      IndicatorRelease(g_rsi_handle);
//--- 自分が出した未約定の指値は残さない
   DeleteMyPendings();
  }

//+------------------------------------------------------------------+
//| 新しい足の開始か                                                  |
//+------------------------------------------------------------------+
bool IsNewBar()
  {
   datetime t = iTime(_Symbol, PERIOD_CURRENT, 0);
   if(t == 0)
      return(false);
   if(t == g_last_bar)
      return(false);
   g_last_bar = t;
   return(true);
  }

//+------------------------------------------------------------------+
//| 自分のポジション数                                                |
//+------------------------------------------------------------------+
int CountMyPositions()
  {
   int cnt = 0;
   for(int i = PositionsTotal() - 1; i >= 0; i--)
      if(g_pos.SelectByIndex(i))
         if(g_pos.Symbol() == _Symbol && g_pos.Magic() == InpMagic)
            cnt++;
   return(cnt);
  }

//+------------------------------------------------------------------+
//| RSI による決済                                                    |
//|   確定足(shift=1)の RSI で判定し、成行で決済する。                |
//|   OnTick の新足直後に呼ぶため、検証の「次の足の始値で決済」に     |
//|   対応する。                                                      |
//+------------------------------------------------------------------+
void CloseByRSI()
  {
   double buf[];
   if(CopyBuffer(g_rsi_handle, 0, 1, 1, buf) != 1)
     {
      if(InpVerboseLog)
         Print("[TradeToolsRangeRSI] RSI の取得に失敗: ", GetLastError());
      return;
     }
   double rsi = buf[0];

   bool close_buy  = (rsi >= InpRSIUpper);
   bool close_sell = (rsi <= InpRSILower);
   if(!close_buy && !close_sell)
      return;

   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      if(!g_pos.SelectByIndex(i))
         continue;
      if(g_pos.Symbol() != _Symbol || g_pos.Magic() != InpMagic)
         continue;

      ENUM_POSITION_TYPE type = g_pos.PositionType();
      if((type == POSITION_TYPE_BUY && close_buy) ||
         (type == POSITION_TYPE_SELL && close_sell))
        {
         ulong ticket = g_pos.Ticket();

         //--- v1.02: 含み損なら決済せず、次にシグナルが出るまで保有する
         //    検証は Bid ベースの足で建値と比較したが、ここでは実際に決済
         //    される価格(買いは Bid / 売りは Ask)で比較する。売り側は
         //    スプレッドのぶんだけ検証より厳しい判定になる。
         if(InpHoldLosingPos)
           {
            double open_price = g_pos.PriceOpen();
            double now = (type == POSITION_TYPE_BUY)
                         ? SymbolInfoDouble(_Symbol, SYMBOL_BID)
                         : SymbolInfoDouble(_Symbol, SYMBOL_ASK);
            double move = (type == POSITION_TYPE_BUY)
                          ? (now - open_price)
                          : (open_price - now);
            if(move <= 0.0)
              {
               if(InpVerboseLog)
                  PrintFormat("[TradeToolsRangeRSI] RSI=%.1f だが含み損 %.1fpips のため見送り ticket=%I64u",
                              rsi, move / g_pip, ticket);
               continue;
              }
           }

         if(!g_trade.PositionClose(ticket))
            PrintFormat("[TradeToolsRangeRSI] 決済失敗 ticket=%I64u ret=%d %s",
                        ticket, g_trade.ResultRetcode(), g_trade.ResultRetcodeDescription());
         else if(InpVerboseLog)
            PrintFormat("[TradeToolsRangeRSI] RSI=%.1f で決済 ticket=%I64u %s",
                        rsi, ticket, (type == POSITION_TYPE_BUY ? "BUY" : "SELL"));
        }
     }
  }

//+------------------------------------------------------------------+
//| 自分が出した未約定の指値を消す                                    |
//|   検証では「その足だけ有効な指値」だったため、毎足消して出し直す  |
//+------------------------------------------------------------------+
void DeleteMyPendings()
  {
   for(int i = OrdersTotal() - 1; i >= 0; i--)
     {
      if(!g_ord.SelectByIndex(i))
         continue;
      if(g_ord.Symbol() != _Symbol || g_ord.Magic() != InpMagic)
         continue;
      ulong ticket = g_ord.Ticket();
      if(!g_trade.OrderDelete(ticket))
         PrintFormat("[TradeToolsRangeRSI] 指値の削除に失敗 ticket=%I64u ret=%d",
                     ticket, g_trade.ResultRetcode());
     }
  }

//+------------------------------------------------------------------+
//| 指値を出す                                                        |
//+------------------------------------------------------------------+
void PlaceOrders()
  {
//--- 同時保有の上限
   if(InpMaxPositions > 0 && CountMyPositions() >= InpMaxPositions)
      return;

//--- スプレッド上限
   if(InpMaxSpreadPts > 0)
     {
      long sp = SymbolInfoInteger(_Symbol, SYMBOL_SPREAD);
      if(sp > InpMaxSpreadPts)
        {
         if(InpVerboseLog)
            PrintFormat("[TradeToolsRangeRSI] スプレッド %d > %d のため発注を見送り",
                        (int)sp, InpMaxSpreadPts);
         return;
        }
     }

//--- 確定足(shift=1)から直近 InpLookback 本の高値・安値
   double hh[], ll[];
   if(CopyHigh(_Symbol, PERIOD_CURRENT, 1, InpLookback, hh) != InpLookback)
      return;
   if(CopyLow(_Symbol, PERIOD_CURRENT, 1, InpLookback, ll) != InpLookback)
      return;

   double hi = hh[ArrayMaximum(hh)];
   double lo = ll[ArrayMinimum(ll)];
   double c1 = iClose(_Symbol, PERIOD_CURRENT, 1);
   if(c1 <= 0.0)
      return;

   double off        = InpOffsetPips * g_pip;
   double sell_level = NormPrice(hi - off);
   double buy_level  = NormPrice(lo + off);

   double ask   = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   double bid   = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   double point = SymbolInfoDouble(_Symbol, SYMBOL_POINT);
   long   stops = SymbolInfoInteger(_Symbol, SYMBOL_TRADE_STOPS_LEVEL);
   double mindist = stops * point;

//--- 利確。0 なら設定しない(= v1.00 と同じ挙動)
//    検証では「足の高値/安値が利確水準に届いたらその水準で約定」としたため、
//    ブローカー側の TP として置くのが検証と同じ扱いになる。
//    損切りは検証条件どおり設定しない(SL は 0.0 のまま)。
   double tp_dist  = InpTakeProfitPips * g_pip;
   double sell_tp  = (InpTakeProfitPips > 0.0) ? NormPrice(sell_level - tp_dist) : 0.0;
   double buy_tp   = (InpTakeProfitPips > 0.0) ? NormPrice(buy_level + tp_dist) : 0.0;

//--- 売り: 検証では「確定足の終値が水準より下」のときだけ発注した
   if(InpAllowSell && c1 < sell_level)
     {
      if(sell_level > bid + mindist)
        {
         if(!g_trade.SellLimit(InpLots, sell_level, _Symbol, 0.0, sell_tp,
                               ORDER_TIME_GTC, 0, "RangeRSI sell"))
            PrintFormat("[TradeToolsRangeRSI] SellLimit 失敗 price=%.5f tp=%.5f ret=%d %s",
                        sell_level, sell_tp, g_trade.ResultRetcode(),
                        g_trade.ResultRetcodeDescription());
         else if(InpVerboseLog)
            PrintFormat("[TradeToolsRangeRSI] SellLimit %.5f tp=%.5f (直近高値 %.5f - %.1fpips)",
                        sell_level, sell_tp, hi, InpOffsetPips);
        }
      else if(InpMarketIfBreached)
        {
         double mtp = (InpTakeProfitPips > 0.0) ? NormPrice(bid - tp_dist) : 0.0;
         if(!g_trade.Sell(InpLots, _Symbol, 0.0, 0.0, mtp, "RangeRSI sell mkt"))
            PrintFormat("[TradeToolsRangeRSI] 成行売り失敗 ret=%d", g_trade.ResultRetcode());
        }
     }

//--- 買い: 検証では「確定足の終値が水準より上」のときだけ発注した
   if(InpAllowBuy && c1 > buy_level)
     {
      if(buy_level < ask - mindist)
        {
         if(!g_trade.BuyLimit(InpLots, buy_level, _Symbol, 0.0, buy_tp,
                              ORDER_TIME_GTC, 0, "RangeRSI buy"))
            PrintFormat("[TradeToolsRangeRSI] BuyLimit 失敗 price=%.5f tp=%.5f ret=%d %s",
                        buy_level, buy_tp, g_trade.ResultRetcode(),
                        g_trade.ResultRetcodeDescription());
         else if(InpVerboseLog)
            PrintFormat("[TradeToolsRangeRSI] BuyLimit %.5f tp=%.5f (直近安値 %.5f + %.1fpips)",
                        buy_level, buy_tp, lo, InpOffsetPips);
        }
      else if(InpMarketIfBreached)
        {
         double mtp = (InpTakeProfitPips > 0.0) ? NormPrice(ask + tp_dist) : 0.0;
         if(!g_trade.Buy(InpLots, _Symbol, 0.0, 0.0, mtp, "RangeRSI buy mkt"))
            PrintFormat("[TradeToolsRangeRSI] 成行買い失敗 ret=%d", g_trade.ResultRetcode());
        }
     }
  }

//+------------------------------------------------------------------+
//| ティック                                                          |
//+------------------------------------------------------------------+
void OnTick()
  {
   if(!IsNewBar())
      return;

//--- 検証と同じ順序: 決済 → 前の足の指値を取り消し → 新しい指値
   CloseByRSI();
   DeleteMyPendings();
   PlaceOrders();
  }
//+------------------------------------------------------------------+
