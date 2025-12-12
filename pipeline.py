import sqlite3
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score
import json

DB_NAME = "example_casino.db"

def load_data():
    """Load data from SQLite database into Pandas DataFrames"""
    conn = sqlite3.connect(DB_NAME)
    
    casinos_df = pd.read_sql_query("SELECT * FROM casinos", conn)
    games_df = pd.read_sql_query("SELECT * FROM games", conn)
    players_df = pd.read_sql_query("SELECT * FROM players", conn)
    game_sessions_df = pd.read_sql_query("SELECT * FROM game_sessions", conn)
    
    conn.close()
    return casinos_df, games_df, players_df, game_sessions_df

def preprocess_data(casinos_df, games_df, players_df, game_sessions_df):
    """Clean and merge dataframes into a single dataset"""
    
    # 1. Merge Sessions with Players
    # 'player_id' in sessions matches 'id' in players
    merged_df = pd.merge(game_sessions_df, players_df, left_on='player_id', right_on='id', how='left', suffixes=('', '_player'))
    
    # 2. Merge with Games
    # 'game_id' in sessions matches 'id' in games
    merged_df = pd.merge(merged_df, games_df, left_on='game_id', right_on='id', how='left', suffixes=('', '_game'))
    
    # 3. Merge with Casinos
    # 'casino_id' in games matches 'id' in casinos
    merged_df = pd.merge(merged_df, casinos_df, left_on='casino_id', right_on='id', how='left', suffixes=('', '_casino'))
    
    # Drop redundant ID columns from right tables if desired, but for ML features we might want some
    # We drop the 'id' columns that came from the right tables to avoid confusion (id_player, id_game, id_casino)
    merged_df.drop(columns=['id_player', 'id_game', 'id_casino'], inplace=True, errors='ignore')
    
    # Feature Engineering
    # Convert dates to datetime objects if not already
    merged_df['session_date'] = pd.to_datetime(merged_df['session_date'])
    merged_df['signup_date'] = pd.to_datetime(merged_df['signup_date'])
    merged_df['opened_date'] = pd.to_datetime(merged_df['opened_date'])
    
    # Create derived features
    merged_df['days_since_signup'] = (merged_df['session_date'] - merged_df['signup_date']).dt.days
    merged_df['hour_of_day'] = merged_df['session_date'].dt.hour
    
    # Encode categorical variables
    # Simple one-hot encoding or label encoding could be done here.
    # For this example, we'll select numeric columns + some categorical for dummy encoding
    
    return merged_df

def train_model(X_train, y_train):
    model = LinearRegression()
    model.fit(X_train, y_train)
    return model

def main():
    print("Loading data...")
    casinos_df, games_df, players_df, game_sessions_df = load_data()
    
    print("Preprocessing data...")
    df_processed = preprocess_data(casinos_df, games_df, players_df, game_sessions_df)
    
    # Prepare features for ML
    # Goal: Predict 'net_outcome' (win/loss amount) based on features
    target_col = 'net_outcome'
    
    # Select features
    feature_cols = [
        'duration_minutes', 'total_wagered', 'age', 
        'days_since_signup', 'hour_of_day', 'house_edge'
    ]
    
    # Filter for full data
    df_ml = df_processed.dropna(subset=feature_cols + [target_col])
    
    X = df_ml[feature_cols]
    y = df_ml[target_col]
    
    print(f"Training on {len(df_ml)} records...")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    model = train_model(X_train, y_train)
    
    predictions = model.predict(X_test)
    mse = mean_squared_error(y_test, predictions)
    r2 = r2_score(y_test, predictions)
    
    report = {
        "metrics": {
            "mse": mse,
            "r2": r2
        },
        "model_type": "LinearRegression",
        "features": feature_cols,
        "target": target_col
    }
    
    print("Model Training Complete.")
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()
