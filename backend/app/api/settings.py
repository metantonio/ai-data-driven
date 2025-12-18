import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv, set_key
from pathlib import Path
import sys
import signal

router = APIRouter()

# Try to locate the .env file robustly
def get_env_path():
    # If running as executable, look for .env next to the .exe file
    if getattr(sys, 'frozen', False):
        exe_dir = Path(sys.executable).parent
        env_file = exe_dir / ".env"
        print(f"Frozen mode: Looking for .env at {env_file}")
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

@router.get("/settings")
def get_settings():
    load_dotenv(dotenv_path=ENV_PATH, override=True)
    return {
        "LLM_PROVIDER": os.getenv("LLM_PROVIDER", "ollama"),
        "LLM_API_URL": os.getenv("LLM_API_URL", "http://localhost:11434/api/generate"),
        "LLM_MODEL": os.getenv("LLM_MODEL", "qwen2.5-coder:7b"),
        "DATABASE_URL": os.getenv("DATABASE_URL", "sqlite:///../example.db"),
        "LLM_API_KEY": os.getenv("LLM_API_KEY", "mock"),
    }

@router.post("/settings")
def update_settings(settings: Settings):
    try:
        # Create .env if it doesn't exist
        if not ENV_PATH.exists():
            with open(ENV_PATH, "w") as f:
                f.write("")
            
        set_key(str(ENV_PATH.absolute()), "LLM_PROVIDER", settings.LLM_PROVIDER)
        set_key(str(ENV_PATH.absolute()), "LLM_API_URL", settings.LLM_API_URL)
        set_key(str(ENV_PATH.absolute()), "LLM_MODEL", settings.LLM_MODEL)
        set_key(str(ENV_PATH.absolute()), "DATABASE_URL", settings.DATABASE_URL)
        set_key(str(ENV_PATH.absolute()), "LLM_API_KEY", settings.LLM_API_KEY)
        
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
