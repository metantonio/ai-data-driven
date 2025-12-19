import os
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import json

# [PLACEHOLDER] Data Loading
def load_data():
    pass

# [PLACEHOLDER] Preprocessing
def preprocess_data(df):
    return df

def optimize_clusters(X, max_k=10):
    best_score = -1
    best_k = 2
    best_model = None
    
    # Needs at least 2 samples to cluster
    if len(X) < 2:
        return 1, None
        
    limit = min(max_k, len(X))
    
    for k in range(2, limit + 1):
        model = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = model.fit_predict(X)
        
        # Silhouette requires > 1 unique label
        if len(np.unique(labels)) > 1:
            score = silhouette_score(X, labels)
            if score > best_score:
                best_score = score
                best_k = k
                best_model = model
        
    return best_k, best_model, best_score

def main():
    try:
        # 1. Load Data
        df = load_data()
        
        # 2. Preprocess
        df_processed = preprocess_data(df)
        
        # 3. Select Features
        df_processed.columns = df_processed.columns.astype(str)
        X = df_processed.select_dtypes(include=['number'])
        
        if X.empty:
            raise ValueError("No numeric data found for clustering.")
            
        # 4. Train & Optimize (The "Agent" Logic)
        print(f"Optimizing number of clusters (k=2..10)...")
        best_k, model, score = optimize_clusters(X)
        
        if model is None:
             # Fallback if optimization failed (e.g. too little data)
             model = KMeans(n_clusters=2, random_state=42).fit(X)
             best_k = 2
             score = -1.0
             
             
        # 5. Evaluate
        
        # Prepare Visualization Data (PCA 2D projection if needed, or just 2 features)
        # For simplicity in this generic agent, we'll take the first 2 features if available
        visualization_data = []
        if X.shape[1] >= 2:
            viz_df = X.iloc[:, :2].copy()
            viz_df['cluster'] = model.labels_
            if len(viz_df) > 300:
                viz_df = viz_df.sample(300, random_state=42)
            visualization_data = viz_df.to_dict(orient='records')
            
        report = {
            "metrics": {
                "silhouette_score": float(score),
                "n_clusters": int(best_k),
                "optimization_status": "optimized"
            },
            "model_type": "K-Means Clustering (Auto-Optimized)",
            "features": list(X.columns),
            "cluster_centers": model.cluster_centers_.tolist(),
            "visualization_data": visualization_data
        }
        print(json.dumps(report))

    except Exception as e:
        import traceback
        traceback.print_exc()
        import sys; sys.exit(1)

if __name__ == "__main__":
    main()
