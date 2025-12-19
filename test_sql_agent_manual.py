import sys
import os
import pandas as pd
import sqlite3
from unittest.mock import MagicMock

# Add backend to path
sys.path.append(os.path.abspath("backend"))

from app.services.simple_eda_service import SimpleEDAService

def setup_db():
    conn = sqlite3.connect("test_eda.db")
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT, age INTEGER)")
    cursor.execute("DELETE FROM users") # Clear old data
    cursor.execute("INSERT INTO users (id, name, age) VALUES (1, 'Alice', 30)")
    cursor.execute("INSERT INTO users (id, name, age) VALUES (2, 'Bob', 25)")
    conn.commit()
    conn.close()
    return "sqlite:///test_eda.db"

def test_sql_agent():
    try:
        conn_str = setup_db()
        service = SimpleEDAService()
        
        # Mock LLM to avoid real calls and ensure deterministic SQL
        service.llm = MagicMock()
        # First call: Bad SQL (to test retry)
        # Second call: Good SQL
        service.llm.generate_response.side_effect = [
            "SELECT * FROM non_existent_table", # Fail
            "SELECT * FROM users"               # Success
        ]
        service.use_llm = True
        
        print("Testing SQL Agent with Retry...")
        result = service.generate_sql_with_retry(conn_str, "Show me all users")
        
        print("AI Message:", result['ai_message'])
        print("Artifacts:", result['artifacts'].keys())
        
        history = result['artifacts']['sql_history']
        print(f"History length: {len(history)}")
        for item in history:
            print(f"Attempt {item['attempt']}: {item['status']} - {item.get('error') or item.get('sql')}")
            
        if len(history) == 2 and history[0]['status'] == 'error' and history[1]['status'] == 'success':
            print("\nSUCCESS: Retry logic verified!")
        else:
            print("\nFAILURE: Retry logic did not work as expected.")
            
    except Exception as e:
        print(f"\nCRITICAL ERROR during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_sql_agent()
