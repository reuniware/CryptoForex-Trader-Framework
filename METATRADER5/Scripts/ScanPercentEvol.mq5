//+------------------------------------------------------------------+
//|                                                 Scan1Percent.mq5 |
//|                        Copyright 2024 Reuniware / DVASoft        |
//|                                                                  |
//+------------------------------------------------------------------+
#property strict

input double PercentThreshold = 0.19; // Seuil de pourcentage pour détecter un mouvement

// Déclaration d'un tableau global pour stocker les prix précédents
double previousPrices[];

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
  {
   //--- initialisation
   int total = SymbolsTotal(true); // Nombre de symboles visibles
   ArrayResize(previousPrices, total); // Redimensionner le tableau pour les symboles visibles
   for(int i = 0; i < total; i++)
     {
      string symbol = SymbolName(i, true);
      Print("processing " + symbol);
      previousPrices[i] = SymbolInfoDouble(symbol, SYMBOL_BID); // Stocker le prix actuel comme prix précédent initial
     }
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
         double currentPrice = SymbolInfoDouble(symbol, SYMBOL_BID);
         double prevPrice = previousPrices[i];

         if(prevPrice > 0 && currentPrice > 0)
           {
            double changePercent = (currentPrice - prevPrice) / prevPrice * 100;
            if(MathAbs(changePercent) >= PercentThreshold)
              {
               Print("Mouvement de ", changePercent, "% détecté sur ", symbol);
              }
            // Mettre à jour le prix précédent avec le prix actuel pour le prochain passage
            previousPrices[i] = currentPrice;
           }
        }
     }
  }
//+------------------------------------------------------------------+
