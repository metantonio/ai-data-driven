from app.services.llm_service import LLMService
import json

class ErrorAnalysisAgent:
    def __init__(self, llm_service: LLMService):
        self.llm = llm_service

    def analyze_error(self, code: str, stderr: str, schema_analysis: dict) -> dict:
        """
        Analyzes the failed code and stderr to provide a structured summary.
        Returns a dictionary: {"summary": str, "fix_type": "QUICK_FIX"|"FULL_REPAIR", "quick_fix_details": dict|None}
        """
        ml_objective = schema_analysis.get('ml_objective')
        ml_objective_section = f"\nUser ML Objective: {ml_objective}\n" if ml_objective else ""

        prompt = f"""
        You are a Senior Machine Learning Engineer and Debugging Expert.
        A Python ML pipeline failed to execute. Analyze the error and provide a structured summary in JSON format.

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
        1. Identify the exact technical cause.
        2. Categorize the fix: 
           - "QUICK_FIX": For missing imports (e.g. 'name "np" is not defined') or single-line fixes.
           - "FULL_REPAIR": For logic errors, schema mismatches, or multi-line repairs.
        3. If QUICK_FIX and it's a missing import, specify which one.
        
        Return ONLY a JSON object with this structure:
        {{
            "summary": "Concise human-readable explanation (max 2 sentences).",
            "fix_type": "QUICK_FIX" or "FULL_REPAIR",
            "quick_fix_details": {{
                "action": "add_import",
                "library": "library_name_to_import"
            }} (or null if not a quick fix)
        }}
        """
        
        try:
            response = self.llm.generate_response(prompt).strip()
            # Clean up potential markdown formatting
            if response.startswith("```json"):
                response = response[7:-3].strip()
            elif response.startswith("```"):
                response = response[3:-3].strip()
            
            return json.loads(response)
        except Exception as e:
            return {
                "summary": f"Failed to analyze error: {str(e)}. Raw error: {stderr[:100]}",
                "fix_type": "FULL_REPAIR",
                "quick_fix_details": None
            }
