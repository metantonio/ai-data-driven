class LLMService:
    def __init__(self, api_key: str = "mock"):
        self.api_key = api_key

    def generate_response(self, prompt: str) -> str:
        """
        Mock LLM response generator. 
        In a real scenario, this would call OpenAI/Gemini API.
        """
        print(f"[LLM Prompt]: {prompt[:100]}...")
        
        # Simple heuristic response for demonstration
        if "analyze the following database schema" in prompt.lower():
            return "The database contains user data and activity logs. The 'users' table is the central entity."
        
        if "adapt the following" in prompt.lower():
            return """
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score
from sqlalchemy import create_engine
import json

def load_data():
    # Connect to the DB (using a dummy connection string for example purposes, 
    # in real usage, would use the one from schema analysis if passed)
    # For this mock, we assume 'houses' table exists as per the task dscription.
    engine = create_engine("sqlite:///../example.db")
    df = pd.read_sql("SELECT * FROM houses", engine)
    return df

def preprocess_data(df):
    # Simple preprocessing: drop missing, handle basic types
    df = df.dropna()
    return df

def train_model(X_train, y_train):
    model = LinearRegression()
    model.fit(X_train, y_train)
    return model

def main():
    # 1. Load Data
    df = load_data()
    
    # 2. Preprocess
    df_processed = preprocess_data(df)
    
    # 3. Split
    # Heuristic: 'price' is a common target in the example dataset
    target_col = 'price'
    if target_col not in df_processed.columns:
        # Fallback if specific target not found, pick last column
        target_col = df_processed.columns[-1]
        
    X = df_processed.drop(columns=[target_col])
    y = df_processed[target_col]
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # 4. Train
    model = train_model(X_train, y_train)
    
    # 5. Evaluate
    predictions = model.predict(X_test)
    mse = mean_squared_error(y_test, predictions)
    r2 = r2_score(y_test, predictions)
    
    # Standardized Reporting
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
"""
            
        return "I am a mock AI agent."
