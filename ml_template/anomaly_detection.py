import sys
import os
import pandas as pd
import numpy as np
import json
import joblib
import time
from sqlalchemy import create_engine
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

# Reasoning:
# 1. Load data.
# 2. Select numeric columns for anomaly detection.
# 3. Scale the data.
# 4. Fit IsolationForest.
# 5. Identify top anomalies (outliers).
# 6. Save results to the registry.

def load_data():
    engine = create_engine("{{connection_string}}")
    query = "{{query}}"
    return pd.read_sql_query(query, engine)

def main():
    try:
        df = load_data()
        
        # Select numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if not numeric_cols:
             print(json.dumps({"status": "error", "message": "No numeric columns found for anomaly detection."}))
             sys.exit(1)
             
        X = df[numeric_cols].copy()
        for col in X.columns:
            X[col] = X[col].fillna(X[col].mean())
            
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Isolation Forest
        # contamination='auto' or a fixed ratio. Let's use 0.05 (5%)
        model = IsolationForest(contamination=0.05, random_state=42)
        model.fit(X_scaled)
        
        # Predict: -1 for outliers, 1 for inliers
        df['anomaly_score'] = model.decision_function(X_scaled)
        df['is_anomaly'] = model.predict(X_scaled)
        
        anomalies = df[df['is_anomaly'] == -1].sort_values('anomaly_score')
        
        # Metrics
        metrics = {
            "total_rows": len(df),
            "anomalies_found": len(anomalies),
            "anomaly_ratio": float(len(anomalies) / len(df))
        }
        
        # Save to Registry
        run_id = f"anomaly_{int(time.time())}"
        run_dir = os.path.join('models', run_id)
        os.makedirs(run_dir, exist_ok=True)
        
        joblib.dump(model, os.path.join(run_dir, 'model.joblib'))
        
        metadata = {
            "run_id": run_id,
            "timestamp": time.ctime(),
            "metrics": metrics,
            "model_type": "Isolation Forest Anomaly Detection",
            "features": numeric_cols,
            "target": "is_anomaly",
            "shap_importance": {} # SHAP not directly applicable to IF easily here
        }
        
        with open(os.path.join(run_dir, 'metadata.json'), 'w') as f:
            json.dump(metadata, f)

        report = {
            "status": "success",
            "metrics": metrics,
            "run_id": run_id,
            "top_anomalies": anomalies.head(10).to_dict('records')
        }
        print(json.dumps(report))

    except Exception as e:
        import traceback
        print(f"Error: {str(e)}", file=sys.stderr)
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
