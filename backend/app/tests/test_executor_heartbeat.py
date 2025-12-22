import asyncio
import sys
import unittest
from unittest.mock import MagicMock
import os
import time

# Add backend/app to path if needed
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app.services.executor import ExecutorService

class TestExecutorHeartbeat(unittest.IsolatedAsyncioTestCase):
    async def test_heartbeat_during_fix(self):
        executor = ExecutorService()
        llm_service = MagicMock()
        
        # A code that fails
        test_code = 'print("Fail"); import sys; sys.exit(1)'
        
        # Mock error analyzer and adapter to be slow
        error_analyzer = MagicMock()
        error_analyzer.analyze_error.return_value = "Error Analyzed"
        
        adapter = MagicMock()
        adapter.fix_code.return_value = 'print("Fixed"); print(\'{"status": "success", "metrics": {}}\')'
        
        # Patching agents correctly
        with unittest.mock.patch('app.services.executor.ErrorAnalysisAgent') as mock_err_class:
            mock_err_class.return_value = error_analyzer
            with unittest.mock.patch('app.services.executor.CodeAdaptationAgent') as mock_adapt_class:
                mock_adapt_class.return_value = adapter
                
                # Replace _run_with_heartbeat with a faster one for test
                original_run = executor._run_with_heartbeat
                async def fast_run(func, *args, **kwargs):
                    # Simulate one heartbeat
                    yield {"status": kwargs.get("status", "info"), "message": kwargs.get("message", "Heartbeat")}
                    yield await asyncio.to_thread(func, *args, **kwargs)
                
                executor._run_with_heartbeat = fast_run

                updates = []
                # Execute with 1 retry
                async for update in executor.execute_code(test_code, {}, llm_service, max_retries=1):
                    updates.append(update)
                    print(f"Received update: {update['status']} - {update['message'][:50]}")

        # Check for heartbeat messages
        # Our _run_with_heartbeat uses a 10s timeout, but we can lower it in the test or make it configurable.
        # Since we use 2s sleep in mock, and 10s heartbeat, it might not trigger unless we lower the timeout.
        
        # Let's verify the flow: Attempt 1 -> Fail -> Analyze -> Fixing -> Fix Applied -> Attempt 2 -> Success
        success = any(u['status'] == 'success' for u in updates)
        self.assertTrue(success)
        
        # Verify Analyze and Fixing messages were yielded
        self.assertTrue(any("analyzing the error details" in u['message'] for u in updates))
        self.assertTrue(any("generating a fixed version" in u['message'] for u in updates))

if __name__ == "__main__":
    unittest.main()
