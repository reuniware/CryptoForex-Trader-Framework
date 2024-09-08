// Simulation : Open position on a DAILY SWING HIGH and close it on a DAILY SWING LOW
// There is no logic to use this code. I just created it out of curiosity. 
// It simulates entering a position when a "daily swing high" is detected 
// and closes the position when a "daily swing low" is detected. Nothing
// in this code is derived from ICT work. It's just out of curiosity. Do
// not use or integrate into an EA for real trading unless you know what 
// you are doing. What stands out from this code is that it works better on BTCUSD.
// I'm actually using it on a demo account but on 1m timeframe.
// This is pure randomness and this has nothing to do with what Huddleston teaches
// in term of trading according to "ICT" principles.
// *** THIS IS NOT ICT AND THIS IS A PURE RANDOM TEST ***

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
datetime lastDetectedTime = 0; // Global variable to store the last detected time

void OnTick()
{
    string symbol = Symbol(); // Get the current symbol
        
    // Get the last 3 completed candles (excluding the current open candle)
    MqlRates rates[];
    int copied = CopyRates(symbol, PERIOD_CURRENT, 0, 3, rates);
    
    if(copied != 3)
    {
        Print("Failed to copy rates for symbol: ", symbol);
        return;
    }
    
    // Check if the last detected time is the same as the current time
    if(lastDetectedTime == rates[0].time)
    {
        // Same pattern detected, do nothing
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
        
        // Update the last detected time
        lastDetectedTime = rates[0].time;
        
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
        
        // Update the last detected time
        lastDetectedTime = rates[0].time;
        
        // Close long if in a long position
        if(PositionSelect(symbol))
        {
            ulong positionTicket = PositionGetInteger(POSITION_TICKET);
            double exitPrice = rates[2].close; // Exit long at the close of the third candle
            Print("Exited long at ", exitPrice, " on ", symbol);
            
            // Execute real trade to close the position
            ExecuteTrade(symbol, ORDER_TYPE_SELL, exitPrice, positionTicket);
        }
    }
}
//+------------------------------------------------------------------+
//| Execute Trade Function                                           |
//+------------------------------------------------------------------+
void ExecuteTrade(string symbol, int orderType, double price, ulong positionTicket = 0)
{
    double lotSize = 5; // Define your lot size here
    int slippage = 10; // Define your slippage here
    double stopLoss = 0; // Define your stop loss here
    double takeProfit = 0; // Define your take profit here
    
    MqlTradeRequest request;
    MqlTradeResult result;
    
    ZeroMemory(request);
    ZeroMemory(result);
    
    request.symbol = symbol;
    request.volume = lotSize;
    request.type = orderType;
    request.price = price;
    request.sl = stopLoss;
    request.tp = takeProfit;
    request.deviation = slippage;
    request.type_filling = ORDER_FILLING_FOK;
    
    // Validate the price
    double bidPrice = SymbolInfoDouble(symbol, SYMBOL_BID);
    double askPrice = SymbolInfoDouble(symbol, SYMBOL_ASK);
    
    if(orderType == ORDER_TYPE_BUY)
    {
        // For buy orders, use the ask price
        request.price = askPrice;
    }
    else if(orderType == ORDER_TYPE_SELL)
    {
        // For sell orders, use the bid price
        request.price = bidPrice;
    }
    
    // If positionTicket is provided, it means we are closing a position
    if(positionTicket != 0)
    {
        request.action = TRADE_ACTION_DEAL;
        request.position = positionTicket;
    }
    else
    {
        request.action = TRADE_ACTION_DEAL;
    }
    
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
