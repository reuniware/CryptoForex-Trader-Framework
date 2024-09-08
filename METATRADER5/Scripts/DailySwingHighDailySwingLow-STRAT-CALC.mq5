// Simulation : Open position on a DAILY SWING HIGH and close it on a DAILY SWING LOW
// There is no logic to use this code. I just created it out of curiosity. 
// It simulates entering a position when a "daily swing high" is detected 
// and closes the position when a "daily swing low" is detected. Nothing
// in this code is derived from ICT work. It's just out of curiosity. Do
// not use or integrate into an EA for real trading unless you know what 
// you are doing. What stands out from this code is that it works better on BTCUSD.

void OnStart()
{
    int nbcandles = 2000;
    double totalProfit = 0; // Variable to track total profit

    // Get the list of all symbols in the Market Watch
    string symbols[];
    int symbolCount = SymbolsTotal(true);
    ArrayResize(symbols, symbolCount);
    
    for(int i = 0; i < symbolCount; i++)
    {
        symbols[i] = SymbolName(i, true);
    }
    
    // Arrays to store profits and corresponding symbols
    double profits[];
    ArrayResize(profits, symbolCount);
    ArrayInitialize(profits, 0);
    
    // Loop through each symbol
    for(int s = 0; s < symbolCount; s++)
    {
        string symbol = symbols[s];
        double assetProfit = 0; // Variable to track profit for the current asset
        
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
        
        bool inLong = false; // Variable to track if we are in a long position
        double entryPrice = 0; // Variable to track the entry price
        
        // Scan candles 3 by 3
        for(int i = 0; i < nbcandles-2; i++) // nbcandles-2 because we are checking 3 candles at a time
        {
            MqlRates candle1 = rates[i];
            MqlRates candle2 = rates[i + 1];
            MqlRates candle3 = rates[i + 2];
            
            // Check the first pattern condition (Green Criteria)
            if(candle1.high > candle2.high && candle3.high > candle2.high && candle3.high < candle1.high)
            {
                // Pattern detected
                Print("Green Criteria detected on ", symbol, " at times: ", 
                      TimeToString(candle1.time), ", ", 
                      TimeToString(candle2.time), ", ", 
                      TimeToString(candle3.time));
                
                // Enter long if not already in a long position
                if(!inLong)
                {
                    inLong = true;
                    entryPrice = candle3.close; // Enter long at the close of the third candle
                    Print("Entered long at ", entryPrice, " on ", symbol);
                }
            }
            
            // Check the second pattern condition (Red Criteria)
            if(candle1.low > candle2.low && candle3.low > candle2.low && candle3.low < candle1.low)
            {
                // Pattern detected
                Print("Red Criteria detected on ", symbol, " at times: ", 
                      TimeToString(candle1.time), ", ", 
                      TimeToString(candle2.time), ", ", 
                      TimeToString(candle3.time));
                
                // Close long if in a long position
                if(inLong)
                {
                    inLong = false;
                    double exitPrice = candle3.close; // Exit long at the close of the third candle
                    double profit = exitPrice - entryPrice;
                    assetProfit += profit;
                    totalProfit += profit;
                    Print("Exited long at ", exitPrice, " on ", symbol, ". Profit: ", profit);
                }
            }
        }
        
        // Store the profit for the current asset
        profits[s] = assetProfit;
    }
    
    // Sort the profits array and the symbols array accordingly
    for(int i = 0; i < symbolCount - 1; i++)
    {
        for(int j = i + 1; j < symbolCount; j++)
        {
            if(profits[j] > profits[i])
            {
                // Swap profits
                double tempProfit = profits[i];
                profits[i] = profits[j];
                profits[j] = tempProfit;
                
                // Swap symbols
                string tempSymbol = symbols[i];
                symbols[i] = symbols[j];
                symbols[j] = tempSymbol;
            }
        }
    }
    
    // Get the range of dates used for the analysis
    datetime startDate = 0;
    datetime endDate = 0;
    for(int s = 0; s < symbolCount; s++)
    {
        string symbol = symbols[s];
        MqlRates rates[];
        int copied = CopyRates(symbol, PERIOD_CURRENT, 0, nbcandles, rates);
        if(copied == nbcandles)
        {
            if(startDate == 0 || rates[0].time < startDate)
                startDate = rates[0].time;
            if(endDate == 0 || rates[nbcandles-1].time > endDate)
                endDate = rates[nbcandles-1].time;
        }
    }
    
    // Print total profit, all assets ordered by profitability, and the date range
    Print("Total Profit: ", totalProfit);
    Print("Assets ordered by profitability:");
    for(int i = 0; i < symbolCount; i++)
    {
        Print(i + 1, ". ", symbols[i], " with profit: ", profits[i]);
    }
    Print("Date range used for analysis: ", TimeToString(startDate), " to ", TimeToString(endDate));
}
//+------------------------------------------------------------------+
