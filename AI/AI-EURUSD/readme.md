
# Chantier de recherche expérimentale sur la prédiction du cours de l'EUR/USD en utilisant le deep learning.
# Forex market forecasting using machine learning

On utilise ai-predict-eurusd-2-loop.py pour générer des fichiers de poids pour lesquels quand on lance une prédiction il y a un mape inférieur ou égal à 1.005%

Tous les répertoires qui sont nommés "models" auraient dû être nommés "models weights" car ils ne contiennent pas les modèles en eux-mêmes mais les poids qui sont appliqués aux modèles.

Les modèles sont dans les fichiers .py, comme par exemple :

    model = Sequential()
    model.add(LSTM(units=150, return_sequences=True, input_shape=(X_train.shape[1], 1)))
    model.add(LSTM(units=300))
    model.add(Dense(1))
    # Compilation du modèle
    model.compile(optimizer='adam', loss='huber_loss')

Bien sûr, pour rappel, quand on charge un fichier de poids, ce dernier ne peut être appliqué qu'au modèle qui a été utilisé pour générer ce fichier de poids.

C'est pour cela qu'idéalement je devrai sauvegarder chaque modèle qui peut être utilisé par un fichier de poids... Mais je n'ai pas pris cette habitude jusqu'à maintenant. A l'avenir je tâcherai de penser à ce point.
