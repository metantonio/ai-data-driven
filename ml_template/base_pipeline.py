import os
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score
import json

# [PLACEHOLDER] Data Loading
# Agent will inject code here to load data from the specific source
def load_data():
    pass

# [PLACEHOLDER] Preprocessing
# Agent will inject code here for cleaning and feature engineering
def preprocess_data(df):
    return df

# [PLACEHOLDER] Model Training
def train_model(X_train, y_train):
    model = LinearRegression()
    model.fit(X_train, y_train)
    return model

def main():
    # 1. Load Data
    df = load_data()
    
    # 2. Preprocess
    df_processed = preprocess_data(df)
    
    # 3. Split (Assumes 'target' column exists - Agent must adapt this)
    target_col = 'target' 
    
    # Ensure all column names are strings to avoid sklearn TypeError
    df_processed.columns = df_processed.columns.astype(str)
    
    X = df_processed.drop(columns=[target_col])
    
    # Drop non-numeric columns (like Datetime objects) that Sklearn can't handle
    X = X.select_dtypes(include=['number'])
    
    y = df_processed[target_col]
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # 4. Train
    model = train_model(X_train, y_train)
    
    # 5. Evaluate
    predictions = model.predict(X_test)
    mse = mean_squared_error(y_test, predictions)
    r2 = r2_score(y_test, predictions)
    
    # Standardized Reporting: Output JSON as the last line
    import json
    report = {
        "metrics": {
            "mse": mse,
            "r2": r2
        },
        "model_type": "LinearRegression",
        "features": list(X.columns),
        "target": target_col
    }
    print(json.dumps(report))

if __name__ == "__main__":
    main()
