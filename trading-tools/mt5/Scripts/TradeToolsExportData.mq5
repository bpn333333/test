//+------------------------------------------------------------------+
//| TradeToolsExportData.mq5 — バックテスト用 OHLC 書き出し           |
//| 出力: <共有フォルダ>/Files/TradeTools/<SYMBOL>_<TIMEFRAME>.csv    |
//| このファイル名は Python 側の backtest CLI が読む形式と一致する。   |
//|                                                                  |
//| 使い方:                                                          |
//|   1. ツール → オプション → チャート → 「ヒストリー内の最大バー数」 |
//|      を無制限にする                                              |
//|   2. 対象銘柄・対象時間軸のチャートを開き、過去まで十分スクロール  |
//|      してヒストリーをダウンロードする                            |
//|   3. そのチャートでこのスクリプトを実行                          |
//|   4. 出力CSVを trading-tools/data/ にコピー                       |
//+------------------------------------------------------------------+
#property copyright "TradeTools"
#property version   "1.00"
#property script_show_inputs

input string InpSymbols   = "USDJPY,EURUSD,GBPUSD";  // カンマ区切り。空なら現在の銘柄
input int    InpBars      = 100000;                  // 書き出す最大本数
input bool   InpUseChartTimeframe = true;            // チャートの時間軸を使う
input ENUM_TIMEFRAMES InpTimeframe = PERIOD_H1;      // 上がfalseのときの時間軸

int ExportOne(const string symbol, const ENUM_TIMEFRAMES tf)
  {
   if(!SymbolSelect(symbol, true))
     {
      PrintFormat("%s: 気配値に追加できません", symbol);
      return(0);
     }

   int available = Bars(symbol, tf);
   if(available <= 0)
     {
      PrintFormat("%s %s: ヒストリーがありません。チャートを開いて過去までスクロールしてください",
                  symbol, EnumToString(tf));
      return(0);
     }

   int count = MathMin(InpBars, available);

   MqlRates rates[];
   ArraySetAsSeries(rates, false);
   int copied = CopyRates(symbol, tf, 0, count, rates);
   if(copied <= 0)
     {
      PrintFormat("%s %s: レートを取得できません err=%d", symbol, EnumToString(tf), GetLastError());
      return(0);
     }

   string filename = StringFormat("TradeTools\\%s_%s.csv", symbol, EnumToString(tf));
   int handle = FileOpen(filename, FILE_WRITE | FILE_TXT | FILE_ANSI | FILE_COMMON);
   if(handle == INVALID_HANDLE)
     {
      PrintFormat("%s: ファイルを開けません err=%d", filename, GetLastError());
      return(0);
     }

   int digits = (int)SymbolInfoInteger(symbol, SYMBOL_DIGITS);
   FileWriteString(handle, "time,open,high,low,close\r\n");

   for(int i = 0; i < copied; i++)
     {
      FileWriteString(handle, StringFormat("%s,%s,%s,%s,%s\r\n",
                                           TimeToString(rates[i].time, TIME_DATE | TIME_SECONDS),
                                           DoubleToString(rates[i].open,  digits),
                                           DoubleToString(rates[i].high,  digits),
                                           DoubleToString(rates[i].low,   digits),
                                           DoubleToString(rates[i].close, digits)));
     }

   FileClose(handle);
   PrintFormat("%s %s: %d 本 → %s (%s 〜 %s)",
               symbol, EnumToString(tf), copied, filename,
               TimeToString(rates[0].time, TIME_DATE),
               TimeToString(rates[copied - 1].time, TIME_DATE));
   return(copied);
  }

void OnStart(void)
  {
   if(!FolderCreate("TradeTools", FILE_COMMON))
      ResetLastError();

   ENUM_TIMEFRAMES tf = InpUseChartTimeframe ? (ENUM_TIMEFRAMES)_Period : InpTimeframe;

   string list = InpSymbols;
   StringTrimLeft(list);
   StringTrimRight(list);
   if(list == "")
      list = _Symbol;

   string symbols[];
   int total = StringSplit(list, ',', symbols);
   int exported = 0;

   for(int i = 0; i < total; i++)
     {
      string symbol = symbols[i];
      StringTrimLeft(symbol);
      StringTrimRight(symbol);
      if(symbol == "")
         continue;
      if(ExportOne(symbol, tf) > 0)
         exported++;
     }

   PrintFormat("完了: %d 銘柄を書き出しました。共有フォルダ MQL5/Files/TradeTools/ を確認してください", exported);
  }
