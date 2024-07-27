//+------------------------------------------------------------------+
//| Script program start function                                    |
//+------------------------------------------------------------------+
void OnStart()
  {
   // Obtenir le nombre de barres sur l'unité de temps journalière
   int barsD1 = Bars(_Symbol, PERIOD_D1);

   // Vérifier que nous avons suffisamment de barres pour les 9 derniers jours
   if(barsD1 < 9)
     {
      Print("Pas assez de barres pour les 9 derniers jours.");
      return;
     }

   // Parcourir les 9 derniers jours
   for(int i = 1; i <= 9; i++)
     {
      double highD1 = iHigh(_Symbol, PERIOD_D1, i);
      double highPrevD1 = iHigh(_Symbol, PERIOD_D1, i - 1);
      double highNextD1 = iHigh(_Symbol, PERIOD_D1, i + 1);

      double lowD1 = iLow(_Symbol, PERIOD_D1, i);
      double lowPrevD1 = iLow(_Symbol, PERIOD_D1, i - 1);
      double lowNextD1 = iLow(_Symbol, PERIOD_D1, i + 1);

      if(highD1 > highPrevD1 && highD1 > highNextD1)
        {
         // Point haut sur D1
         string objectNameLine = "HighLineD1_" + IntegerToString(i);
         ObjectCreate(0, objectNameLine, OBJ_HLINE, 0, 0, highD1);
         ObjectSetInteger(0, objectNameLine, OBJPROP_COLOR, clrRed);
         ObjectSetInteger(0, objectNameLine, OBJPROP_WIDTH, 1);
         ObjectSetInteger(0, objectNameLine, OBJPROP_STYLE, STYLE_DASH);
        }

      if(lowD1 < lowPrevD1 && lowD1 < lowNextD1)
        {
         // Point bas sur D1
         string objectNameLine = "LowLineD1_" + IntegerToString(i);
         ObjectCreate(0, objectNameLine, OBJ_HLINE, 0, 0, lowD1);
         ObjectSetInteger(0, objectNameLine, OBJPROP_COLOR, clrGreen);
         ObjectSetInteger(0, objectNameLine, OBJPROP_WIDTH, 1);
         ObjectSetInteger(0, objectNameLine, OBJPROP_STYLE, STYLE_DASH);
        }
     }
  }
//+------------------------------------------------------------------+
