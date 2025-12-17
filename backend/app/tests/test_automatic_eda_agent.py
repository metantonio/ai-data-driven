import asyncio
import os
import sys

# Add the project root to sys.path to allow imports from app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app.services.llm_service import LLMService
from app.agents.automatic_eda import AutomaticEDAAgent

async def test_automatic_eda():
    llm_service = LLMService()
    agent = AutomaticEDAAgent(llm_service)
    
    # Use the example casino database if it exists, otherwise a generic one
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'example_casino.db'))
    if not os.path.exists(db_path):
        db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'example.db'))
    
    connection_string = f"sqlite:///{db_path}"
    user_comments = {"casinos": {"rating": "Target variable for prediction"}}
    algorithm_type = "linear_regression"
    
    print(f"Starting EDA Agent Test with DB: {connection_string}")
    print("-" * 50)
    
    async for update in agent.run_analysis(connection_string, user_comments, algorithm_type):
        status = update.get('status')
        message = update.get('message')
        data = update.get('data')
        
        print(f"[{status.upper()}] {message}")
        if status == 'thought':
            print(f"   Thoughts: {data.get('thought')}")
            # print(f"   Results Preview: {data.get('results')[:100]}...")
        if status == 'success':
            print(f"   Suggestions: {data.get('suggestions')}")
        if status == 'error':
            print(f"   Error details: {data}")
    
    print("-" * 50)
    print("Test Completed.")

if __name__ == "__main__":
    asyncio.run(test_automatic_eda())
