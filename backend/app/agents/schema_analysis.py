from app.services.db_inspector import DatabaseInspector
from app.services.llm_service import LLMService

class SchemaAnalysisAgent:
    def __init__(self, llm_service: LLMService):
        self.llm = llm_service

    def analyze(self, connection_string: str) -> dict:
        # 1. Inspect Database
        inspector = DatabaseInspector(connection_string)
        schema_summary = inspector.get_schema_summary()
        
        # 2. Prompt LLM to analyze the schema
        prompt = f"""
        You are an expert Data Scientist. Analyze the following database schema and identify:
        1. The main topics/entities.
        2. Potential target variables for regression or classification.
        3. Useful features and potential join paths.

        Schema:
        {schema_summary}
        """
        
        analysis = self.llm.generate_response(prompt)
        
        return {
            "raw_schema": schema_summary,
            "analysis": analysis,
            "connection_string": connection_string
        }
