//+------------------------------------------------------------------+
//|                                                      OrderBlockEA |
//|                        Copyright 2023, MetaQuotes Software Corp. |
//|                                       http://www.metaquotes.net/ |
//+------------------------------------------------------------------+
#include <Trade\Trade.mqh>

input int OrderBlockLookback = 10; // Nombre de barres à vérifier pour les Order Blocks
input color OrderBlockColor = clrRed; // Couleur des lignes des Order Blocks

CTrade trade;

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
  {
   // Initialisation des paramètres
   EventSetTimer(1); // Définir un timer pour vérifier les Order Blocks
   return(INIT_SUCCEEDED);
  }

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
  {
   ObjectsDeleteAll(0, 0, OBJ_HLINE); // Supprimer toutes les lignes horizontales
   EventKillTimer();
  }

//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
  {
   // Vérifier les Order Blocks à chaque tick
   CheckOrderBlocks();
  }

//+------------------------------------------------------------------+
//| Timer function                                                   |
//+------------------------------------------------------------------+
void OnTimer()
  {
   // Vérifier les Order Blocks à chaque seconde
   CheckOrderBlocks();
  }

//+------------------------------------------------------------------+
//| Vérifier les Order Blocks                                        |
//+------------------------------------------------------------------+
void CheckOrderBlocks()
  {
   double high[], low[];
   ArraySetAsSeries(high, true);
   ArraySetAsSeries(low, true);
   CopyHigh(_Symbol, PERIOD_M1, 0, OrderBlockLookback, high);
   CopyLow(_Symbol, PERIOD_M1, 0, OrderBlockLookback, low);

   for(int i = 1; i < OrderBlockLookback; i++)
     {
      if(high[i] > high[i-1] && high[i] > high[i+1])
        {
         // Détecter un Order Block haut
         DrawOrderBlockLine(i, high[i], true);
        }
      if(low[i] < low[i-1] && low[i] < low[i+1])
        {
         // Détecter un Order Block bas
         DrawOrderBlockLine(i, low[i], false);
        }
     }
  }

//+------------------------------------------------------------------+
//| Tracer une ligne pour un Order Block                             |
//+------------------------------------------------------------------+
void DrawOrderBlockLine(int barIndex, double price, bool isHigh)
  {
   string objName = (isHigh ? "OrderBlockHigh_" : "OrderBlockLow_") + IntegerToString(barIndex);
   if(ObjectFind(0, objName) < 0)
     {
      ObjectCreate(0, objName, OBJ_HLINE, 0, TimeCurrent(), price);
      ObjectSetInteger(0, objName, OBJPROP_COLOR, OrderBlockColor);
      ObjectSetInteger(0, objName, OBJPROP_WIDTH, 2);
      ObjectSetInteger(0, objName, OBJPROP_STYLE, STYLE_SOLID);
     }
  }
//+------------------------------------------------------------------+
