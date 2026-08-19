//+------------------------------------------------------------------+
//| SignalCore.mqh                                                   |
//| 4ツール共通のシグナル判定。インジケータ・EA・パリティ検証スクリプトは |
//| すべてこのファイルだけを判定根拠とする(ロジックの二重定義を禁止)。   |
//| Python 側の実装は monitor/tradetools_monitor/signals.py が鏡像。    |
//+------------------------------------------------------------------+
#property copyright "TradeTools"

#ifndef __TT_SIGNAL_CORE_MQH__
#define __TT_SIGNAL_CORE_MQH__

//--- 判定結果の方向
enum ENUM_TT_SIGNAL
  {
   TT_SIGNAL_NONE = 0,
   TT_SIGNAL_BUY  = 1,
   TT_SIGNAL_SELL = -1
  };

//--- ロジックのパラメータ。EA・インジケータで同じ値を渡すこと
struct TTSignalParams
  {
   int      ema_fast;            // 短期EMA
   int      ema_slow;            // 長期EMA(クロス判定の相手)
   int      ema_trend;           // トレンドフィルタEMA
   int      adx_period;          // ADX期間
   double   adx_min;             // ADXがこの値未満ならレンジとみなし見送る
   int      atr_period;          // ATR期間(損切り幅の算出に使う)
   double   sl_atr_mult;         // 損切り = ATR × この倍率
   double   rr_ratio;            // 利確 = 損切り幅 × この倍率
   int      session_start_hour;  // 取引時間帯の開始(サーバー時間)
   int      session_end_hour;    // 取引時間帯の終了(サーバー時間・この時刻未満)
   bool     block_friday_late;   // 金曜終盤の新規を止めるか
   int      friday_cutoff_hour;  // 金曜の新規停止時刻(サーバー時間)
  };

//--- 判定の出力。EAの発注もX配信もこの構造体だけを見る
struct TTSignal
  {
   ENUM_TT_SIGNAL direction;
   datetime       time;      // 判定に使った確定足の時刻
   double         price;     // 判定に使った終値
   double         sl;        // 損切り価格
   double         tp;        // 利確価格
   double         atr;
   double         adx;
   string         reason;    // 見送り理由 / 成立理由(ログとX配信の材料)
  };

//--- 既定値。ここを変えると全ツールの挙動が変わる
TTSignalParams TTDefaultParams()
  {
   TTSignalParams p;
   p.ema_fast           = 12;
   p.ema_slow           = 48;
   p.ema_trend          = 200;
   p.adx_period         = 14;
   p.adx_min            = 20.0;
   p.atr_period         = 14;
   p.sl_atr_mult        = 1.5;
   p.rr_ratio           = 1.8;
   p.session_start_hour = 8;
   p.session_end_hour   = 22;
   p.block_friday_late  = true;
   p.friday_cutoff_hour = 20;
   return(p);
  }

//+------------------------------------------------------------------+
//| シグナル判定本体                                                  |
//+------------------------------------------------------------------+
class CTTSignalCore
  {
private:
   string            m_symbol;
   ENUM_TIMEFRAMES   m_tf;
   TTSignalParams    m_p;
   int               m_h_ema_fast;
   int               m_h_ema_slow;
   int               m_h_ema_trend;
   int               m_h_adx;
   int               m_h_atr;

   bool              ReadOne(const int handle, const int buffer, const int shift, double &value);

public:
                     CTTSignalCore(void);
                    ~CTTSignalCore(void);

   bool              Init(const string symbol, const ENUM_TIMEFRAMES tf, const TTSignalParams &p);
   void              Deinit(void);
   //--- shift=1 で「直近の確定足」を判定する。0を渡すと未確定足になるので通常は使わない
   bool              Evaluate(const int shift, TTSignal &out);
   bool              InSession(const datetime t, string &why);
   int               WarmupBars(void) const;
   TTSignalParams    Params(void) const { return(m_p); }
  };

