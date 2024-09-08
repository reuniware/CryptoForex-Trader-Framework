//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
    // Initialization code here
    return(INIT_SUCCEEDED);
}
//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
    // Deinitialization code here
}
//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
{
    string symbol = Symbol(); // Get the current symbol
    
    // Get the last 3 candles
    MqlRates rates[];
    int copied = CopyRates(symbol, PERIOD_CURRENT, 0, 3, rates);
    
    if(copied != 3)
    {
        Print("Failed to copy rates for symbol: ", symbol);
        return;
    }
    
    // Check the first pattern condition (Green Criteria)
    if(rates[0].high > rates[1].high && rates[2].high > rates[1].high && rates[2].high < rates[0].high)
    {
        // Pattern detected
        Print("Green Criteria detected on ", symbol, " at times: ", 
              TimeToString(rates[0].time), ", ", 
              TimeToString(rates[1].time), ", ", 
              TimeToString(rates[2].time));
        
        // Enter long if not already in a long position
        if(!PositionSelect(symbol))
        {
            double entryPrice = rates[2].close; // Enter long at the close of the third candle
            Print("Entered long at ", entryPrice, " on ", symbol);
            
            // Execute real trade
            ExecuteTrade(symbol, ORDER_TYPE_BUY, entryPrice);
        }
    }
    
    // Check the second pattern condition (Red Criteria)
    if(rates[0].low > rates[1].low && rates[2].low > rates[1].low && rates[2].low < rates[0].low)
    {
        // Pattern detected
        Print("Red Criteria detected on ", symbol, " at times: ", 
              TimeToString(rates[0].time), ", ", 
              TimeToString(rates[1].time), ", ", 
              TimeToString(rates[2].time));
        
        // Close long if in a long position
        if(PositionSelect(symbol))
        {
            double exitPrice = rates[2].close; // Exit long at the close of the third candle
            Print("Exited long at ", exitPrice, " on ", symbol);
            
            // Execute real trade
            ExecuteTrade(symbol, ORDER_TYPE_SELL, exitPrice);
        }
    }
}
//+------------------------------------------------------------------+
//| Execute Trade Function                                           |
//+------------------------------------------------------------------+
void ExecuteTrade(string symbol, int orderType, double price)
{
    double lotSize = 5; // Define your lot size here
    int slippage = 10; // Define your slippage here
    double stopLoss = 0; // Define your stop loss here
    double takeProfit = 0; // Define your take profit here
    
    MqlTradeRequest request;
    MqlTradeResult result;
    
    ZeroMemory(request);
    ZeroMemory(result);
    
    request.action = TRADE_ACTION_DEAL;
    request.symbol = symbol;
    request.volume = lotSize;
    request.type = orderType;
    request.price = price;
    request.sl = stopLoss;
    request.tp = takeProfit;
    request.deviation = slippage;
    request.type_filling = ORDER_FILLING_FOK;
    
    if(!OrderSend(request, result))
    {
        Print("OrderSend failed: ", result.retcode);
    }
    else
    {
        Print("OrderSend succeeded: ", result.retcode);
    }
}
//+------------------------------------------------------------------+
