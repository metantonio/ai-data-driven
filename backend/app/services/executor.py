import subprocess
import tempfile
import os
import json
import sys
import asyncio
import threading
import queue

from app.agents.error_analysis import ErrorAnalysisAgent
from app.agents.code_adaptor import CodeAdaptationAgent

class ExecutorService:
    async def _run_with_heartbeat(self, func, *args, status="info", message="AI is thinking...", **kwargs):
        """Runs a blocking function in a thread while yielding heartbeat updates."""
        task = asyncio.create_task(asyncio.to_thread(func, *args, **kwargs))
        while not task.done():
            yield {"status": status, "message": message}
            try:
                await asyncio.wait_for(asyncio.shield(task), timeout=3.0)
            except asyncio.TimeoutError:
                continue
        yield await task

    async def execute_code(self, code: str, schema_analysis: dict, llm_service, max_retries: int = 2):
        """
        Executes the provided Python code.
        Yields status updates: {"status": "info" | "error" | "success" | "fixing" | "final_error", "message": str, "data": ...}
        """
        try:
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

            # 2. Run Subprocess using a thread-safe approach for Windows compatibility
            try:
                yield {"status": "info", "message": "Running pipeline script...", "data": {"code": current_code}}
                
                stdout_chunks = []
                stderr_chunks = []
                update_queue = asyncio.Queue()
                loop = asyncio.get_running_loop()

                process = subprocess.Popen(
                    [sys.executable, temp_file_path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1,
                    encoding='utf-8',
                    errors='replace'
                )

                def reader_thread(pipe, is_stderr):
                    try:
                        for line in iter(pipe.readline, ''):
                            line_str = line.rstrip()
                            if not line_str:
                                continue
                            if is_stderr:
                                stderr_chunks.append(line_str)
                                loop.call_soon_threadsafe(update_queue.put_nowait, {"status": "info", "message": f"[STDERR] {line_str}"})
                            else:
                                stdout_chunks.append(line_str)
                                try:
                                    # Don't log the final JSON report as info
                                    json.loads(line_str)
                                except:
                                    loop.call_soon_threadsafe(update_queue.put_nowait, {"status": "info", "message": line_str})
                    finally:
                        pipe.close()

                threading.Thread(target=reader_thread, args=(process.stdout, False), daemon=True).start()
                threading.Thread(target=reader_thread, args=(process.stderr, True), daemon=True).start()

                # Consume updates from the queue while the process is running
                while process.poll() is None or not update_queue.empty():
                    try:
                        update = await asyncio.wait_for(update_queue.get(), timeout=0.5)
                        yield update
                    except asyncio.TimeoutError:
                        continue
                
                # Final flush of the queue
                while not update_queue.empty():
                    yield update_queue.get_nowait()

                return_code = process.returncode
                stdout = "\n".join(stdout_chunks)
                stderr = "\n".join(stderr_chunks)

                if return_code == 0:
                    try:
                        # Extract the last line for the JSON report
                        last_line = stdout_chunks[-1] if stdout_chunks else "{}"
                        report = json.loads(last_line)
                        yield {"status": "success", "message": "Execution successful", "data": {"stdout": stdout, "stderr": stderr, "report": report, "code": current_code}}
                        return
                    except (json.JSONDecodeError, IndexError):
                        yield {"status": "success", "message": "Execution finished (no JSON report)", "data": {"stdout": stdout, "stderr": stderr, "report": None, "code": current_code}}
                        return
                
                else:
                    # SUBPROCESS FAILED - Analyze Error
                    yield {"status": "info", "message": "Pipeline failed. AI is analyzing the cause...", "data": {"stderr": stderr}}
                    
                    try:
                        # Use heartbeat for analysis
                        async for update in self._run_with_heartbeat(
                            error_analyzer.analyze_error, current_code, stderr, schema_analysis,
                            status="info", message="AI is analyzing the error details..."
                        ):
                            if isinstance(update, dict) and "status" in update and update["status"] == "info":
                                yield update
                            else:
                                error_summary = update
                        
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
                            # Use heartbeat for fixing
                            async for update in self._run_with_heartbeat(
                                adapter.fix_code, current_code, stderr, schema_analysis, error_summary, error_history,
                                status="fixing", message="AI is generating a fixed version of the code..."
                            ):
                                if isinstance(update, dict) and "status" in update and update["status"] == "fixing":
                                    yield update
                                else:
                                    current_code = update
                                    
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