CTTSignalCore::CTTSignalCore(void) : m_symbol(""), m_tf(PERIOD_CURRENT),
   m_h_ema_fast(INVALID_HANDLE), m_h_ema_slow(INVALID_HANDLE),
   m_h_ema_trend(INVALID_HANDLE), m_h_adx(INVALID_HANDLE), m_h_atr(INVALID_HANDLE)
  {
   m_p = TTDefaultParams();
  }

CTTSignalCore::~CTTSignalCore(void)
  {
   Deinit();
  }

bool CTTSignalCore::Init(const string symbol, const ENUM_TIMEFRAMES tf, const TTSignalParams &p)
  {
   Deinit();
   m_symbol = (symbol == "" ? _Symbol : symbol);
   m_tf     = tf;
   m_p      = p;

   m_h_ema_fast  = iMA(m_symbol, m_tf, m_p.ema_fast,  0, MODE_EMA, PRICE_CLOSE);
   m_h_ema_slow  = iMA(m_symbol, m_tf, m_p.ema_slow,  0, MODE_EMA, PRICE_CLOSE);
   m_h_ema_trend = iMA(m_symbol, m_tf, m_p.ema_trend, 0, MODE_EMA, PRICE_CLOSE);
   m_h_adx       = iADX(m_symbol, m_tf, m_p.adx_period);
   m_h_atr       = iATR(m_symbol, m_tf, m_p.atr_period);

   if(m_h_ema_fast  == INVALID_HANDLE || m_h_ema_slow == INVALID_HANDLE ||
      m_h_ema_trend == INVALID_HANDLE || m_h_adx      == INVALID_HANDLE ||
      m_h_atr       == INVALID_HANDLE)
     {
      Print("CTTSignalCore::Init 失敗 — インジケータハンドルを取得できません symbol=", m_symbol);
      Deinit();
      return(false);
     }
   return(true);
  }

void CTTSignalCore::Deinit(void)
  {
   if(m_h_ema_fast  != INVALID_HANDLE) { IndicatorRelease(m_h_ema_fast);  m_h_ema_fast  = INVALID_HANDLE; }
   if(m_h_ema_slow  != INVALID_HANDLE) { IndicatorRelease(m_h_ema_slow);  m_h_ema_slow  = INVALID_HANDLE; }
   if(m_h_ema_trend != INVALID_HANDLE) { IndicatorRelease(m_h_ema_trend); m_h_ema_trend = INVALID_HANDLE; }
   if(m_h_adx       != INVALID_HANDLE) { IndicatorRelease(m_h_adx);       m_h_adx       = INVALID_HANDLE; }
   if(m_h_atr       != INVALID_HANDLE) { IndicatorRelease(m_h_atr);       m_h_atr       = INVALID_HANDLE; }
  }

int CTTSignalCore::WarmupBars(void) const
  {
//--- EMAは期間の数倍を見ないと値が安定しない。Python側の warmup_bars と必ず一致させる
   int longest = MathMax(m_p.ema_trend, MathMax(m_p.ema_slow, MathMax(m_p.adx_period, m_p.atr_period)));
   return(longest * 3 + 10);
  }

bool CTTSignalCore::ReadOne(const int handle, const int buffer, const int shift, double &value)
  {
   double buf[];
   if(CopyBuffer(handle, buffer, shift, 1, buf) != 1)
      return(false);
   value = buf[0];
   return(value != EMPTY_VALUE && MathIsValidNumber(value));
  }

bool CTTSignalCore::InSession(const datetime t, string &why)
  {
   MqlDateTime dt;
   TimeToStruct(t, dt);

   if(dt.day_of_week == 0 || dt.day_of_week == 6)
     {
      why = "週末のため見送り";
      return(false);
     }
   if(dt.hour < m_p.session_start_hour || dt.hour >= m_p.session_end_hour)
     {
      why = StringFormat("時間帯外(%02d時)のため見送り", dt.hour);
      return(false);
     }
   if(m_p.block_friday_late && dt.day_of_week == 5 && dt.hour >= m_p.friday_cutoff_hour)
     {
      why = "金曜終盤のため新規見送り";
      return(false);
     }
   why = "";
   return(true);
  }

