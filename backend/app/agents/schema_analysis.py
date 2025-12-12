from app.services.db_inspector import DatabaseInspector
from app.services.llm_service import LLMService

class SchemaAnalysisAgent:
    def __init__(self, llm_service: LLMService):
        self.llm = llm_service

    def analyze(self, connection_string: str, algorithm_type: str = "linear_regression") -> dict:
        # 1. Inspect Database
        inspector = DatabaseInspector(connection_string)
        schema_summary = inspector.get_schema_summary()
        
        # 2. Prompt LLM to analyze the schema
        prompt = f"""
        You are an expert Data Scientist. Analyze the following database schema for a '{algorithm_type}' task.
        
        Identify:
        1. The main topics/entities.
        2. SUITABILITY FOR {algorithm_type.upper()}.
           - If Time Series: Identify the Date/Time column and the Target Value.
           - If Classification: Identify the Categorical Target.
           - If Regression: Identify the Continuous Target.
           - If Clustering: Identify numeric feature columns.
           - If Association Rules: Identify Transaction ID and Item ID.
           - If Optimization: Identify Constraints and Objectives.
        3. Potential features and join paths relevant to this algorithm.

        Schema:
        {schema_summary}
        """
        
        analysis = self.llm.generate_response(prompt)
        
        return {
            "raw_schema": schema_summary,
            "analysis": analysis,
            "connection_string": connection_string
        }
