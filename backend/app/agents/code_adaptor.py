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
        prompt = f"""
        You are a Machine Learning Engineer. Adapt the following Python ML template to work with the described dataset.
        
        Dataset Analysis:
        {schema_analysis['analysis']}
        
        Raw Schema:
        {schema_analysis['raw_schema']}
        
        Template Code:
        {template_code}
        
        Tasks:
        1. Implement 'load_data' to connect to the DB and fetch data using SQL (use sqlalchemy or pandas).
        2. Implement 'preprocess_data' to handle missing values and encode categoricals based on the schema types.
        3. Select the most likely target column from the schema for 'train_model'.
        
        Output the full valid Python code.
        """
        
        adapted_code = self.llm.generate_response(prompt)
        
        return adapted_code
