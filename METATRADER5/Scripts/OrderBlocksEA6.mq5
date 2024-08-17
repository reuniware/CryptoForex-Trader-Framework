//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
  {
   // Call the function to detect the specified pattern
   DetectCandlePattern();
   
   return(INIT_SUCCEEDED);
  }
//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
  {
   // Do nothing
  }
//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
  {
   // Do nothing
  }
//+------------------------------------------------------------------+
//| Function to detect the specified candle pattern                  |
//+------------------------------------------------------------------+
void DetectCandlePattern()
  {
   int totalCandles = 100; // Number of past candles to check
   double percentageThreshold = 0.0001; // 0.01% threshold
   
   MqlRates rates[];
   ArraySetAsSeries(rates, true);
   int copied = CopyRates(Symbol(), Period(), 0, totalCandles, rates);
   
   if(copied < totalCandles)
     {
      Print("Failed to copy rates");
      return;
     }
   
   for(int i = 1; i < totalCandles - 1; i++) // Adjust the loop to avoid out-of-range access
     {
      double open1 = rates[i].open;
      double close1 = rates[i].close;
      double open2 = rates[i + 1].open;
      double close2 = rates[i + 1].close;
      
      // Calculate percentage changes
      double percentageChange1 = (open1 - close1) / open1;
      double percentageChange2 = (close2 - open2) / open2;
      
      // Check for the specified pattern
      if(open1 > close1 && // Candle 1 is red
         percentageChange1 >= percentageThreshold && // Candle 1 is down by at least 0.01%
         open2 < close2 && // Candle 2 is green
         percentageChange2 >= percentageThreshold && // Candle 2 is up by at least 0.01%
         open2 > close1 && // Candle 2's open2 > close1
         close2 > open1)   // Candle 2's close2 > open1
        {
         Print("Pattern detected at ", rates[i + 1].time);
        }
     }
  }
//+------------------------------------------------------------------+
