//+------------------------------------------------------------------+
//|                                          IchimokuBreakoutStrategy.mq5|
//|                                Copyright 2024, Reuniware Systems |
//|                                     https://github.com/reuniware |
//| This strategy makes +30% from 01/01/2024 to 26/07/2024 on XAUEUR |
//| in 15m timeframe                                                 |
//+------------------------------------------------------------------+
#property copyright "Copyright 2024, Reuniware Systems"
#property link      "https://github.com/reuniware"
#property version   "1.00"
#property strict

input double lot_size = 0.1;              // Fixed lot size for trades
input double take_profit_percent = 1.0;   // Take profit in percent
input double stop_loss_percent = 1.0;     // Stop loss in percent
input int tenkan_sen_period = 9;          // Period for Tenkan Sen calculation
input int kijun_sen_period = 26;          // Period for Kijun Sen calculation
input int senkou_span_b_period = 52;      // Period for Senkou Span B calculation

double open_price = 0.0;                // To store the price at which the position was opened
bool position_open = false;             // Flag to check if a position is currently open
int position_ticket = -1;               // To store the ticket number of the position

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
  {
   Print("IchimokuBreakoutStrategy initialized");
   return INIT_SUCCEEDED;
  }

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
  {
   // Close any open positions if necessary
   if (position_open)
     {
      double current_price = SymbolInfoDouble(_Symbol, SYMBOL_BID);

      // Prepare trade request to close the position
      MqlTradeRequest request = {};
      MqlTradeResult result = {};
      
      request.action   = TRADE_ACTION_DEAL;
      request.symbol   = _Symbol;
      request.volume   = PositionGetDouble(POSITION_VOLUME);
      request.type     = PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY ? ORDER_TYPE_SELL : ORDER_TYPE_BUY;
      request.price    = current_price;
      request.deviation = 10; // Max allowed deviation
      request.type_filling = ORDER_FILLING_FOK;
      request.type_time = ORDER_TIME_GTC;
      request.position = PositionGetInteger(POSITION_TICKET);

      if (OrderSend(request, result))
        {
         if (result.retcode == TRADE_RETCODE_DONE)
           {
            position_open = false;
            Print("Position closed successfully at price: ", current_price);
           }
         else
           {
            Print("Failed to close position. Error code: ", result.retcode);
           }
        }
      else
        {
         Print("OrderSend failed. Error: ", GetLastError());
        }
     }
  }

//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
  {
   // Get the current period (timeframe)
   ENUM_TIMEFRAMES timeframe = (ENUM_TIMEFRAMES)Period();

   // Calculate the Tenkan Sen (Conversion Line) value
   double tenkan_sen = CalculateTenkanSen(_Symbol, timeframe, tenkan_sen_period);

   // Calculate the Kijun Sen (Base Line) value
   double kijun_sen = CalculateKijunSen(_Symbol, timeframe, kijun_sen_period);

   // Calculate the Senkou Span A (Leading Span A) value
   double senkou_span_a = CalculateSenkouSpanA(_Symbol, timeframe, tenkan_sen, kijun_sen);

   // Calculate the Senkou Span B (Leading Span B) value
   double senkou_span_b = CalculateSenkouSpanB(_Symbol, timeframe, senkou_span_b_period);

   // Retrieve the close price of the current candle
   double current_close = iClose(_Symbol, timeframe, 0);

   // Retrieve the close price of the previous candle
   double previous_close = iClose(_Symbol, timeframe, 1);

   // Current price
   double current_price = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   double ask_price = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   
   // Check if a position is currently open
   if (PositionSelect(_Symbol))
     {
      position_open = true;
      open_price = PositionGetDouble(POSITION_PRICE_OPEN);
     }
   else
     {
      position_open = false;
     }

   if (position_open)
     {
      // Check if the position has reached the take profit or stop loss
      double profit_percent = (current_price - open_price) / open_price * 100;
      if (profit_percent >= take_profit_percent)
        {
         ClosePosition();
        }
      else if (profit_percent <= -stop_loss_percent)
        {
         ClosePosition();
        }
     }
   else
     {
      // Check if there are any open positions
      if (PositionsTotal() == 0)
        {
         // Enter a long position when the current candle closes above all the Ichimoku levels
         if (current_close > tenkan_sen && current_close > kijun_sen && current_close > senkou_span_a && current_close > senkou_span_b &&
             previous_close <= tenkan_sen && previous_close <= kijun_sen && previous_close <= senkou_span_a && previous_close <= senkou_span_b)
           {
            Print("Current candle closed above all Ichimoku levels");
            Print("Current Close: ", current_close, " Tenkan Sen: ", tenkan_sen, " Kijun Sen: ", kijun_sen, " Senkou Span A: ", senkou_span_a, " Senkou Span B: ", senkou_span_b);
            OpenPosition(ORDER_TYPE_BUY, ask_price);
           }
        }
     }
  }

