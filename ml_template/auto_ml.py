import sys
import os
import pandas as pd
import numpy as np
import json
import joblib
import time
from sqlalchemy import create_engine
from sklearn.model_selection import train_test_split, RandomizedSearchCV
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, mean_squared_error, r2_score
import xgboost as xgb
import shap

# Reasoning:
# 1. Load data from the provided connection string.
# 2. Preprocess data (missing values, encoding).
# 3. Determine if task is classification or regression.
# 4. Use RandomizedSearchCV to test multiple models (RF, GB, XGB).
# 5. Select the best model and evaluate.
# 6. Calculate SHAP values for the best model.
# 7. Save model and metadata to the registry.

def load_data():
    engine = create_engine("{{connection_string}}")
    query = "{{query}}"
    return pd.read_sql_query(query, engine)

def preprocess_data(df):
    target_col = "{{target_column}}"
    
    # Simple preprocessing
    X = df.drop(columns=[target_col])
    y = df[target_col]
    
    # Handle missing values
    for col in X.columns:
        if X[col].dtype == 'object':
            X[col] = X[col].fillna(X[col].mode()[0] if not X[col].mode().empty else 'Unknown')
        else:
            X[col] = X[col].fillna(X[col].mean())
            
    # Encode categorical features
    X = pd.get_dummies(X)
    
    # Ensure all names are strings (for some models)
    X.columns = X.columns.astype(str)
    
    return X, y, target_col

def main():
    try:
        df = load_data()
        X, y, target_col = preprocess_data(df)
        
        # Determine if classification or regression
        is_classification = y.nunique() < 20 or y.dtype == 'object'
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        if is_classification:
            models = {
                'rf': (RandomForestClassifier(), {
                    'n_estimators': [50, 100, 200],
                    'max_depth': [None, 10, 20, 30],
                    'min_samples_split': [2, 5, 10]
                }),
                'xgb': (xgb.XGBClassifier(eval_metric='logloss'), {
                    'n_estimators': [50, 100, 200],
                    'learning_rate': [0.01, 0.1, 0.2],
                    'max_depth': [3, 5, 7]
                }),
                'gb': (GradientBoostingClassifier(), {
                    'n_estimators': [50, 100],
                    'learning_rate': [0.01, 0.1],
                    'max_depth': [3, 5]
                })
            }
        else:
            models = {
                'rf': (RandomForestRegressor(), {
                    'n_estimators': [50, 100, 200],
                    'max_depth': [None, 10, 20],
                    'min_samples_split': [2, 5]
                }),
                'gb': (GradientBoostingRegressor(), {
                    'n_estimators': [50, 100],
                    'learning_rate': [0.01, 0.1],
                    'max_depth': [3, 5]
                })
            }
            
        best_score = -np.inf
        best_model = None
        best_name = ""
        
        for name, (model, params) in models.items():
            print(f"Optimizing {name}...", flush=True)
            search = RandomizedSearchCV(model, params, n_iter=5, cv=3, random_state=42, n_jobs=-1, verbose=1)
            search.fit(X_train, y_train)
            if search.best_score_ > best_score:
                best_score = search.best_score_
                best_model = search.best_estimator_
                best_name = name
                
        y_pred = best_model.predict(X_test)
        
        metrics = {}
        if is_classification:
            metrics = {
                "accuracy": float(accuracy_score(y_test, y_pred)),
                "f1": float(f1_score(y_test, y_pred, average='weighted')),
                "precision": float(precision_score(y_test, y_pred, average='weighted')),
                "recall": float(recall_score(y_test, y_pred, average='weighted'))
            }
        else:
            metrics = {
                "mse": float(mean_squared_error(y_test, y_pred)),
                "r2": float(r2_score(y_test, y_pred))
            }
            
        # SHAP calculation for best model
        try:
            if hasattr(best_model, "feature_importances_") or "xgb" in best_name:
                explainer = shap.Explainer(best_model, X_train)
                shap_values = explainer(X_test)
                importance = np.abs(shap_values.values).mean(0)
                if len(importance.shape) > 1: # multi-class
                    importance = importance.mean(1)
                shap_importance = {col: float(imp) for col, imp in zip(X.columns, importance)}
            else:
                shap_importance = {}
        except:
            shap_importance = {}

        # Save to Registry
        run_id = f"auto_ml_{int(time.time())}"
        run_dir = os.path.join('models', run_id)
        os.makedirs(run_dir, exist_ok=True)
        
        joblib.dump(best_model, os.path.join(run_dir, 'model.joblib'))
        
        metadata = {
            "run_id": run_id,
            "timestamp": time.ctime(),
            "metrics": metrics,
            "model_type": f"AutoML ({best_model.__class__.__name__})",
            "features": list(X.columns),
            "target": target_col,
            "shap_importance": shap_importance
        }
        
        with open(os.path.join(run_dir, 'metadata.json'), 'w') as f:
            json.dump(metadata, f)

        report = {
            "status": "success",
            "metrics": metrics,
            "best_algorithm": best_model.__class__.__name__,
            "run_id": run_id,
            "shap_importance": shap_importance
        }
        print(json.dumps(report))

    except Exception as e:
        import traceback
        print(f"Error: {str(e)}", file=sys.stderr)
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
