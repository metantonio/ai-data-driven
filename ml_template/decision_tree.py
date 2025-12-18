import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score
import joblib
import os
import json

# [PLACEHOLDER] Data Loading
def load_data():
    pass

# [PLACEHOLDER] Preprocessing
def preprocess_data(df):
    return df

# [PLACEHOLDER] Model Training
def train_model(X_train, y_train):
    model = DecisionTreeClassifier(random_state=42)
    model.fit(X_train, y_train)
    return model

def main():
    try:
        # 1. Load Data
        df = load_data()
        
        # 2. Preprocess
        df_processed = preprocess_data(df)
        
        # 3. Split
        target_col = 'target' # [PLACEHOLDER] Agent must replace
        
        # Ensure string column names
        df_processed.columns = df_processed.columns.astype(str)
        
        X = df_processed.drop(columns=[target_col])
        X = X.select_dtypes(include=['number']) # Only numeric features
        
        y = df_processed[target_col]
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # 4. Train
        print(f"Training Decision Tree Classifier...")
        model = train_model(X_train, y_train)
        
        # 5. Evaluate
        predictions = model.predict(X_test)
        accuracy = accuracy_score(y_test, predictions)
        
        # Feature Importance
        importances = model.feature_importances_
        feature_importance = [
            {"feature": f, "importance": float(i)} 
            for f, i in zip(X.columns, importances)
        ]
        feature_importance = sorted(feature_importance, key=lambda x: x['importance'], reverse=True)[:10]
        
        # 6. Save Model
        os.makedirs('models', exist_ok=True)
        model_path = 'models/model.joblib'
        joblib.dump(model, model_path)
        
        report = {
            "metrics": {
                "accuracy": float(accuracy)
            },
            "model_type": "Decision Tree Classifier",
            "features": list(X.columns),
            "target": target_col,
            "model_path": model_path,
            "feature_importance": feature_importance
        }
        print(json.dumps(report))

    except Exception as e:
        import traceback
        traceback.print_exc()
        import sys; sys.exit(1)

if __name__ == "__main__":
    main()
