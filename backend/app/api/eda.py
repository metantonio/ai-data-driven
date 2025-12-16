
from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from app.services.simple_eda_service import SimpleEDAService
import os
import traceback
import pandas as pd
from sqlalchemy import create_engine, inspect as sql_inspect

router = APIRouter()

class EDARequest(BaseModel):
    question: str
    connection_string: str
    query: Optional[str] = None

class EDAResponse(BaseModel):
    ai_message: str
    tool_calls: List[str]
    artifacts: Optional[Dict[str, Any]] = None

@router.post("/chat", response_model=EDAResponse)
async def chat_eda(request: EDARequest):
    try:
        # Initialize simple EDA service
        service = SimpleEDAService()
        
        # Check if user wants to see available tables
        if any(word in request.question.lower() for word in ['show tables', 'list tables', 'available tables', 'what tables']):
            result = service.show_available_tables(request.connection_string)
            return result
        
        # Load Data
        df = load_data_from_db(request.connection_string, request.query)
        
        if df.empty:
            return {
                "ai_message": "The dataset loaded is empty.",
                "tool_calls": [],
                "artifacts": {}
            }

        # Process query with simple EDA
        result = service.analyze_dataset(df, request.question)
        
        return result

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

def load_data_from_db(connection_string: str, query: str = None, limit: int = 1000) -> pd.DataFrame:
    """
    Helper to load data from DB into DataFrame.
    """
    engine = create_engine(connection_string)
    
    if query:
        return pd.read_sql(query, engine)
    
    # Auto-discovery
    inspector = sql_inspect(engine)
    tables = inspector.get_table_names()
    if not tables:
        raise ValueError("No tables found in database.")
    
    # Just pick first table
    table = tables[0]
    return pd.read_sql(f"SELECT * FROM {table} LIMIT {limit}", engine)
