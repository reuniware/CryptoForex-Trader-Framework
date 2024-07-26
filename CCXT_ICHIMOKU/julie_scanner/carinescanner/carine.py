import pandas as pd
import glob
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error
import joblib

def load_data_from_files(directory, pattern):
    # Use glob to find files matching the pattern
    file_paths = glob.glob(f"{directory}/{pattern}")
    print(f"Found {len(file_paths)} files matching the pattern {pattern}")

    # Load and concatenate data from all matching CSV files
    data_frames = [pd.read_csv(file) for file in file_paths]
    df = pd.concat(data_frames, ignore_index=True)
    
    return df

def preprocess_data(df):
    # Ensure the 'Date' column is datetime type
    df['Date'] = pd.to_datetime(df['Timestamp'])
    
    # Feature Engineering
    df['Target'] = df['Close'].shift(-1)  # Predict next day's closing price
    df.dropna(inplace=True)  # Drop rows with missing target values

    # Feature and Target Preparation
    X = df[['Open', 'High', 'Low', 'Volume']]  # Include relevant features
    y = df['Target']
    
    return X, y

def train_and_save_model(X, y, model_filename):
    # Split the data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Initialize and train the Random Forest model
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    # Make predictions and evaluate the model
    y_pred = model.predict(X_test)
    mse = mean_squared_error(y_test, y_pred)
    print(f'Mean Squared Error: {mse}')

    # Save the model
    joblib.dump(model, model_filename)
    print(f"Model saved to {model_filename}")

def main():
    directory = '../downloaded_history'
    pattern = 'BTC_USDT_*.csv'  # Pattern to match filenames
    model_filename = 'bitcoin_price_model.pkl'

    # Load data from CSV files
    df = load_data_from_files(directory, pattern)

    if df.empty:
        print("No data found for training.")
        return

    # Preprocess the data
    X, y = preprocess_data(df)

    if X.empty or y.empty:
        print("No valid data available for training.")
        return

    # Train and save the model
    train_and_save_model(X, y, model_filename)

if __name__ == "__main__":
    main()
