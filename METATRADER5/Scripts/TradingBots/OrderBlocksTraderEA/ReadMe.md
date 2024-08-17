![image](https://github.com/user-attachments/assets/fad73f87-8a50-40ab-8db5-eec30b09762a)

![image](https://github.com/user-attachments/assets/fb1dfb31-bea4-492d-91fe-35d74dc4f438)

The provided code is a simple trading bot written in MQL5, which is a programming language used for creating automated trading systems for the MetaTrader 5 platform. The bot is designed to detect a specific candle pattern and execute a long trade (buy order) when the pattern is identified. Below is a detailed explanation of the code:

### Header and Author Information
```cpp
//+-------------------------------------------------------------------------------------------+
//| Trading bot by InvestDataSystems@Yahoo.com / SolanaExpert@ProtonMail.com / DVASoft 2024   |
//+-------------------------------------------------------------------------------------------+
```
This section contains the author's contact information and the year of creation.

### Include Trade Library
```cpp
#include <Trade\Trade.mqh>
```
This line includes the `Trade.mqh` library, which provides classes and functions for executing trades.

### Global Variable
```cpp
CTrade trade;
```
This initializes an instance of the `CTrade` class, which will be used for executing trades.

### OnInit Function
```cpp
int OnInit()
  {
   // Initialization successful
   return(INIT_SUCCEEDED);
  }
```
The `OnInit` function is called when the expert advisor (EA) is initialized. It returns `INIT_SUCCEEDED` to indicate that the initialization was successful.

### OnDeinit Function
```cpp
void OnDeinit(const int reason)
  {
   // Do nothing
  }
```
The `OnDeinit` function is called when the EA is deinitialized. Currently, it does nothing.

### OnTick Function
```cpp
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
```
The `OnTick` function is called on every tick (new price update). It checks if the current candle has changed by comparing the timestamp of the last checked candle with the timestamp of the current candle. If a new candle has formed, it updates the `lastCheckedCandleTime` and calls the `DetectCandlePattern` function.

### DetectCandlePattern Function
```cpp
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
```
The `DetectCandlePattern` function checks for a specific candle pattern on the last two completed candles. The pattern criteria are:
1. The first candle (n-2) is red (open > close).
2. The percentage change of the first candle is at least 0.01%.
3. The second candle (n-1) is green (open < close).
4. The percentage change of the second candle is at least 0.01%.
5. The open of the second candle is greater than the close of the first candle.
6. The close of the second candle is greater than the open of the first candle.

If the pattern is detected, the bot opens a long trade (buy order) with a specified volume, stop loss (currently set to 0), and take profit. The trade details are printed to the log, and the result of the trade execution is checked and logged.

### Summary
This trading bot is designed to detect a specific candle pattern and execute a long trade when the pattern is identified. It uses basic technical analysis and predefined thresholds to make trading decisions. The bot is intended to be run on the MetaTrader 5 platform and uses the MQL5 programming language.

![image](https://github.com/user-attachments/assets/0a98ed12-c031-44c6-ad94-2b09f2dd2e95)

