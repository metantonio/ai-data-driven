import asyncio
import sys
import unittest
from unittest.mock import MagicMock
import os

# Add backend/app to path if needed
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app.services.executor import ExecutorService

class TestExecutorStreaming(unittest.IsolatedAsyncioTestCase):
    async def test_streaming_output(self):
        executor = ExecutorService()
        llm_service = MagicMock()
        
        # A simple python script that prints something, sleeps, and prints again
        test_code = """
import time
import sys
print("Starting...")
sys.stdout.flush()
time.sleep(2)
print("Middle...")
sys.stdout.flush()
time.sleep(2)
print('{"status": "success", "metrics": {"test": 1}}')
"""
        
        updates = []
        async for update in executor.execute_code(test_code, {}, llm_service):
            updates.append(update)
            print(f"Received update: {update['status']} - {update['message'][:50]}")
        
        # Verify we got updates during execution
        info_messages = [u for u in updates if u['status'] == 'info']
        self.assertTrue(any("Starting..." in u['message'] for u in info_messages))
        self.assertTrue(any("Middle..." in u['message'] for u in info_messages))
        
        # Verify success
        success_update = next((u for u in updates if u['status'] == 'success'), None)
        self.assertIsNotNone(success_update)
        self.assertEqual(success_update['data']['report']['metrics']['test'], 1)

if __name__ == "__main__":
    unittest.main()
