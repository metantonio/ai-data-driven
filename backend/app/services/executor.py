import subprocess
import tempfile
import os
import json
import sys
import asyncio
from app.agents.error_analysis import ErrorAnalysisAgent

class ExecutorService:
    async def execute_code(self, code: str, schema_analysis: dict, llm_service, max_retries: int = 2):
        """
        Executes the provided Python code.
        Yields status updates: {"status": "info" | "error" | "success" | "fixing" | "final_error", "message": str, "data": ...}
        """
        try:
            from app.agents.code_adaptor import CodeAdaptationAgent 
            error_analyzer = ErrorAnalysisAgent(llm_service)
        except Exception as startup_error:
             yield {"status": "final_error", "message": f"Executor startup failed: {str(startup_error)}", "data": {"code": code}}
             return
        current_code = code
        attempt = 0
        error_history = []  # Track previous errors to avoid repeating fixes

        while attempt <= max_retries:
            attempt += 1
            yield {"status": "info", "message": f"Execution attempt {attempt}/{max_retries + 1}...", "data": {"code": current_code}}

            # 1. Write Code to File
            try:
                with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
                    f.write(current_code)
                    temp_file_path = f.name
            except Exception as write_error:
                yield {"status": "final_error", "message": f"Failed to write temp file: {str(write_error)}", "data": None}
                return

            # 2. Run Subprocess
            try:
                yield {"status": "info", "message": "Running pipeline script...", "data": {"code": current_code}}
                
                def run_sync():
                    return subprocess.run(
                        [sys.executable, temp_file_path],
                        capture_output=True,
                        text=True,
                        encoding='utf-8'
                    )
                
                result = await asyncio.to_thread(run_sync)
                stdout = result.stdout
                stderr = result.stderr
                return_code = result.returncode

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
                    # SUBPROCESS FAILED - Analyze Error
                    yield {"status": "info", "message": "Pipeline failed. AI is analyzing the cause...", "data": {"stderr": stderr}}
                    
                    try:
                        error_summary = error_analyzer.analyze_error(current_code, stderr, schema_analysis)
                        yield {"status": "error", "message": error_summary, "data": {"stderr": stderr, "is_ai_summary": True}}
                    except Exception as e:
                        error_summary = f"Pipeline execution failed. Error: {stderr[-500:]}"
                        yield {"status": "error", "message": error_summary, "data": {"stderr": stderr}}

                    # Add to error history
                    error_history.append({
                        "attempt": attempt,
                        "error": stderr[-500:],  # Last 500 chars to keep it manageable
                        "summary": error_summary
                    })

                    if attempt <= max_retries:
                        yield {"status": "fixing", "message": "AI is applying an automated fix..."}
                        
                        try:
                            adapter = CodeAdaptationAgent(llm_service)
                            current_code = adapter.fix_code(current_code, stderr, schema_analysis, error_summary, error_history)
                            yield {"status": "info", "message": "Fix applied. Retrying...", "data": {"code": current_code}}
                        except Exception as fix_error:
                             yield {"status": "error", "message": f"Auto-fixer failed: {str(fix_error)}. Retrying with original code...", "data": None}
                    else:
                        yield {"status": "final_error", "message": "Max retries reached. Execution failed.", "data": {"stdout": stdout, "stderr": stderr, "report": None, "code": current_code, "error_summary": error_summary}}
                        return

            except Exception as e:
                 import traceback
                 traceback.print_exc()
                 yield {"status": "final_error", "message": f"System error: {str(e)}", "data": {"stdout": "", "stderr": str(e), "report": None, "code": current_code}}
                 return
            finally:
                if os.path.exists(temp_file_path):
                    try:
                        os.remove(temp_file_path)
                    except:
                        pass

        # Fallback if loop finishes unexpectedly
        yield {"status": "final_error", "message": "Execution ended without reaching success state.", "data": {"code": current_code}}
