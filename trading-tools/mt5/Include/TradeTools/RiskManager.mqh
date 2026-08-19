//+------------------------------------------------------------------+
//| RiskManager.mqh                                                  |
//| ロット計算と発注前ガード。EAが「口座を壊さない」ための最後の砦。    |
//+------------------------------------------------------------------+
#property copyright "TradeTools"

#ifndef __TT_RISK_MANAGER_MQH__
#define __TT_RISK_MANAGER_MQH__

struct TTRiskParams
  {
   double   risk_percent;        // 1トレードで許容する損失(口座残高比 %)
   double   max_lot;             // 1トレードの上限ロット(証拠金以前の自主規制)
   int      max_positions;       // 同時保有ポジション数の上限
   double   max_daily_loss_pct;  // 当日の損失がこの%を超えたら新規停止
   int      max_spread_points;   // スプレッドがこれを超えたら発注しない
   int      slippage_points;     // 許容スリッページ
  };

TTRiskParams TTDefaultRiskParams()
  {
   TTRiskParams r;
   r.risk_percent       = 1.0;
   r.max_lot            = 1.0;
   r.max_positions      = 1;
   r.max_daily_loss_pct = 3.0;
   r.max_spread_points  = 30;
   r.slippage_points    = 20;
   return(r);
  }

class CTTRiskManager
  {
private:
   string        m_symbol;
   TTRiskParams  m_r;
   long          m_magic;

   double        NormalizeLot(const double lot);

public:
                 CTTRiskManager(void) : m_symbol(""), m_magic(0) { m_r = TTDefaultRiskParams(); }

   void          Init(const string symbol, const long magic, const TTRiskParams &r)
     {
      m_symbol = (symbol == "" ? _Symbol : symbol);
      m_magic  = magic;
      m_r      = r;
     }

   //--- 損切り距離(価格差)から、リスク%に収まるロットを逆算する
   double        CalcLot(const double entry_price, const double sl_price);
   int           CountPositions(void);
   double        TodayRealizedPnL(void);
   //--- 新規発注してよいか。ダメな場合は why に理由が入る
   bool          CanOpen(string &why);
   int           Slippage(void) const { return(m_r.slippage_points); }
  };

double CTTRiskManager::NormalizeLot(const double lot)
  {
   double min_lot  = SymbolInfoDouble(m_symbol, SYMBOL_VOLUME_MIN);
   double max_lot  = SymbolInfoDouble(m_symbol, SYMBOL_VOLUME_MAX);
   double lot_step = SymbolInfoDouble(m_symbol, SYMBOL_VOLUME_STEP);

   if(lot_step <= 0.0)
      lot_step = 0.01;

   double normalized = MathFloor(lot / lot_step) * lot_step;

   if(normalized < min_lot)
      normalized = 0.0;                       // 最小ロットに満たない = 発注しない
   if(normalized > max_lot)
      normalized = max_lot;
   if(m_r.max_lot > 0.0 && normalized > m_r.max_lot)
      normalized = m_r.max_lot;

   //--- ステップの丸め誤差で拒否されないよう桁を揃える
   int digits = (int)MathMax(0, MathRound(-MathLog10(lot_step)));
   return(NormalizeDouble(normalized, digits));
  }

double CTTRiskManager::CalcLot(const double entry_price, const double sl_price)
  {
   double sl_distance = MathAbs(entry_price - sl_price);
   if(sl_distance <= 0.0)
      return(0.0);

   double tick_size  = SymbolInfoDouble(m_symbol, SYMBOL_TRADE_TICK_SIZE);
   double tick_value = SymbolInfoDouble(m_symbol, SYMBOL_TRADE_TICK_VALUE);
   if(tick_size <= 0.0 || tick_value <= 0.0)
     {
      Print("CalcLot: ティック情報を取得できません symbol=", m_symbol);
      return(0.0);
     }

   //--- 1ロットあたりの損失額 = 損切り距離をティック数に直して1ティックの価値を掛ける
   double loss_per_lot = (sl_distance / tick_size) * tick_value;
   if(loss_per_lot <= 0.0)
      return(0.0);

   double balance     = AccountInfoDouble(ACCOUNT_BALANCE);
   double risk_amount = balance * m_r.risk_percent / 100.0;

   return(NormalizeLot(risk_amount / loss_per_lot));
  }

int CTTRiskManager::CountPositions(void)
  {
   int count = 0;
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      ulong ticket = PositionGetTicket(i);
      if(ticket == 0)
         continue;
      if(PositionGetString(POSITION_SYMBOL) == m_symbol &&
         PositionGetInteger(POSITION_MAGIC) == m_magic)
         count++;
     }
   return(count);
  }

double CTTRiskManager::TodayRealizedPnL(void)
  {
   datetime now = TimeCurrent();
   MqlDateTime dt;
   TimeToStruct(now, dt);
   dt.hour = 0; dt.min = 0; dt.sec = 0;
   datetime day_start = StructToTime(dt);

   if(!HistorySelect(day_start, now))
      return(0.0);

   double pnl = 0.0;
   for(int i = HistoryDealsTotal() - 1; i >= 0; i--)
     {
      ulong deal = HistoryDealGetTicket(i);
      if(deal == 0)
         continue;
      if(HistoryDealGetInteger(deal, DEAL_MAGIC) != m_magic)
         continue;
      if(HistoryDealGetString(deal, DEAL_SYMBOL) != m_symbol)
         continue;
      if(HistoryDealGetInteger(deal, DEAL_ENTRY) != DEAL_ENTRY_OUT)
         continue;

      pnl += HistoryDealGetDouble(deal, DEAL_PROFIT)
           + HistoryDealGetDouble(deal, DEAL_SWAP)
           + HistoryDealGetDouble(deal, DEAL_COMMISSION);
     }
   return(pnl);
  }

bool CTTRiskManager::CanOpen(string &why)
  {
   if(!TerminalInfoInteger(TERMINAL_TRADE_ALLOWED))
     {
      why = "端末の自動売買が無効です";
      return(false);
     }
   if(!AccountInfoInteger(ACCOUNT_TRADE_EXPERT))
     {
      why = "口座側で自動売買が許可されていません";
      return(false);
     }
   if(!SymbolInfoInteger(m_symbol, SYMBOL_TRADE_MODE))
     {
      why = "この銘柄は取引できません";
      return(false);
     }

   if(CountPositions() >= m_r.max_positions)
     {
      why = StringFormat("同時保有上限(%d)に達しています", m_r.max_positions);
      return(false);
     }

   long spread = SymbolInfoInteger(m_symbol, SYMBOL_SPREAD);
   if(m_r.max_spread_points > 0 && spread > m_r.max_spread_points)
     {
      why = StringFormat("スプレッド %d point が上限 %d を超過", (int)spread, m_r.max_spread_points);
      return(false);
     }

   if(m_r.max_daily_loss_pct > 0.0)
     {
      double balance = AccountInfoDouble(ACCOUNT_BALANCE);
      double limit   = -balance * m_r.max_daily_loss_pct / 100.0;
      double today   = TodayRealizedPnL();
      if(today <= limit)
        {
         why = StringFormat("当日損失 %.2f が上限 %.2f に到達したため新規停止", today, limit);
         return(false);
        }
     }

   why = "";
   return(true);
  }

#endif // __TT_RISK_MANAGER_MQH__
