//+------------------------------------------------------------------+
//|                                          HighsLowsHorizontal.mq5 |
//|                      Reuniware Systems / DVASyst                 |
//+------------------------------------------------------------------+
#property strict

// Parameters of the EA
input int DaysToCheck = 30; // Number of days to check
input ENUM_TIMEFRAMES Period = PERIOD_D1; // Time period to check

// Unique identifiers for graphical objects
int highLineCount = 0;
int lowLineCount = 0;

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
  {
   // Update lines at startup
   UpdateLines();
   
   // Request EA to call OnTick() at every tick
   EventSetTimer(1);
   
   return(INIT_SUCCEEDED);
  }
//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
  {
   // Delete graphical objects created by EA upon deinitialization
   //ObjectsDeleteAll(0, "HighLine_");
   //ObjectsDeleteAll(0, "LowLine_");
   
   // Stop the timer
   EventKillTimer();
  }
//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
  {
   // Update lines at every tick
   // UpdateLines();
  }
//+------------------------------------------------------------------+
//| Function to update high and low lines                            |
//+------------------------------------------------------------------+
void UpdateLines()
  {
  Print("UpdateLines()");
   // Delete old lines
   //ObjectsDeleteAll(0, "HighLine_");
   //ObjectsDeleteAll(0, "LowLine_");

   // Loop through bars to find highs and lows over the specified period
   for(int i = 1; i <= DaysToCheck; i++)
     {
      double high = iHigh(NULL, Period, i);
      double low = iLow(NULL, Period, i);
      datetime time = iTime(NULL, Period, i);
      
      // Create horizontal lines for each high
      string highLineName = "HighLine_" + IntegerToString(highLineCount++);
      Print(highLineName);
      ObjectCreate(0, highLineName, OBJ_HLINE, 0, 0, high);
      ObjectSetInteger(0, highLineName, OBJPROP_COLOR, clrRed);
      ObjectSetInteger(0, highLineName, OBJPROP_WIDTH, 1);
      ObjectSetInteger(0, highLineName, OBJPROP_STYLE, STYLE_DOT);

      // Create horizontal lines for each low
      string lowLineName = "LowLine_" + IntegerToString(lowLineCount++);
      Print(lowLineName);
      ObjectCreate(0, lowLineName, OBJ_HLINE, 0, 0, low);
      ObjectSetInteger(0, lowLineName, OBJPROP_COLOR, clrBlue);
      ObjectSetInteger(0, lowLineName, OBJPROP_WIDTH, 1);
      ObjectSetInteger(0, lowLineName, OBJPROP_STYLE, STYLE_DOT);
     }
  }
//+------------------------------------------------------------------+
