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
def execute_code(request: ExecuteRequest):
    try:
        executor = ExecutorService()
        result = executor.execute_code(request.code)
        
        # Auto-Correction Logic
        if result.get("return_code") != 0 and request.schema_analysis:
            print("Execution failed. Triggering auto-correction...")
            agent = CodeAdaptationAgent(llm_service)
            max_retries = 3
            
            for attempt in range(max_retries):
                print(f"Auto-correction attempt {attempt + 1}/{max_retries}")
                try:
                    # Fix the code
                    fixed_code = agent.fix_code(request.code, result["stderr"], request.schema_analysis)
                    
                    # Execute fixed code
                    new_result = executor.execute_code(fixed_code)
                    
                    # Update result
                    result = new_result
                    
                    # If successful, break
                    if result.get("return_code") == 0:
                        print("Auto-correction successful!")
                        break
                    else:
                        # Update code for next iteration to fix the NEW code's error
                        request.code = fixed_code
                        
                except Exception as inner_e:
                    print(f"Auto-correction failed: {inner_e}")
                    # Continue or break? Let's continue to try again if we have retries left, 
                    # but honestly if the agent fails to generate, we might be stuck.
                    # For now just continue.
                    continue
                    
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
