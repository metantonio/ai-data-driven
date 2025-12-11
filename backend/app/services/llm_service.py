import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

class LLMService:
    def __init__(self):
        self.provider = os.getenv("LLM_PROVIDER", "mock").lower()
        self.api_url = os.getenv("LLM_API_URL", "http://localhost:11434/api/generate")
        self.model = os.getenv("LLM_MODEL", "mistral")
        self.api_key = os.getenv("LLM_API_KEY", "mock")

    def generate_response(self, prompt: str) -> str:
        """
        Generates a response using the configured LLM provider.
        """
        print(f"[LLM Service]: Using provider '{self.provider}' for prompt: {prompt[:50]}...")

        if self.provider == "mock":
            return self._mock_response(prompt)
        
        elif self.provider == "ollama":
            return self._ollama_response(prompt)
            
        elif self.provider in ["vllm", "openai"]:
            return self._openai_compatible_response(prompt)
            
        else:
            return f"Error: Unknown LLM provider '{self.provider}'"

    def _ollama_response(self, prompt: str) -> str:
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False
            }
            response = requests.post(self.api_url, json=payload, timeout=120)
            response.raise_for_status()
            data = response.json()
            return data.get("response", "")
        except Exception as e:
            print(f"Error calling Ollama: {e}")
            return f"Error calling Ollama: {e}"

    def _openai_compatible_response(self, prompt: str) -> str:
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7
            }
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=120)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"Error calling vLLM/OpenAI: {e}")
            return f"Error calling vLLM/OpenAI: {e}"

    def _mock_response(self, prompt: str) -> str:
        # Heuristic response for demonstration
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
