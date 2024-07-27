//+------------------------------------------------------------------+
//| Paramètres d'entrée                                              |
//+------------------------------------------------------------------+
input int BarCount = 50; // Nombre de barres initial
input ENUM_TIMEFRAMES Timeframe = PERIOD_M15; // Période
//+------------------------------------------------------------------+
//| Variables globales                                               |
//+------------------------------------------------------------------+
int barCount;
ENUM_TIMEFRAMES timeframe;
int maxBarCountUsed = 0; // Nouvelle variable pour suivre le nombre maximum de barres utilisées

//--- identifiants des touches
#define KEY_NUMPAD_5       12
#define KEY_LEFT           37
#define KEY_UP             38
#define KEY_RIGHT          39
#define KEY_DOWN           40
#define KEY_NUMLOCK_DOWN   98
#define KEY_NUMLOCK_LEFT  100
#define KEY_NUMLOCK_5     101
#define KEY_NUMLOCK_RIGHT 102
#define KEY_NUMLOCK_UP    104
//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
  {
   // Initialiser les variables globales avec les paramètres d'entrée
   barCount = BarCount;
   timeframe = Timeframe;
   maxBarCountUsed = barCount;
   
   // Tracer les lignes horizontales pour les points hauts et bas
   DrawHorizontalLines();
   
   // Indiquer que tout est bien initialisé
   return(INIT_SUCCEEDED);
  }
//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
  {
   // Supprimer les lignes horizontales et le bouton lors de la déinitialisation
   DeleteHorizontalLines();
  }
//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
  {
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
   if(bars < barCount + 2) // Ajouté +2 pour vérifier correctement les points hauts/bas
     {
      Print("Pas assez de barres pour les ", barCount, " dernières barres.");
      return;
     }

   // Mettre à jour la valeur maximale de barCount utilisée
   if (barCount > maxBarCountUsed)
      maxBarCountUsed = barCount;

   // Parcourir les barres sélectionnées
   for(int i = 1; i <= barCount; i++)
     {
      double high = iHigh(_Symbol, timeframe, i);
      double highPrev = iHigh(_Symbol, timeframe, i + 1); // Inverser les index pour être correct
      double highNext = iHigh(_Symbol, timeframe, i - 1);

      double low = iLow(_Symbol, timeframe, i);
      double lowPrev = iLow(_Symbol, timeframe, i + 1); // Inverser les index pour être correct
      double lowNext = iLow(_Symbol, timeframe, i - 1);

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
   // Supprimer toutes les lignes jusqu'à la valeur maximale de barCount utilisée
   for(int i = 1; i <= maxBarCountUsed; i++)
     {
      string highLineName = "HighLine_" + IntegerToString(i);
      string lowLineName = "LowLine_" + IntegerToString(i);
      if(ObjectFind(0, highLineName) >= 0)
         ObjectDelete(0, highLineName);
      if(ObjectFind(0, lowLineName) >= 0)
         ObjectDelete(0, lowLineName);
     }
  }
//+------------------------------------------------------------------+
//| Fonction ChartEvent                                              |
//+------------------------------------------------------------------+
void OnChartEvent(const int id,
                  const long &lparam,
                  const double &dparam,
                  const string &sparam)
  {
//--- appui sur une touche
   if(id == CHARTEVENT_KEYDOWN)
     {
      switch((int)lparam)
        {
         case KEY_NUMLOCK_LEFT:  Print("Appui sur KEY_NUMLOCK_LEFT");   break;
         case KEY_LEFT:          Print("Appui sur KEY_LEFT");           break;
         case KEY_NUMLOCK_UP:    Print("Appui sur KEY_NUMLOCK_UP");     break;
         case KEY_UP:
               barCount++;
               Print("barCount=", barCount);
               DrawHorizontalLines();
            break;
         case KEY_NUMLOCK_RIGHT: Print("Appui sur KEY_NUMLOCK_RIGHT");  break;
         case KEY_RIGHT:         Print("Appui sur KEY_RIGHT");          break;
         case KEY_NUMLOCK_DOWN:  Print("Appui sur KEY_NUMLOCK_DOWN");   break;
         case KEY_DOWN:
               barCount--;
               if (barCount < 0) barCount = 0;
               Print("barCount=", barCount);
               DrawHorizontalLines();
            break;
         case KEY_NUMPAD_5:      Print("Appui sur KEY_NUMPAD_5");       break;
         case KEY_NUMLOCK_5:     Print("Appui sur KEY_NUMLOCK_5");      break;
         default:                Print("Appui sur une touche non listée");
        }
     }
  }
