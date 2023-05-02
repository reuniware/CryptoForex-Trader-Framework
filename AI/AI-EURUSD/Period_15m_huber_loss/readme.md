Mes tests montrent que le nombre d'Epochs optimal est de 4 car on arrive à obtenir un mape d'environs 0.07% d'erreur.

Avec un nombre d'Epochs de 5 on obtient en moyenne un mape d'environs 0.15% d'erreur.

Selon moi, il faut jouer sur le modèle pour tenter de réduire encore le mape. C'est la seule piste que j'ai, mais déjà on a de très bons résultats.

Une autre piste serait aussi d'obtenir plus de données. Car quand on demande à l'API Yahoo les données 15 minutes pour la plage du 04/03/2023 au 02/05/2023 et bien les dernières données obtenues concernent le 01/05/2023 à 23h45. De ce fait on a un entraînement du modèle sans les données du jour et donc probablement une prédiction un peu moins précise car il manque les données du jour (en l'occurrence le 02/05/2023 dans le cas présent).


      Date range used : 2023-03-04 2023-05-02
      [*********************100%***********************]  1 of 1 completed
                      Datetime      Open      High       Low     Close  Adj Close  Volume
      0    2023-03-06 00:00:00  1.062812  1.063717  1.062812  1.063717   1.063717       0
      1    2023-03-06 00:15:00  1.063604  1.063830  1.063377  1.063830   1.063830       0
      2    2023-03-06 00:30:00  1.063830  1.063943  1.063604  1.063717   1.063717       0
      3    2023-03-06 00:45:00  1.063717  1.063830  1.063038  1.063038   1.063038       0
      4    2023-03-06 01:00:00  1.063151  1.063264  1.062925  1.062925   1.062925       0
      ...                  ...       ...       ...       ...       ...        ...     ...
      3876 2023-05-01 22:45:00  1.097815  1.097936  1.097695  1.097936   1.097936       0
      3877 2023-05-01 23:00:00  1.097815  1.097936  1.097815  1.097815   1.097815       0
      3878 2023-05-01 23:15:00  1.097815  1.097815  1.097695  1.097815   1.097815       0
      3879 2023-05-01 23:30:00  1.097815  1.097815  1.097815  1.097815   1.097815       0
      3880 2023-05-01 23:45:00  1.097815  1.097815  1.097695  1.097695   1.097695       0
