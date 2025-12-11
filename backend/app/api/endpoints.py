from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.llm_service import LLMService
from app.agents.schema_analysis import SchemaAnalysisAgent
from app.agents.code_adaptor import CodeAdaptationAgent

router = APIRouter()
llm_service = LLMService()

class AnalyzeRequest(BaseModel):
    connection_string: str

class AdaptRequest(BaseModel):
    schema_analysis: dict

@router.post("/analyze-schema")
def analyze_schema(request: AnalyzeRequest):
    try:
        agent = SchemaAnalysisAgent(llm_service)
        result = agent.analyze(request.connection_string)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/adapt-code")
def adapt_code(request: AdaptRequest):
    try:
        agent = CodeAdaptationAgent(llm_service)
        result = agent.adapt(request.schema_analysis)
        return {"code": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from app.services.executor import ExecutorService
from app.agents.insights import InsightsAgent

class ExecuteRequest(BaseModel):
    code: str

class InsightsRequest(BaseModel):
    execution_report: dict
    schema_analysis: dict

@router.post("/execute-code")
def execute_code(request: ExecuteRequest):
    try:
        executor = ExecutorService()
        result = executor.execute_code(request.code)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-insights")
def generate_insights(request: InsightsRequest):
    try:
        agent = InsightsAgent(llm_service)
        insights = agent.generate_insights(request.execution_report, request.schema_analysis)
        return {"insights": insights}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
