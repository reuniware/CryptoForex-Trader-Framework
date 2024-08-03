//+------------------------------------------------------------------+
//|                                                   GetHistory.mq5 |
//|                        Copyright 2024, Reuniware/DVASoft         |
//|                     https://www.ichimoku-expert.blogspot.com     |
//+------------------------------------------------------------------+
#include <Trade\Trade.mqh>

input int BarsToGet = 100; // Nombre de barres à récupérer
input ENUM_TIMEFRAMES Timeframe = PERIOD_M1; // Timeframe à utiliser

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
  {
   // Compte le nombre de symboles dans la fenêtre de Market Watch
   int symbols_total = SymbolsTotal(true);

   // Boucle sur tous les symboles
   for(int i=0; i < symbols_total; i++)
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

   // Initialise un tableau pour stocker les temps
   datetime time_array[];
   
   // Copie les temps des barres dans le tableau
   int copied = CopyTime(symbol, timeframe, 0, bars, time_array);

   // Vérifie s'il y a une erreur dans la copie
   if(copied <= 0)
     {
      Print("Erreur : impossible de copier les données pour ", symbol, ". Erreur n°", GetLastError());
      return;
     }

   // Affiche le nom de l'actif, la date et l'heure de début et de fin de la plage récupérée
   Print("Symbole: ", symbol, " - Début: ", TimeToString(time_array[copied-1]), " - Fin: ", TimeToString(time_array[0]));
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
