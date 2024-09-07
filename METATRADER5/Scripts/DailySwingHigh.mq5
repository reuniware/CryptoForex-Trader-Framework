//+------------------------------------------------------------------------------------------------------------------------------------+
//| Script program start function                                                                                                      |
//| Inspired by ICT - Mastering High Probability Scalping Vol. 1 of 3 - Huddleston                                                     |
//|https://www.youtube.com/watch?v=uE-aaP16nOw&list=PLVgHx4Z63paYdrA3rupIlFhsYFA07GJGP                                                 |
//+------------------------------------------------------------------------------------------------------------------------------------+
void OnStart()
{
    // Get the list of all symbols in the Market Watch
    string symbols[];
    int symbolCount = SymbolsTotal(true);
    ArrayResize(symbols, symbolCount);
    
    for(int i = 0; i < symbolCount; i++)
    {
        symbols[i] = SymbolName(i, true);
    }
    
    // Loop through each symbol
    for(int s = 0; s < symbolCount; s++)
    {
        string symbol = symbols[s];
        
        // Get the last 100 candles
        MqlRates rates[];
        int copied = CopyRates(symbol, PERIOD_CURRENT, 0, 10, rates);
        
        if(copied != 10)
        {
            Print("Failed to copy rates for symbol: ", symbol);
            continue;
        }
        
        // Scan candles 3 by 3
        for(int i = 0; i < 8; i++) // 98 because we are checking 3 candles at a time
        {
            MqlRates candle1 = rates[i];
            MqlRates candle2 = rates[i + 1];
            MqlRates candle3 = rates[i + 2];
            
            // Check the pattern condition
            if(candle1.high > candle2.high && candle3.high > candle2.high && candle3.high < candle1.high)
            {
                // Pattern detected
                Print("Pattern detected on ", symbol, " at times: ", 
                      TimeToString(candle1.time), ", ", 
                      TimeToString(candle2.time), ", ", 
                      TimeToString(candle3.time));
                
                // Switch to the chart of the detected symbol
                long chartId = ChartFirst();
                while(ChartSymbol(chartId) != symbol)
                {
                    chartId = ChartNext(chartId);
                    if(chartId == -1)
                    {
                        Print("Chart for symbol ", symbol, " not found.");
                        break;
                    }
                }
                
                if(chartId != -1)
                {
                    // Draw an arrow under the middle candle (candle2)
                    string arrowName = symbol + "_Arrow_" + IntegerToString(candle2.time);
                    if(ObjectCreate(chartId, arrowName, OBJ_ARROW_UP, 0, candle2.time, candle2.low - 10 * _Point))
                    {
                        ObjectSetInteger(chartId, arrowName, OBJPROP_COLOR, clrRed); // Set arrow color
                        ObjectSetInteger(chartId, arrowName, OBJPROP_WIDTH, 2); // Set arrow width
                    }
                }
            }
        }
    }
}
//+------------------------------------------------------------------+