//+------------------------------------------------------------------+
//| Open a position                                                  |
//+------------------------------------------------------------------+
void OpenPosition(ENUM_ORDER_TYPE order_type, double price)
  {
   // Prepare trade request to open a position
   MqlTradeRequest request = {};
   MqlTradeResult result = {};
   
   request.action   = TRADE_ACTION_DEAL;
   request.symbol   = _Symbol;
   request.volume   = NormalizeVolume(lot_size, _Symbol); // Normalized lot size
   request.type     = order_type;
   request.price    = price;
   request.deviation = 10; // Max allowed deviation
   request.type_filling = ORDER_FILLING_FOK;
   request.type_time = ORDER_TIME_GTC;

   // Calculate take profit and stop loss levels
   request.tp = price * (1 + take_profit_percent / 100);
   request.sl = price * (1 - stop_loss_percent / 100);

   if (OrderSend(request, result))
     {
      if (result.retcode == TRADE_RETCODE_DONE)
        {
         open_price = price; // Record the open price
         position_open = true;
         position_ticket = result.order;
         Print("Position opened successfully at price: ", open_price);

         // Display take profit and stop loss levels on the chart
         string tp_label = "TP_" + IntegerToString(position_ticket);
         string sl_label = "SL_" + IntegerToString(position_ticket);
         ObjectCreate(0, tp_label, OBJ_HLINE, 0, 0, request.tp);
         ObjectCreate(0, sl_label, OBJ_HLINE, 0, 0, request.sl);
         ObjectSetInteger(0, tp_label, OBJPROP_COLOR, clrGreen);
         ObjectSetInteger(0, sl_label, OBJPROP_COLOR, clrRed);
         ObjectSetInteger(0, tp_label, OBJPROP_STYLE, STYLE_DASH);
         ObjectSetInteger(0, sl_label, OBJPROP_STYLE, STYLE_DASH);
         ObjectSetInteger(0, tp_label, OBJPROP_WIDTH, 1);
         ObjectSetInteger(0, sl_label, OBJPROP_WIDTH, 1);
         ObjectSetInteger(0, tp_label, OBJPROP_BACK, true);
         ObjectSetInteger(0, sl_label, OBJPROP_BACK, true);
         Comment("Take Profit Level: ", request.tp, " Stop Loss Level: ", request.sl);
        }
      else
        {
         Print("Failed to open position. Error code: ", result.retcode);
        }
     }
   else
     {
      Print("OrderSend failed. Error: ", GetLastError());
     }
  }

