#include <Trade\Trade.mqh>

CTrade trade;

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
  {
   // Initialization successful
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
   static datetime lastCheckedCandleTime = 0;
   datetime currentCandleTime = iTime(Symbol(), Period(), 1); // Time of the just finished candle
   
   // Check if the just finished candle is different from the last checked candle
   if(currentCandleTime != lastCheckedCandleTime)
     {
      // Update the last checked candle time
      lastCheckedCandleTime = currentCandleTime;
      
      // Call the function to detect the specified pattern on the just finished candle and the one before it
      DetectCandlePattern();
     }
  }
//+------------------------------------------------------------------+
//| Function to detect the specified candle pattern                  |
//+------------------------------------------------------------------+
void DetectCandlePattern()
  {
   int totalCandles = 3; // Number of past candles to check (current + 2 previous)
   double percentageThreshold = 0.0001; // 0.01% threshold
   double pipValue = 100 * _Point; // 10 pips in points
   
   MqlRates rates[];
   ArraySetAsSeries(rates, true);
   int copied = CopyRates(Symbol(), Period(), 0, totalCandles, rates);
   
   if(copied < totalCandles)
     {
      Print("Failed to copy rates");
      return;
     }
   
   // Check the last two completed candles
   double open1 = rates[2].open;  // (n-2) candle
   double close1 = rates[2].close; // (n-2) candle
   double open2 = rates[1].open;  // (n-1) candle
   double close2 = rates[1].close; // (n-1) candle
   
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
      Print("Pattern detected at ", rates[1].time);
      
      // Open a long trade
      double price = SymbolInfoDouble(Symbol(), SYMBOL_ASK);
      double sl = 0;//price - pipValue;
      double tp = price + pipValue;
      trade.Buy(5.0, Symbol(), price, sl, tp, "Long Trade");
      
      if(trade.ResultRetcode() == TRADE_RETCODE_DONE)
        {
         Print("Long trade opened successfully with ticket ", trade.ResultOrder());
        }
      else
        {
         Print("Failed to open long trade. Error code: ", trade.ResultRetcode());
        }
     }
  }
//+------------------------------------------------------------------+