bool CTTSignalCore::Evaluate(const int shift, TTSignal &out)
  {
   out.direction = TT_SIGNAL_NONE;
   out.time      = 0;
   out.price     = 0.0;
   out.sl        = 0.0;
   out.tp        = 0.0;
   out.atr       = 0.0;
   out.adx       = 0.0;
   out.reason    = "";

   if(Bars(m_symbol, m_tf) < WarmupBars())
     {
      out.reason = "ヒストリー不足";
      return(false);
     }

//--- 判定足と、その1本前(クロス検出に必要)
   double fast_now, fast_prev, slow_now, slow_prev, trend_now, adx_now, atr_now;
   if(!ReadOne(m_h_ema_fast,  0, shift,     fast_now)  ||
      !ReadOne(m_h_ema_fast,  0, shift + 1, fast_prev) ||
      !ReadOne(m_h_ema_slow,  0, shift,     slow_now)  ||
      !ReadOne(m_h_ema_slow,  0, shift + 1, slow_prev) ||
      !ReadOne(m_h_ema_trend, 0, shift,     trend_now) ||
      !ReadOne(m_h_adx,       0, shift,     adx_now)   ||
      !ReadOne(m_h_atr,       0, shift,     atr_now))
     {
      out.reason = "インジケータ値を取得できません";
      return(false);
     }

   MqlRates rates[];
   if(CopyRates(m_symbol, m_tf, shift, 1, rates) != 1)
     {
      out.reason = "レートを取得できません";
      return(false);
     }

   out.time  = rates[0].time;
   out.price = rates[0].close;
   out.atr   = atr_now;
   out.adx   = adx_now;

   if(atr_now <= 0.0)
     {
      out.reason = "ATRが0のため損切り幅を決められません";
      return(false);
     }

//--- 時間帯フィルタ
   string why = "";
   if(!InSession(out.time, why))
     {
      out.reason = why;
      return(true);   // 判定自体は成功。方向がNONEなだけ
     }

//--- モメンタムフィルタ
   if(adx_now < m_p.adx_min)
     {
      out.reason = StringFormat("ADX %.1f < %.1f のためレンジと判断", adx_now, m_p.adx_min);
      return(true);
     }

//--- クロス検出(確定足ベース)
   bool cross_up   = (fast_prev <= slow_prev && fast_now > slow_now);
   bool cross_down = (fast_prev >= slow_prev && fast_now < slow_now);

   if(!cross_up && !cross_down)
     {
      out.reason = "クロスなし";
      return(true);
     }

//--- トレンドフィルタ(上位方向に逆らわない)
   if(cross_up && out.price <= trend_now)
     {
      out.reason = "上抜けだが終値がトレンドEMAの下のため見送り";
      return(true);
     }
   if(cross_down && out.price >= trend_now)
     {
      out.reason = "下抜けだが終値がトレンドEMAの上のため見送り";
      return(true);
     }

   double sl_distance = atr_now * m_p.sl_atr_mult;
   double tp_distance = sl_distance * m_p.rr_ratio;

   if(cross_up)
     {
      out.direction = TT_SIGNAL_BUY;
      out.sl        = out.price - sl_distance;
      out.tp        = out.price + tp_distance;
     }
   else
     {
      out.direction = TT_SIGNAL_SELL;
      out.sl        = out.price + sl_distance;
      out.tp        = out.price - tp_distance;
     }

   out.reason = StringFormat("EMA%d/%d %s・終値がEMA%dの%s・ADX %.1f",
                             m_p.ema_fast, m_p.ema_slow,
                             (cross_up ? "上抜け" : "下抜け"),
                             m_p.ema_trend,
                             (cross_up ? "上" : "下"),
                             adx_now);
   return(true);
  }

//--- 表示・ログ・配信で共通に使う文字列化
string TTSignalDirectionToString(const ENUM_TT_SIGNAL d)
  {
   if(d == TT_SIGNAL_BUY)  return("BUY");
   if(d == TT_SIGNAL_SELL) return("SELL");
   return("NONE");
  }

#endif // __TT_SIGNAL_CORE_MQH__
