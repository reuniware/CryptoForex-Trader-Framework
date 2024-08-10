//+------------------------------------------------------------------+
//|                                                   OrderBlockEA3  |
//|                        Copyright 2024, Reuniware/DVASoft         |
//|                            https://ichimoku-expert.blogspot.com/ |
//+------------------------------------------------------------------+
#include <Trade\Trade.mqh>

input int OrderBlockLookback = 10; // Nombre de barres à vérifier pour les Order Blocks
input color OrderBlockColor = clrGray; // Couleur des lignes des Order Blocks

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
   datetime time[];
   ArraySetAsSeries(high, true);
   ArraySetAsSeries(low, true);
   ArraySetAsSeries(time, true);
   CopyHigh(_Symbol, _Period, 0, OrderBlockLookback, high);
   CopyLow(_Symbol, _Period, 0, OrderBlockLookback, low);
   CopyTime(_Symbol, _Period, 0, OrderBlockLookback, time);

   for(int i = 1; i < OrderBlockLookback - 1; i++)
     {
      if(high[i] > high[i-1] && high[i] > high[i+1])
        {
         // Détecter un Order Block haut
         DrawOrderBlockLine(i, high[i], true, time[i]);
        }
      if(low[i] < low[i-1] && low[i] < low[i+1])
        {
         // Détecter un Order Block bas
         DrawOrderBlockLine(i, low[i], false, time[i]);
        }
     }
  }

//+------------------------------------------------------------------+
//| Tracer une ligne pour un Order Block                             |
//+------------------------------------------------------------------+
//+------------------------------------------------------------------+
//| Tracer une ligne pour un Order Block                             |
//+------------------------------------------------------------------+
void DrawOrderBlockLine(int barIndex, double price, bool isHigh, datetime barTime)
  {
   string objName = (isHigh ? "OrderBlockHigh_" : "OrderBlockLow_") + IntegerToString(barIndex);
   if(ObjectFind(0, objName) < 0)
     {
      ObjectCreate(0, objName, OBJ_HLINE, 0, TimeCurrent(), price);
      ObjectSetInteger(0, objName, OBJPROP_COLOR, isHigh ? clrGreen : clrRed); // Set color based on isHigh
      ObjectSetInteger(0, objName, OBJPROP_WIDTH, 2);
      ObjectSetInteger(0, objName, OBJPROP_STYLE, STYLE_SOLID);
      ObjectSetInteger(0, objName, OBJPROP_BACK, true); // Draw line behind candles

      // Afficher la date et l'heure de la bougie où l'Order Block est détecté, ainsi que la valeur de la ligne
      string message = (isHigh ? "High Order Block" : "Low Order Block") + 
                       " detected at " + TimeToString(barTime, TIME_DATE|TIME_MINUTES) + 
                       ", Price: " + DoubleToString(price, _Digits);
      Print(message);
     }
  }
//+------------------------------------------------------------------+
