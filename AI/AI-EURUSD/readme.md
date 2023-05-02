
# Chantier de recherche expérimentale sur la prédiction du cours de l'EUR/USD en utilisant le deep learning.

On utilise ai-predict-eurusd-2-loop.py pour générer des fichiers de poids pour lesquels quand on lance une prédiction il y a un mape inférieur ou égal à 1.005%

Tous les répertoires qui sont nommés "models" auraient dû être nommés "models weights" car ils ne contiennent pas les modèles en eux-mêmes mais les poids qui sont appliqués aux modèles.

Les modèles sont dans les fichiers .py, comme par exemple :

    model = Sequential()
    model.add(LSTM(units=150, return_sequences=True, input_shape=(X_train.shape[1], 1)))
    model.add(LSTM(units=300))
    model.add(Dense(1))
    # Compilation du modèle
    model.compile(optimizer='adam', loss='huber_loss')

