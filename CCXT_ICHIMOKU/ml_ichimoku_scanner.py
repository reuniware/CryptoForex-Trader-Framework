import sys
import os
import ccxt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import threading
import ta
import argparse
import signal
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import tweepy
from textblob import TextBlob
import pickle
import warnings

# Suppress warnings
warnings.filterwarnings('ignore')

# Configuration
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.expand_frame_repr', True)

class MLIchimokuScanner:
    def __init__(self, training_mode=False):
        self.enable_tweet = True
        self.training_mode = training_mode
        self.model = None
        self.model_file = "ichimoku_ml_model.pkl"
        self.training_data_file = "training_data.csv"
        self.min_training_samples = 100
        self.load_ml_model()
        
        # Initialize exchanges
        self.exchanges = {}
        for id in ccxt.exchanges:
            exchange = getattr(ccxt, id)
            self.exchanges[id] = exchange()
            
        # Twitter API config
        self.twitter_auth_keys = {
            "consumer_key": "replaceme",
            "consumer_secret": "replaceme",
            "access_token": "replaceme",
            "access_token_secret": "replaceme"
        }
        
        # ML features configuration
        self.feature_columns = [
            'ichimoku_a', 'ichimoku_b', 'kijun_sen', 'tenkan_sen', 'chikou_span',
            'rsi', 'macd', 'bollinger_upper', 'bollinger_lower', 'volume_ma',
            'sentiment_score', 'price_above_cloud', 'cloud_color'
        ]
        
        # Performance tracking
        self.performance_history = pd.DataFrame(columns=[
            'timestamp', 'symbol', 'prediction', 'actual', 'profit'
        ])
        
        # Training data collection
        self.training_data = pd.DataFrame(columns=self.feature_columns + ['target'])
        
    def load_ml_model(self):
        """Load trained ML model if exists"""
        if os.path.exists(self.model_file):
            with open(self.model_file, 'rb') as f:
                self.model = pickle.load(f)
            print("Loaded trained model from file")
        else:
            print("Initializing new model")
            self.model = RandomForestClassifier(n_estimators=100, random_state=42)
    
    def save_ml_model(self):
        """Save trained ML model"""
        with open(self.model_file, 'wb') as f:
            pickle.dump(self.model, f)
        print("Saved model to file")
    
    def load_training_data(self):
        """Load existing training data if available"""
        if os.path.exists(self.training_data_file):
            self.training_data = pd.read_csv(self.training_data_file)
            print(f"Loaded {len(self.training_data)} training samples")
    
    def save_training_data(self):
        """Save training data to file"""
        self.training_data.to_csv(self.training_data_file, index=False)
        print(f"Saved {len(self.training_data)} training samples")
    
    def calculate_features(self, df):
        """Calculate technical indicators and features for ML"""
        try:
            # Ichimoku Cloud
            high = df['high'].astype(float)
            low = df['low'].astype(float)
            close = df['close'].astype(float)
            volume = df['volume'].astype(float)
            
            df['ichimoku_a'] = ta.trend.ichimoku_a(high, low, window1=9, window2=26).shift(26)
            df['ichimoku_b'] = ta.trend.ichimoku_b(high, low, window2=26, window3=52).shift(26)
            df['kijun_sen'] = ta.trend.ichimoku_base_line(high, low)
            df['tenkan_sen'] = ta.trend.ichimoku_conversion_line(high, low)
            df['chikou_span'] = close.shift(-26)
            
            # Additional technical indicators
            df['rsi'] = ta.momentum.rsi(close, window=14)
            df['macd'] = ta.trend.macd_diff(close)
            bollinger = ta.volatility.BollingerBands(close)
            df['bollinger_upper'] = bollinger.bollinger_hband()
            df['bollinger_lower'] = bollinger.bollinger_lband()
            df['volume_ma'] = volume.rolling(window=20).mean()
            
            # Derived features
            df['price_above_cloud'] = (close > df[['ichimoku_a', 'ichimoku_b']].max(axis=1)).astype(int)
            df['cloud_color'] = (df['ichimoku_a'] > df['ichimoku_b']).astype(int)
            
            return df
        except Exception as e:
            print(f"Error calculating features: {str(e)}")
            return None
    
    def get_sentiment_score(self, symbol):
        """Get sentiment score from Twitter for given symbol"""
        if not self.enable_tweet:
            return 0
            
        try:
            auth = tweepy.OAuthHandler(
                self.twitter_auth_keys['consumer_key'],
                self.twitter_auth_keys['consumer_secret']
            )
            auth.set_access_token(
                self.twitter_auth_keys['access_token'],
                self.twitter_auth_keys['access_token_secret']
            )
            api = tweepy.API(auth, wait_on_rate_limit=True)
            
            # Use search_tweets instead of the deprecated search method
            tweets = api.search_tweets(q=f"${symbol.replace('USDT', '')}", count=100)
            sentiments = []
            for tweet in tweets:
                analysis = TextBlob(tweet.text)
                sentiments.append(analysis.sentiment.polarity)
            
            return np.mean(sentiments) if sentiments else 0
        except tweepy.Unauthorized as e:
            print(f"Twitter API authentication failed: {str(e)}")
            return 0
        except Exception as e:
            print(f"Error getting sentiment: {str(e)}")
            return 0
    
    def train_initial_model(self):
        """Train initial model if we have enough data"""
        self.load_training_data()
        
        if len(self.training_data) >= self.min_training_samples:
            X = self.training_data[self.feature_columns]
            y = self.training_data['target']
            
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            self.model.fit(X_train, y_train)
            
            # Evaluate model
            preds = self.model.predict(X_test)
            accuracy = accuracy_score(y_test, preds)
            print(f"Initial model trained with accuracy: {accuracy:.2f}")
            
            self.save_ml_model()
            return True
        else:
            print(f"Not enough training data ({len(self.training_data)} samples). Need at least {self.min_training_samples}.")
            return False
    
    def predict_direction(self, features):
        """Predict price direction using ML model"""
        try:
            if self.model is None or not hasattr(self.model, 'classes_'):
                return 0  # Neutral if no model
            
            # Ensure features are in correct order
            features = features[self.feature_columns].values.reshape(1, -1)
            return self.model.predict(features)[0]
        except Exception as e:
            print(f"Prediction error: {str(e)}")
            return 0
    
    def collect_training_sample(self, symbol, exchange, timeframe='1h'):
        """Collect data sample for training"""
        try:
            # Get historical data
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=100)
            if len(ohlcv) < 52:  # Need enough data for Ichimoku
                return
                
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df = self.calculate_features(df)
            if df is None:
                return
                
            # Get current and future price for target
            current_price = df['close'].iloc[-1]
            future_price = df['close'].iloc[-1]  # Placeholder - in real use, would get future price
            
            # Determine target (1 for up, -1 for down, 0 for neutral)
            price_change = future_price - current_price
            target = 1 if price_change > 0 else (-1 if price_change < 0 else 0)
            
            # Get features from last complete row
            features = df.iloc[-2].copy()
            features['sentiment_score'] = self.get_sentiment_score(symbol)
            features['target'] = target
            
            # Add to training data using concat instead of append
            new_row = pd.DataFrame([features])
            self.training_data = pd.concat([self.training_data, new_row], ignore_index=True)
            print(f"Collected training sample for {symbol}")
            
            # Periodically save data
            if len(self.training_data) % 10 == 0:
                self.save_training_data()
                
        except Exception as e:
            print(f"Error collecting training sample: {str(e)}")
    
    def scan_symbol(self, symbol, exchange, timeframes):
        """Enhanced scanning with ML predictions"""
        try:
            # Get data for primary timeframe
            primary_tf = timeframes[0]
            ohlcv = exchange.fetch_ohlcv(symbol, primary_tf, limit=100)
            if len(ohlcv) < 52:  # Need enough data for Ichimoku
                return
                
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df = self.calculate_features(df)
            if df is None:
                return
                
            # Get sentiment data
            sentiment = self.get_sentiment_score(symbol)
            
            # Prepare features for ML prediction
            latest = df.iloc[-1].copy()
            latest['sentiment_score'] = sentiment
            features = pd.DataFrame([latest[self.feature_columns]])
            
            # In training mode, just collect data
            if self.training_mode:
                self.collect_training_sample(symbol, exchange, primary_tf)
                return
                
            # Make prediction (returns -1, 0, or 1)
            prediction = self.predict_direction(features)
            
            # Check Ichimoku conditions
            uptrend = all(
                self.check_timeframe_up(symbol, tf, exchange)
                for tf in timeframes
            )
            
            downtrend = all(
                self.check_timeframe_down(symbol, tf, exchange)
                for tf in timeframes
            )
            
            # Generate appropriate alert
            if uptrend and prediction == 1:
                self.alert(symbol, "STRONG UPTREND", timeframes)
            elif downtrend and prediction == -1:
                self.alert(symbol, "STRONG DOWNTREND", timeframes)
            elif uptrend:
                self.alert(symbol, "UPTREND", timeframes)
            elif downtrend:
                self.alert(symbol, "DOWNTREND", timeframes)
                
        except Exception as e:
            print(f"Error scanning {symbol}: {str(e)}")
    
    def check_timeframe_up(self, symbol, timeframe, exchange):
        """Check if symbol is in uptrend on given timeframe"""
        try:
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=100)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df = self.calculate_features(df)
            
            ssb = df['ichimoku_b'].iloc[-1]
            ssa = df['ichimoku_a'].iloc[-1]
            kijun = df['kijun_sen'].iloc[-1]
            tenkan = df['tenkan_sen'].iloc[-1]
            chikou = df['chikou_span'].iloc[-27] if len(df) > 27 else 0
            price_close = df['close'].iloc[-1]
            price_open = df['open'].iloc[-1]
            
            # Basic uptrend conditions
            above_cloud = (price_close > max(ssa, ssb))
            above_kijun = (price_close > kijun)
            above_tenkan = (price_close > tenkan)
            rising = (price_close > price_open)
            
            return above_cloud and above_kijun and above_tenkan and rising
        except:
            return False
    
    def check_timeframe_down(self, symbol, timeframe, exchange):
        """Check if symbol is in downtrend on given timeframe"""
        try:
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=100)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df = self.calculate_features(df)
            
            ssb = df['ichimoku_b'].iloc[-1]
            ssa = df['ichimoku_a'].iloc[-1]
            kijun = df['kijun_sen'].iloc[-1]
            tenkan = df['tenkan_sen'].iloc[-1]
            chikou = df['chikou_span'].iloc[-27] if len(df) > 27 else 0
            price_close = df['close'].iloc[-1]
            price_open = df['open'].iloc[-1]
            
            # Basic downtrend conditions
            below_cloud = (price_close < min(ssa, ssb))
            below_kijun = (price_close < kijun)
            below_tenkan = (price_close < tenkan)
            falling = (price_close < price_open)
            
            return below_cloud and below_kijun and below_tenkan and falling
        except:
            return False
    
    def alert(self, symbol, trend_type, timeframes):
        """Generate alert for detected trend"""
        message = f"({trend_type}) detected for {symbol} on {timeframes} at {datetime.now()}"
        print(message)
        
        if self.enable_tweet:
            self.tweet(message)
    
    def tweet(self, message):
        """Send tweet with trading alert"""
        try:
            auth = tweepy.OAuthHandler(
                self.twitter_auth_keys['consumer_key'],
                self.twitter_auth_keys['consumer_secret']
            )
            auth.set_access_token(
                self.twitter_auth_keys['access_token'],
                self.twitter_auth_keys['access_token_secret']
            )
            api = tweepy.API(auth, wait_on_rate_limit=True)
            
            tweet_msg = f"{message} #Ichimoku #ML #Trading #Crypto"
            api.update_status(status=tweet_msg)
        except Exception as e:
            print(f"Error tweeting: {str(e)}")

