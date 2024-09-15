//+------------------------------------------------------------------+
//| Input parameters                                                 |
//+------------------------------------------------------------------+
input int CandlesToCheck = 2; // Number of candles to check for equal highs and lows
input int SwingRange = 10; // Number of previous and next candles to check for swing highs and lows

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
   for(int i = bars - SwingRange - 2; i >= SwingRange; i--)
     {
      // Get the high and low prices for the current and previous bars
      double high2 = iHigh(_Symbol, _Period, i+1);
      double low2 = iLow(_Symbol, _Period, i+1);
      
      // Check for swing high
      bool isSwingHigh = true;
      for(int j = i - SwingRange; j <= i + SwingRange; j++)
        {
         if(j != i+1 && iHigh(_Symbol, _Period, j) >= high2)
           {
            isSwingHigh = false;
            break;
           }
        }
      
      if(isSwingHigh)
        {
         // Draw an arrow sufficiently above the high of the middle candlestick of the swing high
         string arrowName = "SwingHigh_" + IntegerToString(i+1);
         datetime time = iTime(_Symbol, _Period, i+1);
         double high = iHigh(_Symbol, _Period, i+1);
         double offset = SymbolInfoDouble(_Symbol, SYMBOL_POINT) * 20; // Adjust the offset as needed
         ObjectCreate(_Symbol, arrowName, OBJ_ARROW_SELL, 0, time, high + offset);
         ObjectSetInteger(0, arrowName, OBJPROP_COLOR, clrGreen);
         
         // Check for equal highs in the last CandlesToCheck candles
         for(int j = i + 2; j < i + 2 + CandlesToCheck && j < bars; j++)
           {
            double currentHigh = iHigh(_Symbol, _Period, j);
            if(MathAbs(currentHigh - high) < SymbolInfoDouble(_Symbol, SYMBOL_POINT))
              {
               // Draw a horizontal line at this high
               string lineName = "HighLine_" + IntegerToString(j);
               ObjectCreate(_Symbol, lineName, OBJ_HLINE, 0, 0, currentHigh);
               ObjectSetInteger(0, lineName, OBJPROP_COLOR, clrGreen);
               ObjectSetInteger(0, lineName, OBJPROP_STYLE, STYLE_DASH);
               break; // Only draw one line per swing high
              }
           }
        }
      
      // Check for swing low
      bool isSwingLow = true;
      for(int j = i - SwingRange; j <= i + SwingRange; j++)
        {
         if(j != i+1 && iLow(_Symbol, _Period, j) <= low2)
           {
            isSwingLow = false;
            break;
           }
        }
      
      if(isSwingLow)
        {
         // Draw an arrow just below the low of the middle candlestick of the swing low
         string arrowName = "SwingLow_" + IntegerToString(i+1);
         datetime time = iTime(_Symbol, _Period, i+1);
         double low = iLow(_Symbol, _Period, i+1);
         double offset = SymbolInfoDouble(_Symbol, SYMBOL_POINT) * 20; // Adjust the offset as needed
         ObjectCreate(_Symbol, arrowName, OBJ_ARROW_BUY, 0, time, low - offset);
         ObjectSetInteger(0, arrowName, OBJPROP_COLOR, clrRed);
         
         // Check for equal lows in the last CandlesToCheck candles
         for(int j = i + 2; j < i + 2 + CandlesToCheck && j < bars; j++)
           {
            double currentLow = iLow(_Symbol, _Period, j);
            if(MathAbs(currentLow - low) < SymbolInfoDouble(_Symbol, SYMBOL_POINT))
              {
               // Draw a horizontal line at this low
               string lineName = "LowLine_" + IntegerToString(j);
               ObjectCreate(_Symbol, lineName, OBJ_HLINE, 0, 0, currentLow);
               ObjectSetInteger(0, lineName, OBJPROP_COLOR, clrRed);
               ObjectSetInteger(0, lineName, OBJPROP_STYLE, STYLE_DASH);
               break; // Only draw one line per swing low
              }
           }
        }
     }
  }
//+------------------------------------------------------------------+

/*Explanation of Changes:
Input Parameter SwingRange: Added a new input parameter SwingRange to specify the number of previous and next candles to check for swing highs and lows.

Loop Adjustment: The loop now starts from bars - SwingRange - 2 and goes up to SwingRange to ensure there are enough candles to check both before and after the current candle.

Swing High Check: Added a loop to check if the high of the current candle (high2) is higher than the highs of the 10 previous and 10 next candles.

Swing Low Check: Added a loop to check if the low of the current candle (low2) is lower than the lows of the 10 previous and 10 next candles.

Drawing Arrows and Lines: The code for drawing arrows and horizontal lines remains the same, but now it only draws them if the swing high or low conditions are met.
*/
