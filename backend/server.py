import uvicorn
import os
import sys
import multiprocessing
from pathlib import Path
from app.main import app

# This allows for bundling with PyInstaller
if getattr(sys, 'frozen', False):
    # If the app is run from a bundle, the 'meipass' directory is where it's unpacked
    current_dir = Path(sys._MEIPASS)
else:
    current_dir = Path(__file__).parent

def start_server():
    print(f"Starting AI-Data-Driven ML System Server...")
    print(f"Running from: {current_dir}")
    
    # We use 'app.main:app' as the import string so uvicorn can find it
    # Adding 'backend' to sys.path if needed
    backend_path = str(current_dir)
    if backend_path not in sys.path:
        sys.path.append(backend_path)
        
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
    start_server()
