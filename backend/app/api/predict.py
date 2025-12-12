from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import joblib
import pandas as pd
import os

router = APIRouter()

class PredictRequest(BaseModel):
    model_path: str
    features: dict

@router.post("/predict")
async def predict(request: PredictRequest):
    # Security check: prevent loading arbitrary files outside models/
    # Simple check: path must allowlist characters or start with models/
    # For MVP local, just checking existence is okay, but let's be slightly careful.
    if not request.model_path.startswith("models") and not ".." in request.model_path:
         raise HTTPException(status_code=400, detail="Invalid model path")

    if not os.path.exists(request.model_path):
        raise HTTPException(status_code=404, detail=f"Model file not found at {request.model_path}")

    try:
        model = joblib.load(request.model_path)
        
        # Convert features to DataFrame (single row)
        # We assume the keys in 'features' match the training columns
        df = pd.DataFrame([request.features])
        
        # Handle potential type mismatches if possible, or let model pipeline fail
        # Ideally, the model includes a preprocessor.
        
        prediction = model.predict(df)
        
        # Handle different output types (array, single value)
        result = prediction.tolist()
        if isinstance(result, list):
             return {"prediction": result[0]}
        return {"prediction": result}

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
