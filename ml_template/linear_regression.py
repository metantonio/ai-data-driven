import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score
import json

# [PLACEHOLDER] Data Loading
def load_data():
    pass

# [PLACEHOLDER] Preprocessing
def preprocess_data(df):
    return df

# [PLACEHOLDER] Model Training
def train_model(X_train, y_train):
    model = LinearRegression()
    model.fit(X_train, y_train)
    return model

def main():
    try:
        # 1. Load Data
        df = load_data()
        
        # 2. Preprocess
        df_processed = preprocess_data(df)
        
        # 3. Split
        target_col = 'target' # [PLACEHOLDER] Agent must replace this
        
        # Ensure string column names for Sklearn
        df_processed.columns = df_processed.columns.astype(str)
        
        X = df_processed.drop(columns=[target_col])
        
        # Drop non-numeric columns (Timestamp, etc.)
        X = X.select_dtypes(include=['number'])
        
        y = df_processed[target_col]
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # 4. Train
        model = train_model(X_train, y_train)
        
        # 5. Evaluate
        predictions = model.predict(X_test)
        mse = mean_squared_error(y_test, predictions)
        r2 = r2_score(y_test, predictions)
        
        report = {
            "metrics": {
                "mse": float(mse),
                "r2": float(r2)
            },
            "model_type": "Linear Regression",
            "features": list(X.columns),
            "target": target_col
        }
        print(json.dumps(report))
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        # Ensure we exit with non-zero code if it fails, allowing backend to catch it
        exit(1)

if __name__ == "__main__":
    main()
