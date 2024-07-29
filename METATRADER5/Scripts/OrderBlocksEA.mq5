//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
  {
   // Detect order blocks when the EA is started
   DetectOrderBlocks(20, 2);
   return(INIT_SUCCEEDED);
  }
//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
  {
   // Deinitialization code
  }
//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
  {
   // EA does not operate on ticks for order block detection
  }
//+------------------------------------------------------------------+
//| Calculate simple moving average                                  |
//+------------------------------------------------------------------+
double CalculateMA(int period, int shift)
  {
   double sum = 0.0;
   for(int i = shift; i < shift + period; i++)
     {
      sum += iClose(NULL, 0, i);
     }
   return sum / period;
  }
//+------------------------------------------------------------------+
//| Order block detection function                                   |
//+------------------------------------------------------------------+
void DetectOrderBlocks(int consolidation_period, double break_threshold)
  {
   int bars = iBars(NULL, 0);
   for(int i = bars - consolidation_period * 2; i >= consolidation_period; i--)
     {
      // Get the range of the consolidation period
      double max_price = iHigh(NULL, 0, iHighest(NULL, 0, MODE_HIGH, consolidation_period, i - consolidation_period));
      double min_price = iLow(NULL, 0, iLowest(NULL, 0, MODE_LOW, consolidation_period, i - consolidation_period));
      double price_range = max_price - min_price;

      // Check if this is a consolidation period (price range within 2% of average price)
      double avg_price = CalculateMA(consolidation_period, i - consolidation_period);
      if(price_range < avg_price * 0.02)
        {
         // Check for a breakout in the following period
         double subsequent_max = iHigh(NULL, 0, iHighest(NULL, 0, MODE_HIGH, consolidation_period, i));
         double subsequent_min = iLow(NULL, 0, iLowest(NULL, 0, MODE_LOW, consolidation_period, i));
         long volume_before = iVolume(NULL, 0, i);
         long volume_after = iVolume(NULL, 0, i + consolidation_period);

         // Confirm breakout with significant price movement and volume increase
         if((subsequent_max > max_price * (1 + break_threshold / 100) || subsequent_min < min_price * (1 - break_threshold / 100)) && volume_after > volume_before * 1.5)
           {
            // Mark the order block on the chart
            datetime start_time = iTime(NULL, 0, i);
            datetime end_time = iTime(NULL, 0, i - consolidation_period);
            string obj_name = "OrderBlock" + IntegerToString(i);
            if(ObjectFind(0, obj_name) == -1)
              {
               ObjectCreate(0, obj_name, OBJ_RECTANGLE, 0, start_time, max_price, end_time, min_price);
               ObjectSetInteger(0, obj_name, OBJPROP_COLOR, clrRed);
               ObjectSetInteger(0, obj_name, OBJPROP_WIDTH, 2);
              }
           }
        }
     }
  }
//+----------Reuniware Systems / DVASystems / 29072024--------------------------------------------------------+
