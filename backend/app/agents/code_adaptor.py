from app.services.llm_service import LLMService
import os
import sys
import re
from pathlib import Path

class CodeAdaptationAgent:
    def __init__(self, llm_service: LLMService, template_path: str = None):
        self.llm = llm_service
        self.template_path = template_path

    def adapt(self, schema_analysis: dict, algorithm_type: str = "linear_regression", eda_summary: str = None, ml_objective: str = None) -> str:
        # Determine template based on algorithm_type
        template_map = {
            "linear_regression": "linear_regression.py",
            "logistic_regression": "logistic_regression.py",
            "kmeans": "clustering_kmeans.py",
            "hierarchical": "clustering_hierarchical.py",
            "time_series": "time_series.py",
            "linear_programming": "linear_programming.py",
            "mixed_integer_programming": "mixed_integer_programming.py",
            "reinforcement_learning": "reinforcement_learning.py",
            "association_rules": "association_rules.py",
            "random_forest": "random_forest.py",
            "decision_tree": "decision_tree.py",
            "auto_ml": "auto_ml.py",
            "anomaly_detection": "anomaly_detection.py"
        }
        
        filename = template_map.get(algorithm_type, "linear_regression.py")
        
        # Load Template
        try:
            # 1. Determine the base path for templates
            base_dir = getattr(sys, '_MEIPASS', os.getcwd())
            
            # 2. Strategy: Try specific path, then relative, then bundled path
            if self.template_path:
                path = self.template_path
            else:
                # Bundle path (PyInstaller) or Development path
                # When bundled, it's at 'ml_template' in the root of _MEIPASS
                bundled_path = os.path.join(base_dir, "ml_template", filename)
                # Development path relative to this file
                dev_path = os.path.join(os.path.dirname(__file__), "../../../ml_template", filename)
                
                if os.path.exists(bundled_path):
                    path = bundled_path
                else:
                    path = dev_path

            with open(path, 'r') as f:
                template_code = f.read()
        except FileNotFoundError:
             return f"# Error: Could not find template for {algorithm_type} at {path}. Current Dir: {os.getcwd()}, Base Dir: {base_dir}"

        # 2. Prompt LLM to fill placeholders
        connection_string = schema_analysis.get('connection_string', 'sqlite:///../example.db')
        selected_tables = schema_analysis.get('selected_tables', [])
        
        # Add multi-table enforcement guidance
        multi_table_enforcement = ""
        if selected_tables and len(selected_tables) > 1:
            table_list = ", ".join(selected_tables)
            multi_table_enforcement = f"""
        
        CRITICAL - MULTI-TABLE REQUIREMENT:
        The user has explicitly selected {len(selected_tables)} tables: {table_list}
        
        YOU MUST:
        1. Load data from ALL {len(selected_tables)} selected tables, not just one.
        2. Perform appropriate JOINs between these tables using primary/foreign key relationships.
        3. Verify that join keys exist in the 'Raw Schema' before using them.
        4. Create a unified dataset that combines features from all selected tables.
        5. If you cannot identify join keys, use the schema analysis to find relationships.
        
        EXAMPLE MULTI-TABLE IMPLEMENTATION:
        ```python
        def load_data():
            engine = create_engine("{connection_string}")
            
            # Load each table
            table1 = pd.read_sql_query("SELECT * FROM {selected_tables[0]}", engine)
            table2 = pd.read_sql_query("SELECT * FROM {selected_tables[1]}", engine)
            
            # Join tables (verify join keys from schema first!)
            # Example: df = table1.merge(table2, left_on='id', right_on='table1_id', how='inner')
            
            return df
        ```
        
        FAILURE TO USE ALL SELECTED TABLES IS UNACCEPTABLE.
        """

        ml_objective_section = ""
        if ml_objective:
            ml_objective_section = f"""
        USER ML OBJECTIVE:
        "{ml_objective}"
        
        CRITICAL: The code you generate MUST aim to solve this specific objective. 
        Adapt the SQL query in 'load_data' and the processing steps to select relevant features and target for this goal.
        """
        
        prompt = f"""
        You are a Machine Learning Engineer. Adapt the following Python ML template to work with the described dataset.
        
        TARGET ALGORITHM TO IMPLEMENT: {algorithm_type.replace('_', ' ').upper()}
        (IMPORTANT: Follow the user's latest selection even if the EDA analysis mentions a different initial choice).

        {ml_objective_section}

        Dataset Analysis:
        {schema_analysis['analysis']}

        {"EDA Findings & Context:" if eda_summary else ""}
        {eda_summary if eda_summary else ""}

        User Comments (Context):
        {schema_analysis.get('user_comments', 'None provided')}
        
        Raw Schema:
        {schema_analysis.get('schema_context', str(schema_analysis['raw_schema']))}
        
        Connection String:
        "{connection_string}"
        {multi_table_enforcement}
        
        Template Code:
        {template_code}
        
        tasks:
        1. REASONING: First, list the tables you will use and the specific columns you will use for each (especially for JOINs). 
           VERIFY each column exists in the provided 'Raw Schema'.
        2. CRITICAL: Ensure `import sys`, `import os`, and `from sqlalchemy import create_engine` are at the very top.
        3. Implement 'load_data' using the provided Connection String exactly.
           ```python
           # CORRECT IMPLEMENTATION EXAMPLE:
           from sqlalchemy import create_engine
           def load_data():
               # USE THIS EXACT STRING: {connection_string}
               engine = create_engine("{connection_string}")
               # DO NOT use sqlite3.connect(). USE the engine.
               query = "SELECT * FROM table_name" # Use real tables from schema, JOIN if needed for the objective
               return pd.read_sql_query(query, engine)
           ```
        4. CRITICAL: Check the schema for every table before joining.
           - {f"CONNECTION STRING TO USE: {connection_string}"}
           - DO NOT assume ANY column exists unless it is in the Raw Schema.
           - ONLY use columns listed in 'Raw Schema' below.
           - To JOIN, prioritize columns in 'FOREIGN KEYS'. Otherwise, match on identical column names (e.g. `order_id`).
           - VERIFY the column exists in BOTH tables before using it in a join.
        5. Implement 'preprocess_data' to handle missing values and encode categoricals. 
           - DO NOT use `df.fillna(inplace=True)`. Use `df[col] = df[col].fillna(...)`.
           - Use `df = pd.get_dummies(df, columns=[...])` for encoding.
        6. Select the target column based on the objective and analysis, and ensure it is categorical/binary if this is a classification task.
        7. CRITICAL: At the end, print the JSON report using `print(json.dumps(report))` WITHOUT indent parameter.
           - DO NOT use `json.dumps(report, indent=2)` or any formatting.
           - The JSON MUST be on a SINGLE LINE for the parser to work.
        8. Output your reasoning first (as comments), then the full valid Python code. No explanations outside the code block.
        """
        
        adapted_code = self.llm.generate_response(prompt)
        
        # Clean up the response to extract only the code
        import re
        # Look for ```python ... ``` or just ``` ... ```
        code_match = re.search(r'```(?:python)?\s*(.*?)```', adapted_code, re.DOTALL)
        if code_match:
            return code_match.group(1).strip()
            
        # Fallback: if no code blocks, potentially return the whole thing 
        # but unlikely to work if there is explanatory text. 
        # Let's try to remove any leading/trailing whitespace at least.
        return adapted_code.strip()

    def fix_code(self, original_code: str, error_msg: str, schema_analysis: dict, error_summary: str = None, error_history: list = None) -> str:
        summary_section = f"\nAI Error Analysis:\n{error_summary}\n" if error_summary else ""
        
        # Format error history if available
        history_section = ""
        if error_history and len(error_history) > 1:
            history_section = "\n\nPREVIOUS FAILED ATTEMPTS:\n"
            # The current error is the last one in error_history list (added in executor.py before calling fix_code)
            # We want to show only the failed attempts BEFORE this one.
            # Usually error_history is [failed1, failed2, current_failed]
            previous_attempts = error_history[:-1]
            # Limit to last 3 previous attempts
            recent_history = previous_attempts[-3:] if len(previous_attempts) > 3 else previous_attempts
            
            for entry in recent_history:
                history_section += f"Attempt {entry['attempt']}: {entry['summary'][:300]}...\n"
            history_section += "\nIMPORTANT: The above fixes DID NOT WORK. Try a DIFFERENT approach.\n"
        
        ml_objective = schema_analysis.get('ml_objective')
        ml_objective_section = ""
        if ml_objective:
            ml_objective_section = f"""
        USER ML OBJECTIVE:
        "{ml_objective}"
        
        CRITICAL: While fixing the code, you MUST ensure it still aims to solve this specific objective.
        """

        prompt = f"""
        You are a Machine Learning Engineer. The following Python code failed to execute. Fix it.
        
        Error Message:
        {error_msg}
        {summary_section}
        {history_section}
        {ml_objective_section}
        
        Original Code:
        {original_code}
        
        Dataset Analysis:
        {schema_analysis.get('analysis', '')}
        
        Raw Schema:
         {schema_analysis.get('schema_context', str(schema_analysis.get('raw_schema', '')))}
        
        tasks:
        1. REASONING: Analyze the Error Message against the 'Raw Schema'. List which column/table was missing and what the correct name should be based ONLY on the schema.
        2. Fix the error by strictly following the 'Raw Schema'.
        3. CRITICAL: Ensure `from sqlalchemy import create_engine` is used for `load_data`.
        4. CRITICAL: USE THIS CONNECTION STRING: {schema_analysis.get('connection_string', '')}
        5. CRITICAL: Only use columns explicitly listed in 'Raw Schema'. 
        6. To JOIN, prioritize 'FOREIGN KEYS'. If not present, use identical column names but VERIFY they exist in both tables.
        7. If you've already tried a join key that failed, DO NOT TRY IT AGAIN. Look for an alternative or just use the main table.
        8. If using Sklearn, convert column names to strings: `X.columns = X.columns.astype(str)`.
        9. Drop any non-numeric columns from features `X` before training.
        10. ENSURE `import sys` is at the very top. Use `sys.exit(1)` on failure.
        11. CRITICAL: Ensure the final JSON report is printed with `print(json.dumps(report))` WITHOUT indent.
            - DO NOT use `json.dumps(report, indent=2)`. The JSON must be on ONE LINE.
        12. Output your reasoning first (as comments), then the full valid Python code.
        """
        
        fixed_code_response = self.llm.generate_response(prompt)
        
        import re
        code_match = re.search(r'```(?:python)?\s*(.*?)```', fixed_code_response, re.DOTALL)
        if code_match:
            return code_match.group(1).strip()
            
        return fixed_code_response.strip()
