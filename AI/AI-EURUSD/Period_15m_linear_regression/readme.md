
This version saves the whole model with the "model.save" function that creates a directory and files in it. In this case there is no need to save the model weights (variables) in a separate .h5 file as it was done before this version.

The directory name can then be loaded as a whole model for predictions.

Do you need a deep learning expert in finance ? Feel free to contact me at : InvestDataSystems@Yahoo.com

When using the following version (and you should) : ai-predict-eurusd-15m-LR-create-or-use-existing.py :

You just need to set the create_model constant to True to generate the coded model with random variables and save the model + the generated variables to the whole model folder.

Then when you want to use a pre-generated whole model folder for a prediction, set the create_model contant to False and specify the folder name to load in the whole_model_folder_to_load constant.

