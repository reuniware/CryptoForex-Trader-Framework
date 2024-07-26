//+------------------------------------------------------------------+
//|                                              DownloadHistory.mq5 |
//|                                  Copyright 2024, MetaQuotes Ltd. |
//|                                             https://www.mql5.com |
//+------------------------------------------------------------------+
#property copyright "Copyright 2024, MetaQuotes Ltd."
#property link      "https://www.mql5.com"
#property version   "1.00"

// Define parameters
input string symbol = "EURUSD";  // Symbol to download
input ENUM_TIMEFRAMES timeframe = PERIOD_D1; // Timeframe (e.g., daily)
input datetime startDate = D'2023.01.01 00:00'; // Start date
input datetime endDate = D'2023.12.31 23:59';   // End date

void OnStart()
  {
   // Ensure the symbol is available
   if(!SymbolSelect(symbol, true))
     {
      Print("Symbol not available: ", symbol);
      return;
     }

   // Prepare an array to store the historical data
   MqlRates rates[];
   
   // Retrieve historical data
   int copied = CopyRates(symbol, timeframe, startDate, endDate, rates);
   if (copied <= 0)
     {
      Print("Failed to retrieve data.");
      return;
     }

   // Output results (for debugging)
   for (int i = 0; i < copied; i++)
     {
      Print("Date: ", TimeToString(rates[i].time),
            " Open: ", rates[i].open,
            " High: ", rates[i].high,
            " Low: ", rates[i].low,
            " Close: ", rates[i].close,
            " Tick Volume: ", rates[i].tick_volume);
     }
  }
//+------------------------------------------------------------------+
