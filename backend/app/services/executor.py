import subprocess
import tempfile
import os
import json
import sys

class ExecutorService:
    def execute_code(self, code: str) -> dict:
        """
        Executes the provided Python code in a separate process.
        Returns a dictionary containing stdout, stderr, and any parsed JSON report.
        """
        # Create a temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
            temp_file.write(code)
            temp_file_path = temp_file.name

        try:
            # Run the code
            result = subprocess.run(
                [sys.executable, temp_file_path],
                capture_output=True,
                text=True,
                timeout=60  # Timeout after 60 seconds
            )
            
            stdout = result.stdout
            stderr = result.stderr
            return_code = result.returncode
            
            # Try to parse the last line as JSON (Standardized Reporting)
            parsed_report = None
            try:
                lines = stdout.strip().split('\n')
                if lines:
                    last_line = lines[-1]
                    parsed_report = json.loads(last_line)
            except json.JSONDecodeError:
                parsed_report = None

            return {
                "stdout": stdout,
                "stderr": stderr,
                "return_code": return_code,
                "report": parsed_report
            }

        except subprocess.TimeoutExpired:
            return {
                "stdout": "",
                "stderr": "Execution timed out.",
                "return_code": -1,
                "report": None
            }
        except Exception as e:
            return {
                "stdout": "",
                "stderr": str(e),
                "return_code": -1,
                "report": None
            }
        finally:
            # Cleanup
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
