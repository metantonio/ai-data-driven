from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

app = FastAPI(title="AI-Data-Driven ML System", version="0.1.0")

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "ok", "message": "Service is running"}

@app.get("/")
def read_root():
    return {"message": "Welcome to the AI-Data-Driven ML System API"}

from app.api import endpoints, predict, eda, settings
app.include_router(endpoints.router, prefix="/api")
app.include_router(predict.router, prefix="/api")
app.include_router(eda.router, prefix="/api/eda")
app.include_router(settings.router, prefix="/api/settings")

# Serve static files in production
# The 'static' folder should contain the contents of the frontend 'dist' folder
STATIC_PATH = Path(__file__).parent.parent / "static"

if STATIC_PATH.exists():
    # Mount assets folder for JS/CSS
    if (STATIC_PATH / "assets").exists():
        app.mount("/assets", StaticFiles(directory=str(STATIC_PATH / "assets")), name="static")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # Exclude API routes from catch-all
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404)
            
        file_path = STATIC_PATH / full_path
        if file_path.is_file():
            return FileResponse(str(file_path))
            
        # Fallback to index.html for SPA routes
        index_file = STATIC_PATH / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))
            
        raise HTTPException(status_code=404, detail="Not found")
