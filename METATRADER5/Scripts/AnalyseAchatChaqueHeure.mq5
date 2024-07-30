//+------------------------------------------------------------------+
//| If we bought at the open price each hour and sold at the closing price for each hour with maximum history |
//    Then how many would we have won until today if initial investment is $10000
//+------------------------------------------------------------------+
input double initialInvestment = 10000; // Initial investment in USD

int OnInit()
  {
   // Get the total number of bars in the chart
   int totalBars = Bars(Symbol(), PERIOD_CURRENT) - 1;

   // Initialize arrays to store the potential profit in USD for each hour
   double potentialProfit[24] = {0};

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

      // Calculate the potential profit in pips for the current hour
      double profitInPips = (closePrice - openPrice) * _Point;

      // Calculate the potential profit in USD for the current hour
      double profitInUSD = profitInPips * initialInvestment / _Point;

      // Add the potential profit in USD to the corresponding hour
      potentialProfit[hour] += profitInUSD;
     }

   // Print the potential profit in USD for each hour
   for (int i = 0; i < 24; i++)
     {
      Print("Hour ", i, ": Potential profit in USD = ", potentialProfit[i]);
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
