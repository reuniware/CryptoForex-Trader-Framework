//+------------------------------------------------------------------+
//| Script program start function                                    |
//+------------------------------------------------------------------+
void OnStart()
  {
   // Get the current symbol and timeframe
   string symbol = _Symbol;
   ENUM_TIMEFRAMES timeframe = _Period;

   // Get the last two days' bars
   MqlRates rates[];
   ArraySetAsSeries(rates, true);
   int copied = CopyRates(symbol, timeframe, 0, 2, rates);

   if(copied < 2)
     {
      Alert("Failed to get historical data.");
      return;
     }

   // Get the open and close prices of the previous day
   double prevDayOpen = rates[1].open;
   double prevDayClose = rates[1].close;

   // Get the start and end time of the previous day
   datetime prevDayStartTime = rates[1].time;
   datetime prevDayEndTime = rates[0].time;

   // Create the line for the open price of the previous day
   string openLineName = symbol + "_PrevDayOpen";
   ObjectCreate(0, openLineName, OBJ_HLINE, 0, 0, prevDayOpen);
   ObjectSetInteger(0, openLineName, OBJPROP_COLOR, clrRed);
   ObjectSetInteger(0, openLineName, OBJPROP_STYLE, STYLE_SOLID);
   ObjectSetInteger(0, openLineName, OBJPROP_WIDTH, 1);

   // Create the line for the close price of the previous day
   string closeLineName = symbol + "_PrevDayClose";
   ObjectCreate(0, closeLineName, OBJ_HLINE, 0, 0, prevDayClose);
   ObjectSetInteger(0, closeLineName, OBJPROP_COLOR, clrBlue);
   ObjectSetInteger(0, closeLineName, OBJPROP_STYLE, STYLE_SOLID);
   ObjectSetInteger(0, closeLineName, OBJPROP_WIDTH, 1);

   // Print the open and close prices for debugging
   Print("Previous Day Open: ", prevDayOpen);
   Print("Previous Day Close: ", prevDayClose);
  }
//+-----------------reuniware/dvasoft/2024-------------------------------------------------+
