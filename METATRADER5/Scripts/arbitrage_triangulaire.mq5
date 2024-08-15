//+------------------------------------------------------------------+
//|                                             Triangular Arbitrage |
//|               Copyright 2024 Investdatasystems/Reuniware/DVASoft |
//|                              https://ichimokuexpert.blogspot.com |
//+------------------------------------------------------------------+
#property copyright "MetaQuotes Software Corp."
#property link      "https://www.mql5.com"
#property version   "1.00"

//--- input parameters
input string Symbol1 = "EURUSD";
input string Symbol2 = "USDJPY";
input string Symbol3 = "EURJPY";
input double Investment = 1000.0;

//--- global variables
double rate12, rate23, rate31;

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
  {
//---
   return(INIT_SUCCEEDED);
  }

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
  {
//---
  }

//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
  {
//--- get rates
   rate12 = SymbolInfoDouble(Symbol1, SYMBOL_BID);
   rate23 = SymbolInfoDouble(Symbol2, SYMBOL_BID);
   rate31 = SymbolInfoDouble(Symbol3, SYMBOL_ASK); // Use ASK price for the final conversion

//--- check for arbitrage opportunity
   if(rate12 * rate23 * rate31 > 1.0)
      {
//--- arbitrage opportunity found, calculate potential profit
         double amountInEUR = Investment / rate12;
         double amountInJPY = amountInEUR * rate31;
         double finalAmountInUSD = amountInJPY / rate23;
         double profit = finalAmountInUSD - Investment;

         Print("Arbitrage opportunity found!");
         Print("Initial Investment: ", Investment, " USD");
         Print("Final Amount: ", finalAmountInUSD, " USD");
         Print("Profit: ", profit, " USD");
      }
  }
