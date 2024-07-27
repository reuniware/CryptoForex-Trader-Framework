//+------------------------------------------------------------------+
//| Paramètres d'entrée                                              |
//+------------------------------------------------------------------+
input int BarCount = 30; // Nombre de barres
input ENUM_TIMEFRAMES Timeframe = PERIOD_M5; // Période
input string SoundFile = "alert.wav"; // Fichier sonore à jouer
//+------------------------------------------------------------------+
//| Variables globales                                              |
//+------------------------------------------------------------------+
int barCount;
ENUM_TIMEFRAMES timeframe;
//+------------------------------------------------------------------+
//| Script program start function                                    |
//+------------------------------------------------------------------+
void OnStart()
  {
   // Initialiser les variables globales avec les paramètres d'entrée
   barCount = BarCount;
   timeframe = Timeframe;

   // Tracer les lignes horizontales pour les points hauts et bas
   DrawHorizontalLines();
  }
//+------------------------------------------------------------------+
//| Fonction pour tracer les lignes horizontales                     |
//+------------------------------------------------------------------+
void DrawHorizontalLines()
  {
   // Supprimer les lignes précédentes
   DeleteHorizontalLines();

   // Obtenir le nombre de barres sur la période sélectionnée
   int bars = Bars(_Symbol, timeframe);

   // Vérifier que nous avons suffisamment de barres pour le nombre de barres sélectionné
   if(bars < barCount)
     {
      Print("Pas assez de barres pour les ", barCount, " dernières barres.");
      return;
     }

   // Parcourir les barres sélectionnées
   for(int i = 1; i <= barCount; i++)
     {
      double high = iHigh(_Symbol, timeframe, i);
      double highPrev = iHigh(_Symbol, timeframe, i - 1);
      double highNext = iHigh(_Symbol, timeframe, i + 1);

      double low = iLow(_Symbol, timeframe, i);
      double lowPrev = iLow(_Symbol, timeframe, i - 1);
      double lowNext = iLow(_Symbol, timeframe, i + 1);

      if(high > highPrev && high > highNext)
        {
         // Point haut
         string objectNameLine = "HighLine_" + IntegerToString(i);
         ObjectCreate(0, objectNameLine, OBJ_HLINE, 0, 0, high);
         ObjectSetInteger(0, objectNameLine, OBJPROP_COLOR, clrRed);
         ObjectSetInteger(0, objectNameLine, OBJPROP_WIDTH, 1);
         ObjectSetInteger(0, objectNameLine, OBJPROP_STYLE, STYLE_DASH);
        }

      if(low < lowPrev && low < lowNext)
        {
         // Point bas
         string objectNameLine = "LowLine_" + IntegerToString(i);
         ObjectCreate(0, objectNameLine, OBJ_HLINE, 0, 0, low);
         ObjectSetInteger(0, objectNameLine, OBJPROP_COLOR, clrGreen);
         ObjectSetInteger(0, objectNameLine, OBJPROP_WIDTH, 1);
         ObjectSetInteger(0, objectNameLine, OBJPROP_STYLE, STYLE_DASH);
        }
     }
  }
//+------------------------------------------------------------------+
//| Fonction pour supprimer les lignes horizontales                  |
//+------------------------------------------------------------------+
void DeleteHorizontalLines()
  {
   for(int i = 1; i <= barCount; i++)
     {
      string highLineName = "HighLine_" + IntegerToString(i);
      string lowLineName = "LowLine_" + IntegerToString(i);
      ObjectDelete(0, highLineName);
      ObjectDelete(0, lowLineName);
     }
  }
//+------------------------------------------------------------------+
//| Fonction de gestion des événements                              |
//+------------------------------------------------------------------+
void OnChartEvent(const int id, const long &lparam, const double &dparam, const string &sparam)
  {
   if(id == CHARTEVENT_KEYDOWN)
     {
      if(lparam == 38) // Flèche haut
        {
         barCount++;
         DrawHorizontalLines();
         ChartRedraw();
        }
      else if(lparam == 40 && barCount > 1) // Flèche bas
        {
         barCount--;
         DrawHorizontalLines();
         ChartRedraw();
        }
     }
   else if(id == CHARTEVENT_OBJECT_CLICK)
     {
      // Vérifier si une ligne horizontale a été touchée
      for(int i = 1; i <= barCount; i++)
        {
         string highLineName = "HighLine_" + IntegerToString(i);
         string lowLineName = "LowLine_" + IntegerToString(i);
         if(sparam == highLineName || sparam == lowLineName)
           {
            PlaySound(SoundFile);
            break;
           }
        }
     }
  }
//+------------------------------------------------------------------+
