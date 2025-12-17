import asyncio
import json
from app.agents.error_analysis import ErrorAnalysisAgent
from app.services.llm_service import LLMService

async def test_error_analysis():
    llm = LLMService()
    agent = ErrorAnalysisAgent(llm)
    
    # Simulating a common ML error: Missing column in preprocessing
    failed_code = """
import pandas as pd
from sklearn.linear_model import LinearRegression

def preprocess(df):
    return df[['target', 'age', 'income']] # income is missing in schema

df = pd.DataFrame({'target': [1,2], 'age': [20,30]})
preprocess(df)
"""
    stderr = "KeyError: \"['income'] not in index\""
    schema_analysis = {
        "analysis": "Dataset contains target and age. income is NOT present.",
        "raw_schema": {"tables": [{"name": "users", "columns": [{"name": "target"}, {"name": "age"}]}]}
    }
    
    print("Testing ErrorAnalysisAgent...")
    summary = agent.analyze_error(failed_code, stderr, schema_analysis)
    print("\n--- AI ERROR SUMMARY ---")
    print(summary)
    print("------------------------\n")
    
    assert len(summary) > 0
    print("Test Passed!")

if __name__ == "__main__":
    asyncio.run(test_error_analysis())
