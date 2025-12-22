import subprocess
import tempfile
import os
import json
import sys
import asyncio
from app.agents.error_analysis import ErrorAnalysisAgent
from app.agents.code_adaptor import CodeAdaptationAgent

class ExecutorService:
    async def _run_with_heartbeat(self, func, *args, status="info", message="AI is thinking...", **kwargs):
        """Runs a blocking function in a thread while yielding heartbeat updates."""
        task = asyncio.create_task(asyncio.to_thread(func, *args, **kwargs))
        while not task.done():
            yield {"status": status, "message": message}
            try:
                await asyncio.wait_for(asyncio.shield(task), timeout=5.0)
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

            # 2. Run Subprocess
            try:
                yield {"status": "info", "message": "Running pipeline script...", "data": {"code": current_code}}
                
                process = await asyncio.create_subprocess_exec(
                    sys.executable, temp_file_path,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )

                stdout_chunks = []
                async def read_stream(stream, status_prefix):
                    while True:
                        line = await stream.readline()
                        if not line:
                            break
                        line_str = line.decode('utf-8', errors='replace').rstrip()
                        if line_str:
                            if status_prefix == "stdout":
                                stdout_chunks.append(line_str)
                            # Yielding info for every line to keep connection alive
                            # We check if it's a JSON line at the end, but intermediate lines are useful logs
                            yield {"status": "info", "message": line_str}

                # Create tasks to read stdout and stderr concurrently
                async def consume_stdout():
                    async for update in read_stream(process.stdout, "stdout"):
                        yield update

                # For stderr, we just collect it to handle errors later, but we could also stream it
                stderr_chunks = []
                async def consume_stderr():
                    while True:
                        line = await process.stderr.readline()
                        if not line:
                            break
                        line_str = line.decode('utf-8', errors='replace').rstrip()
                        if line_str:
                            stderr_chunks.append(line_str)
                            yield {"status": "info", "message": f"LOG: {line_str}"}

                # We use a helper to merge these streams for the yield
                async def merged_streams():
                    tasks = [
                        asyncio.create_task(consume_stdout().__anext__()),
                        asyncio.create_task(consume_stderr().__anext__())
                    ]
                    # This is a bit complex for a simple yield. Let's simplify.
                
                # Simplified approach: Read stdout and stderr in the main loop or tasks
                async def stream_output(stream, is_stderr=False):
                    while True:
                        line = await stream.readline()
                        if not line:
                            break
                        line_str = line.decode('utf-8', errors='replace').rstrip()
                        if line_str:
                            if is_stderr:
                                stderr_chunks.append(line_str)
                                yield {"status": "info", "message": f"[STDERR] {line_str}"}
                            else:
                                stdout_chunks.append(line_str)
                                try:
                                    # Try to see if it's the final JSON report to avoid double-logging it as info
                                    json.loads(line_str)
                                except:
                                    yield {"status": "info", "message": line_str}

                # Create a queue to merge updates from both streams
                update_queue = asyncio.Queue()

                async def stream_reader(stream, is_stderr=False):
                    while True:
                        line = await stream.readline()
                        if not line:
                            break
                        line_str = line.decode('utf-8', errors='replace').rstrip()
                        if line_str:
                            if is_stderr:
                                stderr_chunks.append(line_str)
                                await update_queue.put({"status": "info", "message": f"[STDERR] {line_str}"})
                            else:
                                stdout_chunks.append(line_str)
                                try:
                                    # Don't log the final JSON report as info
                                    json.loads(line_str)
                                except:
                                    await update_queue.put({"status": "info", "message": line_str})

                # Run both readers concurrently
                stdout_task = asyncio.create_task(stream_reader(process.stdout, False))
                stderr_task = asyncio.create_task(stream_reader(process.stderr, True))

                # Yield from the queue until both readers are done
                while not stdout_task.done() or not stderr_task.done() or not update_queue.empty():
                    # If tasks are done but queue has items, consume them
                    # If tasks are not done, wait for queue or tasks
                    try:
                        # Wait for a brief moment to see if something arrives
                        update = await asyncio.wait_for(update_queue.get(), timeout=0.1)
                        yield update
                    except asyncio.TimeoutError:
                        # No update yet, just continue the loop to check tasks status
                        continue
                    except asyncio.CancelledError:
                        break

                await stdout_task
                await stderr_task

                return_code = await process.wait()
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
