
Je ne pense pas qu'il soit logique d'utiliser binary_crossentropy comme fonction de perte mais j'ai fait quelques essais qui ont été concluants pour 2 modèles. C'est peut être un coup de chance. Voir les 2 modèles dans le répertoire models.

model.compile(optimizer='adam', loss='binary_crossentropy')

Je laisse en l'état en attendant d'aller plus loin sur cette version.
