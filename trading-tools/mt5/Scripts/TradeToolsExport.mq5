//+------------------------------------------------------------------+
//| TradeToolsExport.mq5 — パリティ検証用のエクスポート                |
//| MT5 の OHLC と判定結果を吐き出し、Python 実装と一致するか照合する。 |
//| 使い方:                                                          |
//|   1. 対象チャートでこのスクリプトを実行                            |
//|   2. <データフォルダ>/MQL5/Files/TradeTools/parity_ohlc.csv と     |
//|      parity_signals.csv を trading-tools/data/ にコピー            |
//|   3. python -m pytest tests/test_parity.py                        |
//+------------------------------------------------------------------+
#property copyright "TradeTools"
#property version   "1.00"
#property script_show_inputs

#include <TradeTools/SignalCore.mqh>

input int InpBars = 3000;   // 書き出す本数(warmup を含む)

void OnStart(void)
  {
   TTSignalParams p = TTDefaultParams();

   CTTSignalCore core;
   if(!core.Init(_Symbol, (ENUM_TIMEFRAMES)_Period, p))
     {
      Print("Init 失敗");
      return;
     }

   int available = Bars(_Symbol, (ENUM_TIMEFRAMES)_Period);
   int count = MathMin(InpBars, available);
   if(count <= core.WarmupBars())
     {
      PrintFormat("本数が足りません: %d 本(最低 %d 本必要)", count, core.WarmupBars() + 50);
      return;
     }

   if(!FolderCreate("TradeTools", FILE_COMMON))
      ResetLastError();

   int fo = FileOpen("TradeTools\\parity_ohlc.csv", FILE_WRITE | FILE_TXT | FILE_ANSI | FILE_COMMON);
   int fs = FileOpen("TradeTools\\parity_signals.csv", FILE_WRITE | FILE_TXT | FILE_ANSI | FILE_COMMON);
   if(fo == INVALID_HANDLE || fs == INVALID_HANDLE)
     {
      Print("ファイルを開けません err=", GetLastError());
      return;
     }

   FileWriteString(fo, "time,open,high,low,close\r\n");
   FileWriteString(fs, "bar_time,direction,price,sl,tp,atr,adx\r\n");

   int digits = (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS);

   for(int shift = count - 1; shift >= 1; shift--)
     {
      MqlRates r[];
      if(CopyRates(_Symbol, (ENUM_TIMEFRAMES)_Period, shift, 1, r) != 1)
         continue;

      FileWriteString(fo, StringFormat("%s,%s,%s,%s,%s\r\n",
                                       TimeToString(r[0].time, TIME_DATE | TIME_SECONDS),
                                       DoubleToString(r[0].open,  digits),
                                       DoubleToString(r[0].high,  digits),
                                       DoubleToString(r[0].low,   digits),
                                       DoubleToString(r[0].close, digits)));

      TTSignal sig;
      if(!core.Evaluate(shift, sig) || sig.direction == TT_SIGNAL_NONE)
         continue;

      FileWriteString(fs, StringFormat("%s,%s,%s,%s,%s,%s,%.4f\r\n",
                                       TimeToString(sig.time, TIME_DATE | TIME_SECONDS),
                                       TTSignalDirectionToString(sig.direction),
                                       DoubleToString(sig.price, digits),
                                       DoubleToString(sig.sl,    digits),
                                       DoubleToString(sig.tp,    digits),
                                       DoubleToString(sig.atr,   digits + 2),
                                       sig.adx));
     }

   FileClose(fo);
   FileClose(fs);
   PrintFormat("書き出し完了: %d 本 → 共有フォルダ MQL5/Files/TradeTools/", count);
  }
