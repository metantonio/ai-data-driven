from app.services.llm_service import LLMService
import json

class ErrorAnalysisAgent:
    def __init__(self, llm_service: LLMService):
        self.llm = llm_service

    def analyze_error(self, code: str, stderr: str, schema_analysis: dict) -> str:
        """
        Analyzes the failed code and stderr to provide a human-readable summary.
        """
        ml_objective = schema_analysis.get('ml_objective')
        ml_objective_section = f"\nUser ML Objective: {ml_objective}\n" if ml_objective else ""

        prompt = f"""
        You are a Senior Machine Learning Engineer and Debugging Expert.
        A Python ML pipeline failed to execute. Your job is to analyze the error and provide a concise, human-readable summary of the ROOT CAUSE and HOW TO FIX IT.

        {ml_objective_section}
        Dataset Context (Analysis):
        {schema_analysis.get('analysis', 'N/A')}

        Raw Schema Info:
        {schema_analysis.get('schema_context', str(schema_analysis.get('raw_schema', '')))}

        Error Message (stderr):
        {stderr}

        Failed Code Snippet:
        {code[:2000]}... (truncated if long)

        Tasks:
        1. Identify the exact technical cause (e.g., column 'X' missing in table 'Y', data type mismatch, memory error).
        2. Explain it in plain language for the user.
        3. Suggest the specific step to fix it (e.g., 'Ensure you use column_a for merging instead of column_b'). 
           CRITICAL: The fix you suggest MUST use columns and tables that EXPLICITLY exist in the 'Raw Schema Info'.
        4. Be VERY concise (max 3-4 sentences).

        Return ONLY the text summary.
        """
        
        try:
            summary = self.llm.generate_response(prompt).strip()
            return summary
        except Exception as e:
            return f"Failed to analyze error: {str(e)}. Raw error: {stderr[:200]}"
