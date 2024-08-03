//+------------------------------------------------------------------+
//|                                                 Scan2Candles.mq5 |
//|                         Copyright 2024, Reuniware/DVASoft        |
//|                     https://www.ichimoku-expert.blogspot.com     |
//+------------------------------------------------------------------+
#include <Trade\Trade.mqh>

input int BarsToGet = 100; // Nombre de barres à récupérer
input ENUM_TIMEFRAMES Timeframe = PERIOD_M15; // Timeframe à utiliser

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
  {
   // Compte le nombre de symboles dans la fenêtre de Market Watch
   int symbols_total = SymbolsTotal(true);

   // Boucle sur tous les symboles
   for(int i = 0; i < symbols_total; i++)
     {
      // Récupère le nom du symbole
      string symbol_name = SymbolName(i, true);
      
      // Récupère les barres
      GetSymbolHistory(symbol_name, BarsToGet, Timeframe);
     }

   // Indicateur de succès d'initialisation
   return(INIT_SUCCEEDED);
  }
//+------------------------------------------------------------------+
//| Récupère l'historique pour un symbole donné                      |
//+------------------------------------------------------------------+
void GetSymbolHistory(string symbol, int bars, ENUM_TIMEFRAMES timeframe)
  {
   //Print("Récupération des données pour : ", symbol, " sur la timeframe : ", EnumToString(timeframe));

   // Vérifie si les données sont disponibles pour le symbole
   if(!SymbolSelect(symbol, true))
     {
      Print("Erreur : impossible de sélectionner le symbole ", symbol);
      return;
     }

   // Initialise des tableaux pour stocker les temps, open, high, low et close
   datetime time_array[];
   double open_array[], high_array[], low_array[], close_array[];

   // Copie les données des barres dans les tableaux
   int copied_time = CopyTime(symbol, timeframe, 0, bars, time_array);
   int copied_open = CopyOpen(symbol, timeframe, 0, bars, open_array);
   int copied_high = CopyHigh(symbol, timeframe, 0, bars, high_array);
   int copied_low = CopyLow(symbol, timeframe, 0, bars, low_array);
   int copied_close = CopyClose(symbol, timeframe, 0, bars, close_array);

   // Vérifie s'il y a une erreur dans la copie
   if(copied_time <= 0 || copied_open <= 0 || copied_high <= 0 || copied_low <= 0 || copied_close <= 0)
     {
      Print("Erreur : impossible de copier les données pour ", symbol, ". Erreur n°", GetLastError());
      return;
     }

   // S'assurer que nous avons suffisamment de données pour le scan
   int copied = MathMin(copied_time, MathMin(MathMin(copied_open, copied_high), MathMin(copied_low, copied_close)));
   if(copied < 2)
     {
      Print("Erreur : pas assez de données copiées pour ", symbol);
      return;
     }

   // Scan chaque bougie selon les critères spécifiés de la plus ancienne à la plus récente
   for(int i = 1; i < copied - 1; i++)
     {
      //Print(time_array[i]);
     
      double open_current = open_array[i];
      double close_current = close_array[i];
      double high_current = high_array[i];
      double low_current = low_array[i];

      // Si la bougie en cours de scan est verte (haussière)
      if(open_current < close_current)
        {
         double open_next = open_array[i + 1];
         double close_next = close_array[i + 1];

         // Si la prochaine bougie est rouge (baissière)
         // et si l'ouverture de la prochaine bougie est sous la fermeture de la bougie précédente
         // et si la fermeture de la prochaine bougie est sous l'ouverture de la bougie précédente
         if(open_next > close_next && open_next < close_current && close_next < open_current)
           {
            Print(symbol + " : Setup détecté sur la bougie du ", TimeToString(time_array[i + 1]));
           }
        }
     }
  }
//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
  {
   // Actions de désinitialisation si nécessaires
  }
//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
  {
   // Actions à chaque tick si nécessaires
  }
//+------------------------------------------------------------------+
