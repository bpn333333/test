//+------------------------------------------------------------------+
//| SignalFile.mqh                                                   |
//| MT5 と Python(モニタリング・X配信)をつなぐ唯一の受け渡し口。      |
//| 追記専用CSV。MQL5側が書き、Python側は読むだけ(逆流させない)。      |
//| 出力先: <データフォルダ>/MQL5/Files/TradeTools/signals.csv         |
//+------------------------------------------------------------------+
#property copyright "TradeTools"

#ifndef __TT_SIGNAL_FILE_MQH__
#define __TT_SIGNAL_FILE_MQH__

#include <TradeTools/SignalCore.mqh>

#define TT_SIGNAL_DIR    "TradeTools"
#define TT_SIGNAL_FILE   "TradeTools\\signals.csv"
#define TT_SIGNAL_HEADER "signal_id,emitted_at,bar_time,symbol,timeframe,direction,price,sl,tp,atr,adx,source,reason"

//--- 同じ足で二重に書かないための識別子。Python側の重複排除キーでもある
string TTSignalId(const string symbol, const ENUM_TIMEFRAMES tf, const datetime bar_time, const ENUM_TT_SIGNAL dir)
  {
   return(StringFormat("%s-%s-%s-%s",
                       symbol,
                       EnumToString(tf),
                       TimeToString(bar_time, TIME_DATE | TIME_MINUTES),
                       TTSignalDirectionToString(dir)));
  }

//--- ヘッダ行が無ければ作る
bool TTEnsureSignalFile(void)
  {
   if(!FolderCreate(TT_SIGNAL_DIR, FILE_COMMON) && GetLastError() != ERR_DIRECTORY_ALREADY_EXIST)
     {
      ResetLastError();
     }

   if(FileIsExist(TT_SIGNAL_FILE, FILE_COMMON))
      return(true);

   int handle = FileOpen(TT_SIGNAL_FILE, FILE_WRITE | FILE_TXT | FILE_ANSI | FILE_COMMON);
   if(handle == INVALID_HANDLE)
     {
      Print("TTEnsureSignalFile: ファイルを作成できません err=", GetLastError());
      return(false);
     }
   FileWriteString(handle, TT_SIGNAL_HEADER + "\r\n");
   FileClose(handle);
   return(true);
  }

//--- シグナル1件を追記する。source は "indicator" / "ea" など発生源
bool TTAppendSignal(const TTSignal &sig, const string symbol, const ENUM_TIMEFRAMES tf, const string source)
  {
   if(sig.direction == TT_SIGNAL_NONE)
      return(false);
   if(!TTEnsureSignalFile())
      return(false);

   int handle = FileOpen(TT_SIGNAL_FILE, FILE_READ | FILE_WRITE | FILE_TXT | FILE_ANSI | FILE_COMMON);
   if(handle == INVALID_HANDLE)
     {
      Print("TTAppendSignal: ファイルを開けません err=", GetLastError());
      return(false);
     }
   FileSeek(handle, 0, SEEK_END);

   int digits = (int)SymbolInfoInteger(symbol, SYMBOL_DIGITS);

   //--- カンマを含みうるのは reason だけなので、そこだけ引用符で包む
   string line = StringFormat("%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%.1f,%s,\"%s\"",
                              TTSignalId(symbol, tf, sig.time, sig.direction),
                              TimeToString(TimeCurrent(), TIME_DATE | TIME_SECONDS),
                              TimeToString(sig.time, TIME_DATE | TIME_SECONDS),
                              symbol,
                              EnumToString(tf),
                              TTSignalDirectionToString(sig.direction),
                              DoubleToString(sig.price, digits),
                              DoubleToString(sig.sl, digits),
                              DoubleToString(sig.tp, digits),
                              DoubleToString(sig.atr, digits),
                              sig.adx,
                              source,
                              sig.reason);

   FileWriteString(handle, line + "\r\n");
   FileFlush(handle);
   FileClose(handle);
   return(true);
  }

#endif // __TT_SIGNAL_FILE_MQH__
