import os
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
        
        # Prepare Visualization Data (Sample of Actual vs Predicted)
        # Limit to 200 points to keep JSON size manageable
        viz_df = pd.DataFrame({'Actual': y_test, 'Predicted': predictions})
        if len(viz_df) > 200:
            viz_df = viz_df.sample(200, random_state=42)
            
        visualization_data = viz_df.to_dict(orient='records')
        
        # 6. SHAP Explanations
        import shap
        explainer = shap.Explainer(model, X_train)
        shap_values = explainer(X_test)
        
        # Global feature importance (mean absolute SHAP values)
        importance = np.abs(shap_values.values).mean(0)
        shap_importance = {col: float(imp) for col, imp in zip(X.columns, importance)}
        
        # 7. Save Model & Metadata (Model Registry)
        import joblib
        import os
        import time
        
        run_id = f"run_{int(time.time())}"
        run_dir = os.path.join('models', run_id)
        os.makedirs(run_dir, exist_ok=True)
        
        model_path = os.path.join(run_dir, 'model.joblib')
        joblib.dump(model, model_path)
        
        metadata = {
            "run_id": run_id,
            "timestamp": time.ctime(),
            "metrics": {
                "mse": float(mse),
                "r2": float(r2)
            },
            "model_type": "Linear Regression",
            "features": list(X.columns),
            "target": target_col,
            "shap_importance": shap_importance
        }
        
        with open(os.path.join(run_dir, 'metadata.json'), 'w') as f:
            json.dump(metadata, f)
            
        report = {
            # Legacy fields for backward compatibility
            **metadata,
            "model_path": model_path,
            "visualization_data": visualization_data
        }
        print(json.dumps(report))
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        # Ensure we exit with non-zero code if it fails, allowing backend to catch it
        import sys; sys.exit(1)

if __name__ == "__main__":
    main()
