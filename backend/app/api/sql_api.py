from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import json
import os
from pathlib import Path

router = APIRouter()
DATA_DIR = Path("data")
FAVORITES_FILE = DATA_DIR / "favorites.json"

class FavoriteSQL(BaseModel):
    id: Optional[str] = None
    title: str
    query: str
    description: Optional[str] = ""
    connection_string: Optional[str] = ""
    timestamp: Optional[str] = None

def load_favorites() -> List[dict]:
    if not FAVORITES_FILE.exists():
        return []
    try:
        with open(FAVORITES_FILE, 'r') as f:
            return json.load(f)
    except Exception:
        return []

def save_favorites(favorites: List[dict]):
    DATA_DIR.mkdir(exist_ok=True)
    with open(FAVORITES_FILE, 'w') as f:
        json.dump(favorites, f, indent=2)

@router.get("/sql/favorites")
async def get_favorites():
    return load_favorites()

@router.post("/sql/favorites")
async def save_favorite(fav: FavoriteSQL):
    favorites = load_favorites()
    import time
    
    new_fav = fav.model_dump()
    if not new_fav.get('id'):
        new_fav['id'] = f"fav_{int(time.time())}"
    if not new_fav.get('timestamp'):
        new_fav['timestamp'] = time.ctime()
    
    # Check if exists (by title or query to avoid duplicates)
    for existing in favorites:
        if existing['query'].strip() == fav.query.strip():
             return existing
             
    favorites.append(new_fav)
    save_favorites(favorites)
    return new_fav

@router.delete("/sql/favorites/{fav_id}")
async def delete_favorite(fav_id: str):
    favorites = load_favorites()
    new_favorites = [f for f in favorites if f['id'] != fav_id]
    if len(new_favorites) == len(favorites):
        raise HTTPException(status_code=404, detail="Favorite not found")
    save_favorites(new_favorites)
    return {"status": "success"}
