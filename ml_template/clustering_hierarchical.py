import pandas as pd
import numpy as np
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics import silhouette_score
import json

# [PLACEHOLDER] Data Loading
def load_data():
    pass

# [PLACEHOLDER] Preprocessing
def preprocess_data(df):
    return df

def main():
    try:
        df = load_data()
        df_processed = preprocess_data(df)
        
        df_processed.columns = df_processed.columns.astype(str)
        X = df_processed.select_dtypes(include=['number'])
        
        if X.empty: raise ValueError("No numeric data")
        
        # Hierarchical Clustering
        # Limit rows if data is huge because it's O(N^2) memory
        if len(X) > 5000:
            X = X.sample(5000, random_state=42)
            
        model = AgglomerativeClustering(n_clusters=3)
        labels = model.fit_predict(X)
        
        if len(set(labels)) > 1:
            sil_score = silhouette_score(X, labels)
        else:
            sil_score = -1.0
            
        report = {
            "metrics": {
                "silhouette_score": float(sil_score),
                "n_clusters": int(model.n_clusters)
            },
            "model_type": "Hierarchical Clustering",
            "features": list(X.columns)
        }
        print(json.dumps(report))

    except Exception as e:
        import traceback
        traceback.print_exc()
        exit(1)

if __name__ == "__main__":
    main()
