//+------------------------------------------------------------------+
//| Script program start function                                    |
//+------------------------------------------------------------------+
void OnStart()
{
    int nbcandles = 100;

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
        
        // Get the last nbcandles candles
        MqlRates rates[];
        int copied = CopyRates(symbol, PERIOD_CURRENT, 0, nbcandles, rates);
        
        if(copied != nbcandles)
        {
            Print("Failed to copy rates for symbol: ", symbol);
            continue;
        }
        
        // Calculate the average candle height
        double avgCandleHeight = 0;
        for(int i = 0; i < nbcandles; i++)
        {
            avgCandleHeight += (rates[i].high - rates[i].low);
        }
        avgCandleHeight /= nbcandles;
        
        // Scan candles 3 by 3
        for(int i = 0; i < nbcandles-2; i++) // nbcandles-2 because we are checking 3 candles at a time
        {
            MqlRates candle1 = rates[i];
            MqlRates candle2 = rates[i + 1];
            MqlRates candle3 = rates[i + 2];
            
            // Check the first pattern condition
            if(candle1.high > candle2.high && candle3.high > candle2.high && candle3.high < candle1.high)
            {
                // Pattern detected
                Print("Pattern 1 detected on ", symbol, " at times: ", 
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
                    string arrowName = symbol + "_Arrow1_" + IntegerToString(candle2.time);
                    double arrowY = candle2.low - 0.5 * avgCandleHeight; // Position arrow below the candle
                    if(ObjectCreate(chartId, arrowName, OBJ_ARROW_UP, 0, candle2.time, arrowY))
                    {
                        ObjectSetInteger(chartId, arrowName, OBJPROP_COLOR, clrRed); // Set arrow color
                        ObjectSetInteger(chartId, arrowName, OBJPROP_WIDTH, 2); // Set arrow width
                    }
                }
            }
            
            // Check the second pattern condition
            if(candle1.low > candle2.low && candle3.low > candle2.low && candle3.low < candle1.low)
            {
                // Pattern detected
                Print("Pattern 2 detected on ", symbol, " at times: ", 
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
                    // Draw an arrow above the middle candle (candle2)
                    string arrowName = symbol + "_Arrow2_" + IntegerToString(candle2.time);
                    double arrowY = candle2.high + 0.7 * avgCandleHeight; // Position arrow above the candle
                    if(ObjectCreate(chartId, arrowName, OBJ_ARROW_DOWN, 0, candle2.time, arrowY))
                    {
                        ObjectSetInteger(chartId, arrowName, OBJPROP_COLOR, clrBlue); // Set arrow color
                        ObjectSetInteger(chartId, arrowName, OBJPROP_WIDTH, 2); // Set arrow width
                    }
                }
            }
        }
    }
}
//+------------------------------------------------------------------+
