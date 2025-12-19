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

    def analyze_with_comments(self, connection_string: str, user_comments: dict, algorithm_type: str = "linear_regression", selected_tables: list = None, ml_objective: str = None) -> dict:
        # Resolve connection string early
        connection_string = DatabaseInspector.resolve_connection_string(connection_string)
        
        # 1. Inspect Database
        inspector = DatabaseInspector(connection_string)
        schema_summary = inspector.get_schema_summary()
        
        # 2. Filter schema to only include selected tables
        if selected_tables and len(selected_tables) > 0:
            filtered_schema = {"tables": {}}
            for table_name in selected_tables:
                if table_name in schema_summary.get("tables", {}):
                    filtered_schema["tables"][table_name] = schema_summary["tables"][table_name]
            schema_summary = filtered_schema
        
        # 3. Prompt LLM to analyze the schema WITH user comments
        tables_count = len(schema_summary.get("tables", {}))
        multi_table_guidance = ""
        if tables_count > 1:
            multi_table_guidance = f"""
        
        CRITICAL - MULTI-TABLE ANALYSIS:
        The user has selected {tables_count} tables for this analysis. This strongly suggests that:
        1. You MUST use data from MULTIPLE tables, not just one.
        2. You MUST identify appropriate JOIN keys between tables.
        3. You MUST explain how combining these tables creates a richer feature set.
        4. Using only ONE table when multiple are available is likely INCORRECT unless there's a very specific reason.
        
        When analyzing, explicitly state:
        - Which tables will be joined
        - What are the join keys (primary/foreign key relationships)
        - How each table contributes features to the model
        - Why this multi-table approach makes sense for {algorithm_type}
        """

        ml_objective_section = ""
        if ml_objective:
            ml_objective_section = f"""
        USER ML OBJECTIVE:
        "{ml_objective}"
        
        Analyze the schema SPECIFICALLY with this objective in mind. How do these tables and columns help achieve this goal?
        """
        
        prompt = f"""
        You are an expert Data Scientist. Analyze the following database schema for a '{algorithm_type}' task.
        
        {ml_objective_section}
        
        User Comments on Data Dictionary:
        {user_comments}
        {multi_table_guidance}
        
        Identify:
        1. The main topics/entities.
        2. SUITABILITY FOR {algorithm_type.upper()}.
           - If Time Series: Identify the Date/Time column and the Target Value.
           - If Classification: Identify the Categorical Target.
           - If Regression: Identify the Continuous Target.
           - If Clustering: Identify numeric feature columns.
           - If Association Rules: Identify Transaction ID and Item ID.
           - If Optimization: Identify Constraints and Objectives.
        3. Potential features and join paths relevant to this algorithm and objective.
        
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
            "user_comments": user_comments,
            "selected_tables": selected_tables or [],
            "ml_objective": ml_objective
        }
