//+------------------------------------------------------------------+
//|                                              DownloadHistory.mq5 |
//|                                Copyright 2024, Reuniware Systems |
//|                                     https://github.com/reuniware |
//+------------------------------------------------------------------+
#property copyright "Copyright 2024, Reuniware Systems"
#property link      "https://github.com/reuniware"
#property version   "1.00"

// Define parameters
input ENUM_TIMEFRAMES timeframe = PERIOD_D1; // Timeframe (e.g., daily)

void OnStart()
  {
   // Get the current chart symbol
   string symbol = Symbol();

   // Ensure the symbol is available
   if(!SymbolSelect(symbol, true))
     {
      Print("Symbol not available: ", symbol);
      return;
     }

   // Prepare an array to store the historical data
   MqlRates rates[];
   
   // Retrieve the maximum available historical data
   int copied = CopyRates(symbol, timeframe, 0, INT_MAX, rates);
   if (copied <= 0)
     {
      Print("Failed to retrieve data.");
      return;
     }

   // Determine the date range
   datetime startDate = rates[0].time;
   datetime endDate = rates[copied - 1].time;

   // Format the date range and timeframe
   string startDateStr = TimeToString(startDate, TIME_DATE);
   string endDateStr = TimeToString(endDate, TIME_DATE);
   string timeframeStr = EnumToString(timeframe);

   // Construct the filename
   string filename = symbol + "_" + startDateStr + "_to_" + endDateStr + "_" + timeframeStr + ".csv";

   // Open the file for writing
   int handle = FileOpen(filename, FILE_WRITE | FILE_CSV | FILE_ANSI);
   if(handle == INVALID_HANDLE)
     {
      Print("Failed to open file: ", filename);
      return;
     }

   // Write the header to the file
   FileWrite(handle, "Date", "Open", "High", "Low", "Close", "Tick Volume", "Spread", "Real Volume");

   // Write data to the file
   for (int i = 0; i < copied; i++)
     {
      FileWrite(handle,
                TimeToString(rates[i].time, TIME_DATE | TIME_MINUTES),
                rates[i].open,
                rates[i].high,
                rates[i].low,
                rates[i].close,
                rates[i].tick_volume,
                rates[i].spread,
                rates[i].real_volume);
     }

   // Close the file
   FileClose(handle);

   Print("Data successfully saved to ", filename);
  }
//+------------------------------------------------------------------+