# Main execution
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-e", "--exchange", help="Exchange name", required=True)
    parser.add_argument("-f", "--filter", help="Asset filter", required=True)
    parser.add_argument("-tf", "--timeframes", help="Timeframes to scan (comma separated)", required=True)
    parser.add_argument("--train", help="Run in training mode", action="store_true")
    args = parser.parse_args()
    
    scanner = MLIchimokuScanner(training_mode=args.train)
    
    # Initialize exchange
    exchange = scanner.exchanges.get(args.exchange.lower())
    if not exchange:
        print(f"Exchange {args.exchange} not supported")
        sys.exit(1)
    
    # Get markets
    try:
        markets = exchange.fetch_markets()
    except Exception as e:
        print(f"Error fetching markets: {str(e)}")
        sys.exit(1)
    
    # Filter symbols
    symbols = [
        m['id'] for m in markets 
        if m['active'] and args.filter in m['id']
    ]
    
    if not symbols:
        print(f"No symbols found matching filter {args.filter}")
        sys.exit(1)
    
    # In training mode, collect data first
    if args.train:
        print(f"Running in training mode for {len(symbols)} symbols")
        for symbol in symbols:
            scanner.collect_training_sample(symbol, exchange)
        
        # After collecting data, train model
        if scanner.train_initial_model():
            print("Training completed successfully")
        else:
            print("Not enough data collected for training")
        sys.exit(0)
    
    # In scanning mode, check if we have a trained model
    if not hasattr(scanner.model, 'classes_'):
        print("Warning: No trained model available. Running with basic Ichimoku scanning only.")
    
    # Scan symbols
    timeframes = args.timeframes.split(',')
    print(f"Scanning {len(symbols)} symbols on timeframes {timeframes}")
    
    for symbol in symbols:
        scanner.scan_symbol(symbol, exchange, timeframes)
