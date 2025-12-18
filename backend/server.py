import uvicorn
import os
import sys
import multiprocessing
import webbrowser
import threading
import time
from pathlib import Path
from app.main import app

# This allows for bundling with PyInstaller
if getattr(sys, 'frozen', False):
    # If the app is run from a bundle, the 'meipass' directory is where it's unpacked
    current_dir = Path(sys._MEIPASS)
else:
    current_dir = Path(__file__).parent

def start_server():
    print(f"Starting QLX-AI-Data-Science-App Server...")
    print(f"Running from: {current_dir}")
    
    # We use 'app.main:app' as the import string so uvicorn can find it
    # Adding 'backend' to sys.path if needed
    backend_path = str(current_dir)
    if backend_path not in sys.path:
        sys.path.append(backend_path)
        
    # Function to open browser after a delay
    def open_browser():
        time.sleep(1.5)  # Give time for the server to bind the port
        webbrowser.open("http://127.0.0.1:8000")

    # Start browser thread
    threading.Thread(target=open_browser, daemon=True).start()

    uvicorn.run(
        app, 
        host="127.0.0.1", 
        port=8000, 
        reload=False, 
        workers=1,
        log_level="info",
        use_colors=False
    )

if __name__ == "__main__":
    # Required for some platforms when using multiprocessing and freeze
    multiprocessing.freeze_support()
    
    # Check if we are being asked to run a script instead of starting the server
    # This prevents port conflicts when the executor runs generated code in frozen mode
    if len(sys.argv) > 1 and sys.argv[1].endswith(".py"):
        import runpy
        import builtins
        # Inject exit/quit if they don't exist (common in frozen apps and runpy environments)
        if not hasattr(builtins, 'exit'):
            builtins.exit = sys.exit
        if not hasattr(builtins, 'quit'):
            builtins.quit = sys.exit
            
        script_path = sys.argv[1]
        print(f"Executing script: {script_path}")
        try:
            # Set sys.argv correctly for the script
            # sys.argv[0] should be the script path, or we can keep the exe path
            # but usually scripts expect argv[0] to be their name.
            original_argv = sys.argv[:]
            sys.argv = [script_path] + sys.argv[2:]
            runpy.run_path(script_path, run_name="__main__")
            sys.exit(0)
        except Exception as e:
            print(f"Error executing script: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    
    start_server()
