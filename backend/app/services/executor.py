import subprocess
import tempfile
import os
import json
import sys

class ExecutorService:
    async def execute_code(self, code: str, schema_analysis: dict, llm_service):
        """
        Executes the provided Python code.
        Yields status updates: {"status": "info" | "error" | "success", "message": str, "data": ...}
        """
        from app.agents.code_adaptor import CodeAdaptationAgent 
        
        max_retries = 2
        current_code = code
        attempt = 0
        temp_file_path = "pipeline.py"

        while attempt <= max_retries:
            attempt += 1
            yield {"status": "info", "message": f"Execution attempt {attempt}/{max_retries + 1}...", "data": {"code": current_code}}

            # 1. Write Code to File
            with open(temp_file_path, "w") as f:
                f.write(current_code)

            # 2. Run Subprocess
            try:
                yield {"status": "info", "message": "Running pipeline script...", "data": {"code": current_code}}
                
                # Run async if possible, but here using blocking for simplicity within generator
                # In a real async app we'd use asyncio.create_subprocess_exec
                proc = subprocess.run(
                    [sys.executable, temp_file_path],
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                stdout = proc.stdout
                stderr = proc.stderr
                return_code = proc.returncode

                if return_code == 0:
                    try:
                        lines = stdout.strip().split('\n')
                        last_line = lines[-1] if lines else "{}"
                        report = json.loads(last_line)
                        yield {"status": "success", "message": "Execution successful", "data": {"stdout": stdout, "stderr": stderr, "report": report, "code": current_code}}
                        return
                    except json.JSONDecodeError:
                        yield {"status": "success", "message": "Execution finished (no JSON report)", "data": {"stdout": stdout, "stderr": stderr, "report": None, "code": current_code}}
                        return
                
                else:
                    yield {"status": "error", "message": f"Attempt {attempt} failed: {stderr[-200:]}..."}
                    
                    if attempt <= max_retries:
                        yield {"status": "fixing", "message": "Analyzing error and applying fix..."}
                        
                        adapter = CodeAdaptationAgent(llm_service)
                        current_code = adapter.fix_code(current_code, stderr, schema_analysis)
                        
                        yield {"status": "info", "message": "Fix applied. Retrying...", "data": {"code": current_code}}
                    else:
                        yield {"status": "final_error", "message": "Max retries reached. Execution failed.", "data": {"stdout": stdout, "stderr": stderr, "report": None, "code": current_code}}
                        return

            except subprocess.TimeoutExpired:
                yield {"status": "error", "message": "Execution timed out."}
                return
            except Exception as e:
                 yield {"status": "final_error", "message": f"System error: {str(e)}", "data": {"stdout": "", "stderr": str(e), "report": None, "code": current_code}}
                 return
            finally:
                if os.path.exists(temp_file_path):
                    try:
                         os.remove(temp_file_path)
                    except:
                        pass
