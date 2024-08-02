//+------------------------------------------------------------------+
//|                                                 Scan1Percent.mq5 |
//|                        Copyright 2024 Reuniware / DVASoft        |
//|                                                                  |
//+------------------------------------------------------------------+
#property strict

input double PercentThreshold = 1.0; // Seuil de pourcentage pour détecter un mouvement

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
  {
   //--- initialisation
   EventSetTimer(10); // Définir un timer pour scanner toutes les 10 secondes
   return(INIT_SUCCEEDED);
  }
//+------------------------------------------------------------------+
//| Expert deinitialization function                                |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
  {
   //--- deinitialisation
   EventKillTimer(); // Arrêter le timer
  }
//+------------------------------------------------------------------+
//| Expert timer function                                           |
//+------------------------------------------------------------------+
void OnTimer()
  {
   //--- obtenir tous les symboles disponibles dans l'Observateur de Marché
   int total = SymbolsTotal(true); // true pour obtenir uniquement les symboles visibles
   for(int i = 0; i < total; i++)
     {
      string symbol = SymbolName(i, true);
      if(SymbolSelect(symbol, true))
        {
         double prevClose = iClose(symbol, PERIOD_D1, 1);
         double currentPrice = SymbolInfoDouble(symbol, SYMBOL_BID);

         if(prevClose > 0 && currentPrice > 0)
           {
            double changePercent = (currentPrice - prevClose) / prevClose * 100;
            if(MathAbs(changePercent) >= PercentThreshold)
              {
               Print("Mouvement de ", changePercent, "% détecté sur ", symbol);
              }
           }
        }
     }
  }
//+------------------------------------------------------------------+
