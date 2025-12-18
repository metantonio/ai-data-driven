import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv, set_key
from pathlib import Path

router = APIRouter()

# Try to locate the .env file robustly
def get_env_path():
    # Check current dir, then parent, then backend/
    paths = [
        Path(".env"),
        Path("backend/.env"),
        Path("../.env"),
        Path("../../backend/.env")
    ]
    for p in paths:
        if p.exists():
            return p
    # Default to creating one in the current dir if none found
    return Path(".env")

ENV_PATH = get_env_path()

class Settings(BaseModel):
    LLM_PROVIDER: str
    LLM_API_URL: str
    LLM_MODEL: str
    DATABASE_URL: str
    LLM_API_KEY: str = "mock"

@router.get("/")
def get_settings():
    load_dotenv(dotenv_path=ENV_PATH, override=True)
    return {
        "LLM_PROVIDER": os.getenv("LLM_PROVIDER", "ollama"),
        "LLM_API_URL": os.getenv("LLM_API_URL", "http://localhost:11434/api/generate"),
        "LLM_MODEL": os.getenv("LLM_MODEL", "qwen2.5-coder:7b"),
        "DATABASE_URL": os.getenv("DATABASE_URL", "sqlite:///../data/data.db"),
        "LLM_API_KEY": os.getenv("LLM_API_KEY", "mock"),
    }

@router.post("/")
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
