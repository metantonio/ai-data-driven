from app.services.db_inspector import DatabaseInspector
from app.services.llm_service import LLMService

class SchemaAnalysisAgent:
    def __init__(self, llm_service: LLMService):
        self.llm = llm_service

    def analyze(self, connection_string: str, algorithm_type: str = "linear_regression") -> dict:
        # Resolve connection string early
        connection_string = DatabaseInspector.resolve_connection_string(connection_string)
        
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

    def analyze_with_comments(self, connection_string: str, user_comments: dict, algorithm_type: str = "linear_regression") -> dict:
        # Resolve connection string early
        connection_string = DatabaseInspector.resolve_connection_string(connection_string)
        
        # 1. Inspect Database
        inspector = DatabaseInspector(connection_string)
        schema_summary = inspector.get_schema_summary()
        
        # 2. Prompt LLM to analyze the schema WITH user comments
        prompt = f"""
        You are an expert Data Scientist. Analyze the following database schema for a '{algorithm_type}' task.
        
        User Comments on Data Dictionary:
        {user_comments}
        
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
        
        IMPORTANT: Use the "User Comments" to strictly interpret the meaning of columns. 
        If a user says a column is a target or contains specific info, trust it over the variable name.

        Schema:
        {schema_summary}
        """
        
        analysis = self.llm.generate_response(prompt)
        
        return {
            "raw_schema": schema_summary,
            "analysis": analysis,
            "connection_string": connection_string,
            "user_comments": user_comments
        }
