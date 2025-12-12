from app.services.llm_service import LLMService
import os

class CodeAdaptationAgent:
    def __init__(self, llm_service: LLMService, template_path: str = "../ml_template/base_pipeline.py"):
        self.llm = llm_service
        self.template_path = template_path

    def adapt(self, schema_analysis: dict) -> str:
        # 1. Load Template
        try:
            with open(self.template_path, 'r') as f:
                template_code = f.read()
        except FileNotFoundError:
            # Fallback for when running from backend dir
            with open(os.path.join(os.path.dirname(__file__), "../../../ml_template/base_pipeline.py"), 'r') as f:
                template_code = f.read()

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
        3. IMPORTANT: If using sklearn, ensure X.columns are converted to strings (X.columns = X.columns.astype(str)) to avoid TypeError.
        4. Output the full valid Python code.
        """
        
        fixed_code_response = self.llm.generate_response(prompt)
        
        import re
        code_match = re.search(r'```(?:python)?\s*(.*?)```', fixed_code_response, re.DOTALL)
        if code_match:
            return code_match.group(1).strip()
            
        return fixed_code_response.strip()
