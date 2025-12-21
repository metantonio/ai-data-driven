import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv, set_key
from pathlib import Path
import sys
import signal
import requests
import sys
import os
import tempfile
import subprocess
from app.version import VERSION

router = APIRouter()

# Try to locate the .env file robustly
def get_env_path():
    # If running as executable, look for .env next to the .exe file
    if getattr(sys, 'frozen', False):
        exe_dir = Path(sys.executable).parent
        env_file = exe_dir / ".env"
        print(f"--- Frozen mode detected ---")
        print(f"Executable location: {sys.executable}")
        print(f"Looking for .env at: {env_file}")
        if not env_file.exists():
            print(f"Warning: .env file NOT found at {env_file}. Using default settings.")
        return env_file
    
    # Development mode paths
    paths = [
        Path(".env"),
        Path("backend/.env"),
        Path("../.env"),
        Path("../../backend/.env")
    ]
    for p in paths:
        if p.exists():
            return p
    return Path(".env")

ENV_PATH = get_env_path()

class Settings(BaseModel):
    LLM_PROVIDER: str
    LLM_API_URL: str
    LLM_MODEL: str
    DATABASE_URL: str
    LLM_API_KEY: str = "mock"
    MAX_RETRIES: int = 2

@router.get("/settings")
def get_settings():
    load_dotenv(dotenv_path=ENV_PATH, override=True)
    return {
        "LLM_PROVIDER": os.getenv("LLM_PROVIDER", "ollama"),
        "LLM_API_URL": os.getenv("LLM_API_URL", "http://localhost:11434/api/generate"),
        "LLM_MODEL": os.getenv("LLM_MODEL", "qwen2.5-coder:7b"),
        "DATABASE_URL": os.getenv("DATABASE_URL", "sqlite:///../example.db"),
        "LLM_API_KEY": os.getenv("LLM_API_KEY", "mock"),
        "MAX_RETRIES": int(os.getenv("MAX_RETRIES", "2")),
    }

@router.get("/version")
def get_version():
    return {"version": VERSION}

@router.get("/check-updates")
def check_updates():
    try:
        repo = "metantonio/ai-data-driven"
        url = f"https://api.github.com/repos/{repo}/releases/latest"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        latest_version = data.get("tag_name", "").replace("v", "")
        
        return {
            "current_version": VERSION,
            "latest_version": latest_version,
            "has_update": latest_version > VERSION,
            "release_notes": data.get("body", ""),
            "download_url": data.get("html_url", ""),
            "assets": data.get("assets", [])
        }
    except Exception as e:
        print(f"Error checking updates: {e}")
        return {
            "current_version": VERSION,
            "has_update": False,
            "error": str(e)
        }

@router.post("/trigger-update")
def trigger_update(download_url: str):
    """
    Experimental: Downloads the new version and prepares a batch script for replacement.
    This only works on Windows and when running as an executable.
    """
    if not getattr(sys, 'frozen', False):
        raise HTTPException(status_code=400, detail="Auto-update only available in bundled version (.exe)")

    try:
        # 1. Download the file (Assuming the URL is a direct download link or we find the asset)
        # Note: In a real scenario, we'd find the .exe asset in the request data.
        # For this demo, let's assume the user already provided the asset URL.
        
        response = requests.get(download_url, stream=True)
        response.raise_for_status()
        
        exe_path = sys.executable
        new_exe_path = exe_path + ".new"
        
        with open(new_exe_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                
        # 2. Create the batch script for replacement
        bat_content = f"""
@echo off
timeout /t 2 /nobreak > nul
move /y "{new_exe_path}" "{exe_path}"
start "" "{exe_path}"
del "%~f0"
"""
        bat_fd, bat_path = tempfile.mkstemp(suffix=".bat")
        with os.fdopen(bat_fd, 'w') as f:
            f.write(bat_content)
            
        # 3. Execute the script and exit
        subprocess.Popen([bat_path], shell=True)
        
        # Schedule shutdown
        def delayed_shutdown():
            import time
            time.sleep(1)
            os.kill(os.getpid(), signal.SIGINT)
            
        import threading
        threading.Thread(target=delayed_shutdown).start()
        
        return {"message": "Update started. The application will restart shortly."}
        
    except Exception as e:
        print(f"Update failed: {e}")
        raise HTTPException(status_code=500, detail=f"Update failed: {str(e)}")

@router.post("/settings")
def update_settings(settings: Settings):
    try:
        # Create .env if it doesn't exist
        if not ENV_PATH.exists():
            with open(ENV_PATH, "w") as f:
                f.write("")
        
        # Enforce hard limit of 50 for retries (51 attempts total)
        validated_retries = min(max(settings.MAX_RETRIES, 0), 49)
            
        set_key(str(ENV_PATH.absolute()), "LLM_PROVIDER", settings.LLM_PROVIDER)
        set_key(str(ENV_PATH.absolute()), "LLM_API_URL", settings.LLM_API_URL)
        set_key(str(ENV_PATH.absolute()), "LLM_MODEL", settings.LLM_MODEL)
        set_key(str(ENV_PATH.absolute()), "DATABASE_URL", settings.DATABASE_URL)
        set_key(str(ENV_PATH.absolute()), "LLM_API_KEY", settings.LLM_API_KEY)
        set_key(str(ENV_PATH.absolute()), "MAX_RETRIES", str(validated_retries))
        
        # Reload environment variables for the current process
        load_dotenv(dotenv_path=ENV_PATH, override=True)
        
        return {"message": "Settings updated successfully"}
    except Exception as e:
        print(f"Error updating .env: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update settings: {str(e)}")

@router.post("/settings/shutdown")
def shutdown():
    """Shuts down the application server."""
    print("Shutdown requested...")
    # Schedule shutdown after a short delay so the response can be sent
    def delayed_shutdown():
        import time
        time.sleep(1)
        # On Windows, SIGINT is generally handled well for graceful shutdown
        os.kill(os.getpid(), signal.SIGINT)
        
    import threading
    threading.Thread(target=delayed_shutdown).start()
    
    return {"message": "Application is shutting down. You can close this tab."}
