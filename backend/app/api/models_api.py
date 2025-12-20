from fastapi import APIRouter, HTTPException
import os
import json
from typing import List, Dict, Any
from pathlib import Path

router = APIRouter()

MODELS_DIR = Path("models")
MODELS_DIR.mkdir(parents=True, exist_ok=True)

@router.get("/models")
async def list_models():
    """List all model runs with their metadata."""
    if not MODELS_DIR.exists():
        return []
    
    runs = []
    for run_dir in MODELS_DIR.iterdir():
        if run_dir.is_dir():
            metadata_path = run_dir / "metadata.json"
            if metadata_path.exists():
                try:
                    with open(metadata_path, 'r') as f:
                        meta = json.load(f)
                        runs.append(meta)
                except Exception as e:
                    print(f"Error reading metadata for {run_dir.name}: {e}")
    
    # Sort by timestamp (latest first)
    # Note: timestamp is a string, so we might need better parsing or use folder ctime
    return sorted(runs, key=lambda x: os.path.getctime(MODELS_DIR / x['run_id']), reverse=True)

@router.get("/models/{run_id}")
async def get_model_details(run_id: str):
    """Get detailed metadata for a specific run."""
    run_path = MODELS_DIR / run_id
    if not run_path.exists() or not run_path.is_dir():
        raise HTTPException(status_code=404, detail="Run not found")
    
    metadata_path = run_path / "metadata.json"
    if not metadata_path.exists():
        raise HTTPException(status_code=404, detail="Metadata not found")
    
    with open(metadata_path, 'r') as f:
        return json.load(f)

@router.delete("/models/{run_id}")
async def delete_model(run_id: str):
    """Delete a model run."""
    run_path = MODELS_DIR / run_id
    if not run_path.exists() or not run_path.is_dir():
        raise HTTPException(status_code=404, detail="Run not found")
    
    import shutil
    try:
        shutil.rmtree(run_path)
        return {"status": "success", "message": f"Run {run_id} deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