//+------------------------------------------------------------------+
//| Close a position                                                 |
//+------------------------------------------------------------------+
void ClosePosition()
  {
   double current_price = SymbolInfoDouble(_Symbol, SYMBOL_BID);

   // Prepare trade request to close the position
   MqlTradeRequest request = {};
   MqlTradeResult result = {};
   
   request.action   = TRADE_ACTION_DEAL;
   request.symbol   = _Symbol;
   request.volume   = PositionGetDouble(POSITION_VOLUME);
   request.type     = PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY ? ORDER_TYPE_SELL : ORDER_TYPE_BUY;
   request.price    = current_price;
   request.deviation = 10; // Max allowed deviation
   request.type_filling = ORDER_FILLING_FOK;
   request.type_time = ORDER_TIME_GTC;
   request.position = PositionGetInteger(POSITION_TICKET);

   if (OrderSend(request, result))
     {
      if (result.retcode == TRADE_RETCODE_DONE)
        {
         position_open = false;
         Print("Position closed successfully at price: ", current_price);

         // Remove take profit and stop loss levels from the chart
         string tp_label = "TP_" + IntegerToString(position_ticket);
         string sl_label = "SL_" + IntegerToString(position_ticket);
         ObjectDelete(0, tp_label);
         ObjectDelete(0, sl_label);
        }
      else
        {
         Print("Failed to close position. Error code: ", result.retcode);
        }
     }
   else
     {
      Print("OrderSend failed. Error: ", GetLastError());
     }
  }

//+------------------------------------------------------------------+
//| Normalize volume according to symbol's volume constraints        |
//+------------------------------------------------------------------+
double NormalizeVolume(double volume, string symbol)
  {
   double min_volume = SymbolInfoDouble(symbol, SYMBOL_VOLUME_MIN);
   double max_volume = SymbolInfoDouble(symbol, SYMBOL_VOLUME_MAX);
   double volume_step = SymbolInfoDouble(symbol, SYMBOL_VOLUME_STEP);

   int steps = (int)MathRound((volume - min_volume) / volume_step);
   double normalized_volume = min_volume + steps * volume_step;

   if (normalized_volume > max_volume)
      normalized_volume = max_volume;

   return normalized_volume;
  }

//+------------------------------------------------------------------+
//| Calculate Tenkan Sen (Conversion Line)                           |
//+------------------------------------------------------------------+
double CalculateTenkanSen(string symbol, ENUM_TIMEFRAMES timeframe, int period)
  {
   double highest_high = iHigh(symbol, timeframe, iHighest(symbol, timeframe, MODE_HIGH, period, 1));
   double lowest_low = iLow(symbol, timeframe, iLowest(symbol, timeframe, MODE_LOW, period, 1));
   return (highest_high + lowest_low) / 2;
  }

//+------------------------------------------------------------------+
//| Calculate Kijun Sen (Base Line)                                  |
//+------------------------------------------------------------------+
double CalculateKijunSen(string symbol, ENUM_TIMEFRAMES timeframe, int period)
  {
   double highest_high = iHigh(symbol, timeframe, iHighest(symbol, timeframe, MODE_HIGH, period, 1));
   double lowest_low = iLow(symbol, timeframe, iLowest(symbol, timeframe, MODE_LOW, period, 1));
   return (highest_high + lowest_low) / 2;
  }

//+------------------------------------------------------------------+
//| Calculate Senkou Span A (Leading Span A)                         |
//+------------------------------------------------------------------+
double CalculateSenkouSpanA(string symbol, ENUM_TIMEFRAMES timeframe, double tenkan_sen, double kijun_sen)
  {
   return (tenkan_sen + kijun_sen) / 2;
  }

//+------------------------------------------------------------------+
//| Calculate Senkou Span B (Leading Span B)                         |
//+------------------------------------------------------------------+
double CalculateSenkouSpanB(string symbol, ENUM_TIMEFRAMES timeframe, int period)
  {
   double highest_high = iHigh(symbol, timeframe, iHighest(symbol, timeframe, MODE_HIGH, period, 1));
   double lowest_low = iLow(symbol, timeframe, iLowest(symbol, timeframe, MODE_LOW, period, 1));
   return (highest_high + lowest_low) / 2;
  }
//+------------------------------------------------------------------+
