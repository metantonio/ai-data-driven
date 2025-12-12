import subprocess
import tempfile
import os
import json
import sys
import asyncio

class ExecutorService:
    async def execute_code(self, code: str, schema_analysis: dict, llm_service):
        """
        Executes the provided Python code.
        Yields status updates: {"status": "info" | "error" | "success", "message": str, "data": ...}
        """
        try:
            from app.agents.code_adaptor import CodeAdaptationAgent 
            
            max_retries = 2
            current_code = code
            attempt = 0

            while attempt <= max_retries:
                attempt += 1
                yield {"status": "info", "message": f"Execution attempt {attempt}/{max_retries + 1}...", "data": {"code": current_code}}
        except Exception as startup_error:
             yield {"status": "final_error", "message": f"Executor startup failed: {str(startup_error)}", "data": {"code": code}}
             return

        # Continue with loop logic (re-indented effectively, but replacing broadly helps)
        # To avoid massive re-indentation issues in replace_file_content with partial matches, 
        # I will target the specific block I want to wrap, but wait, the 'while' loop is large.
        
        # Let's try a different strategy. I will modify the start of the function to enter the try block 
        # but I have to match the existing indentation.
        # Actually in this specific tool, I can only replace contiguous blocks.
        # If I wrap the whole function body in try/except, I have to re-indent everything.
        # That's risky with replace_file_content on large file.
        
        # Instead, let's just use the `try...except` AROUND the `while` loop start logic in a way that doesn't require re-indenting the loop body if possible?
        # No, Python requires indentation.
        
        # Reset strategy: The loop usually runs. The error is likely the IMPORT or init.
        # So I will just wrap the import and init variables.
        
        try:
             from app.agents.code_adaptor import CodeAdaptationAgent 
        except Exception as e:
             yield {"status": "final_error", "message": f"Import failed: {str(e)}", "data": None}
             return

        max_retries = 2
        current_code = code
        attempt = 0

        while attempt <= max_retries:
             # ... (start of loop is same)

            attempt += 1
            yield {"status": "info", "message": f"Execution attempt {attempt}/{max_retries + 1}...", "data": {"code": current_code}}

            # 1. Write Code to File
            # Use tempfile to avoid triggering uvicorn reload by writing to watched directory
            try:
                print(f"[Executor] Writing code to temp file, attempt {attempt}")
                with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
                    f.write(current_code)
                    temp_file_path = f.name
                print(f"[Executor] Created temp file: {temp_file_path}")
            except Exception as write_error:
                print(f"[Executor] Failed to write temp file: {write_error}")
                raise write_error

            # 2. Run Subprocess
            try:
                yield {"status": "info", "message": "Running pipeline script...", "data": {"code": current_code}}
                
                # Use asyncio.to_thread for robust non-blocking execution on Windows
                print(f"[Executor] Launching subprocess (threaded): {sys.executable} {temp_file_path}")
                
                def run_sync():
                    return subprocess.run(
                        [sys.executable, temp_file_path],
                        capture_output=True,
                        text=True,
                        encoding='utf-8'
                    )
                
                # Offload blocking call to thread
                result = await asyncio.to_thread(run_sync)
                print(f"[Executor] Subprocess finished. RC={result.returncode}")

                stdout = result.stdout
                stderr = result.stderr
                return_code = result.returncode

                if return_code == 0:
                    print(f"[Executor] Execution Successful")
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
                    print(f"[Executor] Execution Failed. RC={return_code}. Stderr len={len(stderr)}")
                    yield {"status": "error", "message": f"Attempt {attempt} failed: {stderr[-1000:]}..."}
                    
                    if attempt <= max_retries:
                        yield {"status": "fixing", "message": "Analyzing error and applying fix..."}
                        
                        try:
                            adapter = CodeAdaptationAgent(llm_service)
                            current_code = adapter.fix_code(current_code, stderr, schema_analysis)
                            yield {"status": "info", "message": "Fix applied. Retrying...", "data": {"code": current_code}}
                        except Exception as fix_error:
                             yield {"status": "error", "message": f"Auto-fixer failed: {str(fix_error)}. Retrying with original code (risky)..."}
                             # Optional: we could continue loop with same code or break. 
                             # Let's just log and continue loop, maybe next run works (unlikely)?
                             # Or better, just let it fail next loop. 
                             pass
                    else:
                        yield {"status": "final_error", "message": "Max retries reached. Execution failed.", "data": {"stdout": stdout, "stderr": stderr, "report": None, "code": current_code}}
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
