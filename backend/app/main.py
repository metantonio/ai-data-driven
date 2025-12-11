from fastapi import FastAPI

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

from app.api.endpoints import router as api_router
app.include_router(api_router, prefix="/api")
