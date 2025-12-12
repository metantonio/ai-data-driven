from app.services.llm_service import LLMService
import os

class CodeAdaptationAgent:
    def __init__(self, llm_service: LLMService, template_path: str = None):
        self.llm = llm_service
        self.template_path = template_path

    def adapt(self, schema_analysis: dict, algorithm_type: str = "linear_regression") -> str:
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
            "association_rules": "association_rules.py"
        }
        
        filename = template_map.get(algorithm_type, "linear_regression.py")
        
        # Load Template
        try:
            # Try specific path if set, else look in standard locations with filename
            if self.template_path:
                path = self.template_path
            else:
                # Default relative lookups
                path = f"../ml_template/{filename}"
                
            with open(path, 'r') as f:
                template_code = f.read()
        except FileNotFoundError:
            # Fallback relative to this file
            import os
            base_dir = os.path.dirname(__file__)
            path = os.path.join(base_dir, f"../../../ml_template/{filename}")
            try:
                with open(path, 'r') as f:
                    template_code = f.read()
            except FileNotFoundError:
                return f"# Error: Could not find template for {algorithm_type} at {path}"

        # 2. Prompt LLM to fill placeholders
        connection_string = schema_analysis.get('connection_string', 'sqlite:///../example.db')
        
        prompt = f"""
        You are a Machine Learning Engineer. Adapt the following Python ML template to work with the described dataset.
        
        Dataset Analysis:
        {schema_analysis['analysis']}
        
        Raw Schema:
        {schema_analysis['raw_schema']}
        
        Connection String:
        "{connection_string}"
        
        Template Code:
        {template_code}
        
        Tasks:
        1. Implement 'load_data' to connect to the DB using the provided Connection String exactly. Use sqlalchemy.
        2. Implement 'preprocess_data' to handle missing values and encode categoricals based on the schema types.
        3. Select the most likely target column from the schema for 'train_model'.
        
        Output the full valid Python code.
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

    def fix_code(self, original_code: str, error_msg: str, schema_analysis: dict) -> str:
        prompt = f"""
        You are a Machine Learning Engineer. The following Python code failed to execute. Fix it.
        
        Error Message:
        {error_msg}
        
        Original Code:
        {original_code}
        
        Dataset Analysis:
        {schema_analysis.get('analysis', '')}
        
        Raw Schema:
        {schema_analysis.get('raw_schema', '')}
        
        tasks:
        1. Analyze the error and the code.
        2. Fix the code to resolve the error. Ensure imports are correct and data types are handled.
        3. IMPORTANT: If using sklearn, ensure X.columns are converted to strings (X.columns = X.columns.astype(str)). 
        4. IMPORTANT: Drop any Datetime/Timestamp columns from X, or convert them to numeric (e.g. .astype(int) / 10**9). Sklearn cannot handle Timestamps.
        5. IF error is related to missing columns/tables: STRICTLY check the 'Raw Schema' provided above and use the exact column names found there.
        6. IF clustering (kmeans/hierarchical), ensure to use the provided 'optimize_clusters' or 'optimize_hierarchical' functions in the template logic instead of hardcoding n_clusters.
        7. Output the full valid Python code.
        """
        
        fixed_code_response = self.llm.generate_response(prompt)
        
        import re
        code_match = re.search(r'```(?:python)?\s*(.*?)```', fixed_code_response, re.DOTALL)
        if code_match:
            return code_match.group(1).strip()
            
        return fixed_code_response.strip()
