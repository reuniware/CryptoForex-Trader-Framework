//+------------------------------------------------------------------+
//| Script program start function                                    |
//+------------------------------------------------------------------+
void OnStart()
  {
   // Delete all objects on the chart
   ObjectsDeleteAll(0, -1, -1);

   // Check for swing highs and lows
   CheckForSwingHighsLows();
  }
//+------------------------------------------------------------------+
//| Function to check for swing highs and lows                        |
//+------------------------------------------------------------------+
void CheckForSwingHighsLows()
  {
   // Get the number of bars on the current chart
   int bars = Bars(_Symbol, _Period);
   
   // Loop through the bars to find swing highs and lows
   for(int i = bars - 3; i >= 0; i--)
     {
      // Get the high and low prices for the current and previous bars
      double high1 = iHigh(_Symbol, _Period, i);
      double high2 = iHigh(_Symbol, _Period, i+1);
      double high3 = iHigh(_Symbol, _Period, i+2);
      
      double low1 = iLow(_Symbol, _Period, i);
      double low2 = iLow(_Symbol, _Period, i+1);
      double low3 = iLow(_Symbol, _Period, i+2);
      
      // Check for swing high
      if(high2 > high1 && high2 > high3)
        {
         // Draw an arrow sufficiently above the high of the middle candlestick of the swing high
         string arrowName = "SwingHigh_" + IntegerToString(i+1);
         datetime time = iTime(_Symbol, _Period, i+1);
         double high = iHigh(_Symbol, _Period, i+1);
         double offset = SymbolInfoDouble(_Symbol, SYMBOL_POINT) * 20; // Adjust the offset as needed
         ObjectCreate(_Symbol, arrowName, OBJ_ARROW_SELL, 0, time, high + offset);
         ObjectSetInteger(0, arrowName, OBJPROP_COLOR, clrGreen);
        }
      
      // Check for swing low
      if(low2 < low1 && low2 < low3)
        {
         // Draw an arrow just below the low of the middle candlestick of the swing low
         string arrowName = "SwingLow_" + IntegerToString(i+1);
         datetime time = iTime(_Symbol, _Period, i+1);
         double low = iLow(_Symbol, _Period, i+1);
         double offset = SymbolInfoDouble(_Symbol, SYMBOL_POINT) * 20; // Adjust the offset as needed
         ObjectCreate(_Symbol, arrowName, OBJ_ARROW_BUY, 0, time, low - offset);
         ObjectSetInteger(0, arrowName, OBJPROP_COLOR, clrRed);
        }
     }
  }
//+------------------------------------------------------------------+
