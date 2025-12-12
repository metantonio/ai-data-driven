from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.llm_service import LLMService
from app.agents.schema_analysis import SchemaAnalysisAgent
from app.agents.code_adaptor import CodeAdaptationAgent

router = APIRouter()
llm_service = LLMService()

class AnalyzeRequest(BaseModel):
    connection_string: str
    algorithm_type: str = "linear_regression"

class AdaptRequest(BaseModel):
    schema_analysis: dict
    algorithm_type: str = "linear_regression"

@router.post("/analyze-schema")
async def analyze_schema_endpoint(request: AnalyzeRequest):
    try:
        agent = SchemaAnalysisAgent(llm_service)
        analysis = agent.analyze(request.connection_string, request.algorithm_type)
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/adapt-code")
def adapt_code(request: AdaptRequest):
    try:
        agent = CodeAdaptationAgent(llm_service)
        result = agent.adapt(request.schema_analysis, request.algorithm_type)
        return {"code": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from app.services.executor import ExecutorService
from app.agents.insights import InsightsAgent

class ExecuteRequest(BaseModel):
    code: str
    schema_analysis: dict = None

class InsightsRequest(BaseModel):
    execution_report: dict
    schema_analysis: dict

@router.post("/execute-code")
async def execute_code_endpoint(request: ExecuteRequest):
    from fastapi.responses import StreamingResponse
    import json

    async def event_generator():
        executor = ExecutorService()
        # Ensure schema_analysis is passed, default to empty dict if None
        analysis = request.schema_analysis or {}
        
        async for update in executor.execute_code(request.code, analysis, llm_service):
            yield json.dumps(update) + "\n"

    return StreamingResponse(event_generator(), media_type="application/x-ndjson")

@router.post("/generate-insights")
def generate_insights(request: InsightsRequest):
    try:
        agent = InsightsAgent(llm_service)
        insights = agent.generate_insights(request.execution_report, request.schema_analysis)
        return {"insights": insights}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
