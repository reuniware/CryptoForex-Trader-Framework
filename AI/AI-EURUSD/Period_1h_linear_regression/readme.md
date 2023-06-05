
For this one I used some tips from :

https://www.mlq.ai/price-prediction-with-linear-regression/

**modeles_a_trier_eurgbp.zip** has been generated with **ai-predict-eurgbp-linear-regression-4.py** with **create_model** set to True.

To use one of the models that are in **modeles_a_trier_eurgbp.zip** :

- Set **create_model** to False in **ai-predict-eurgbp-linear-regression-4.py** file
- Specify a model folder in **ai-predict-eurgbp-linear-regression-4.py** file, in the constant **whole_model_folder_to_load**. Example : './modeles_a_trier/20230515065142-whole_model')
- Run the **ai-predict-eurgbp-linear-regression-4.py** file

Tips :
- When you create a model by setting **create_model** to True, think of changing the epochs constant in the following line of code : **"model.fit(X_train, y_train, epochs=2000, batch_size=None, validation_split=0.1, shuffle=False)"**. Using a value of 2000 seems huge but this value was coded for testing purposes. Try with 20 then increase it and check if the results are ok for you.
- You can change the asset to download by changing it in the following line : **"ohlcv = yf.download('EURGBP=X', start=strStartDate, end=strEndDate, interval='1h')"**. Example : Change **'EURGBP=X'** by **'EURUSD=X'** or any other asset.
- Use GPU when **create_model** = True (to create a model).
- You can use CPU (or GPU) when using an existing model (when **create_model** is set to False) to make a prediction.

# Version 9 #
AI/AI-EURUSD/Period_1h_linear_regression/ai-predict-eurusd-linear-regression-9-send-to-server.py
AI/AI-EURUSD/Period_1h_linear_regression/ai-predict-eurusd-linear-regression-9-send-to-server.php

https://eurodollarbot.000webhostapp.com/index.php
