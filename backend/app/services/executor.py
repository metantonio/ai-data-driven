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

                # Create an async generator that merges both streams
                async def get_all_updates():
                    stdout_gen = stream_output(process.stdout, False)
                    stderr_gen = stream_output(process.stderr, True)
                    
                    next_stdout = asyncio.ensure_future(stdout_gen.__anext__())
                    next_stderr = asyncio.ensure_future(stderr_gen.__anext__())
                    
                    while True:
                        done, pending = await asyncio.wait(
                            [next_stdout, next_stderr],
                            return_when=asyncio.FIRST_COMPLETED
                        )
                        
                        if next_stdout in done:
                            try:
                                yield await next_stdout
                                next_stdout = asyncio.ensure_future(stdout_gen.__anext__())
                            except StopAsyncIteration:
                                next_stdout = None
                                
                        if next_stderr in done:
                            try:
                                yield await next_stderr
                                next_stderr = asyncio.ensure_future(stderr_gen.__anext__())
                            except StopAsyncIteration:
                                next_stderr = None
                                
                        if next_stdout is None and next_stderr is None:
                            break
                        
                        # If one is None, we just wait for the other
                        if next_stdout is None:
                            await asyncio.wait([next_stderr])
                            continue
                        if next_stderr is None:
                            await asyncio.wait([next_stdout])
                            continue

                async for update in get_all_updates():
                    yield update

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
