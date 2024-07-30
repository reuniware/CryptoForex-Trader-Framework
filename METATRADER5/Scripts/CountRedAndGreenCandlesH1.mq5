//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
  {
   // Get the total number of bars in the chart
   int totalBars = Bars(Symbol(), PERIOD_CURRENT) - 1;

   // Initialize arrays to store the number of green and red candles for each hour
   int greenCandles[24] = {0};
   int redCandles[24] = {0};

   // Iterate through the history
   for (int i = 1; i <= totalBars; i++)
     {
      // Get the hour of the current candle
      datetime time = iTime(_Symbol, PERIOD_CURRENT, i);
      MqlDateTime dateTime;
      TimeToStruct(time, dateTime);
      int hour = dateTime.hour;

      // Get the open and close prices of the current candle
      double openPrice = iOpen(_Symbol, PERIOD_CURRENT, i);
      double closePrice = iClose(_Symbol, PERIOD_CURRENT, i);

      // Check if the current candle is green or red
      if (closePrice > openPrice)
        {
         // Increment the number of green candles for the current hour
         greenCandles[hour]++;
        }
      else if (closePrice < openPrice)
        {
         // Increment the number of red candles for the current hour
         redCandles[hour]++;
        }
     }

   // Print the number of green and red candles for each hour
   for (int i = 0; i < 24; i++)
     {
      Print("Hour ", i, ": Green candles = ", greenCandles[i], ", Red candles = ", redCandles[i]);
     }

   return INIT_SUCCEEDED;
  }

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
  {
   // Nothing to clean up in this simple example
  }

//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
  {
   // No need for the OnTick function in this version of the code
  }
