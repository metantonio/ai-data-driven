from app.services.llm_service import LLMService
import os
import sys
import re
from pathlib import Path

class CodeAdaptationAgent:
    def __init__(self, llm_service: LLMService, template_path: str = None):
        self.llm = llm_service
        self.template_path = template_path

    def adapt(self, schema_analysis: dict, algorithm_type: str = "linear_regression", eda_summary: str = None) -> str:
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
            "decision_tree": "decision_tree.py"
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
        
        prompt = f"""
        You are a Machine Learning Engineer. Adapt the following Python ML template to work with the described dataset.
        
        TARGET ALGORITHM TO IMPLEMENT: {algorithm_type.replace('_', ' ').upper()}
        (IMPORTANT: Follow the user's latest selection even if the EDA analysis mentions a different initial choice).

        Dataset Analysis:
        {schema_analysis['analysis']}

        {"EDA Findings & Context:" if eda_summary else ""}
        {eda_summary if eda_summary else ""}

        User Comments (Context):
        {schema_analysis.get('user_comments', 'None provided')}
        
        Raw Schema:
        {schema_analysis['raw_schema']}
        
        Connection String:
        "{connection_string}"
        
        Template Code:
        {template_code}
        
        Tasks:
        1. Implement 'load_data' to connect to the DB using the provided Connection String exactly. Use sqlalchemy. 
           IMPORTANT: 
           - ALWAYS include Primary Key/Foreign Key columns (e.g., 'id', or any linking columns found in the schema) for merging.
           - ALWAYS include ALL columns needed for features (e.g., 'city', 'state', 'type', 'gender') in the SELECT statement.
           - If connection string starts with 'hana://', ensure to use sqlalchemy-hana dialect. 
             Note: 'hdbcli' must be installed.
           - For large datasets in Cloud DBs (Postgres/HANA), consider using 'LIMIT' for initial testing if not specified otherwise.
        2. Implement 'preprocess_data' to handle missing values and encode categoricals based on the schema types. 
           - CRITICAL: DO NOT hallucinate column names. ONLY use columns explicitly listed in the schema provided for each table.
           - IF you need to merge tables, identify the correct keys from the provided schema. DO NOT assume junction columns like 'casino_id' exist unless they are visible in the schema.
           - DO NOT use `df[col] = pd.get_dummies(df[col])`. This will error if there are multiple categories. 
           - INSTEAD: Use `df = pd.get_dummies(df, columns=[col1, col2...])` or a Scikit-Learn `OneHotEncoder`.
           - Avoid deprecated pandas methods: Use `df.ffill()` or `df.bfill()` instead of `df.fillna(method='ffill')`.
           - Check if columns exist before applying operations like 'get_dummies' or 'drop'.
           - If a column is missing, print a warning but do not crash if possible, or fail explicitly with `import sys; sys.exit(1)`.
        3. Select the most likely target column from the schema for 'train_model'.
        4. Ensure the model is saved to 'models/model.joblib' (or unique name) and 'model_path' is in the JSON report.
        5. DO NOT wrap the entire logic in a try-except block that prints a custom message. Allow Python's standard traceback or the template's main try-except to handle errors so the process exits with code 1.
        6. DO NOT print the dataframe to stdout (e.g., no `print(df)`). The ONLY output at the end must be the JSON `report`. Printing large text will break the JSON parsing.
        7. IMPORTANT: For OneHotEncoder, use `sparse_output=False` (scikit-learn >= 1.2) instead of `sparse=False`.
        8. IMPORTANT: If the algorithm is a CLASSIFIER (e.g., LogisticRegression, RandomForestClassifier) but the target column is CONTINUOUS (float/int with many unique values), you MUST convert it to binary/categorical classes in `preprocess_data`. Example: `df['target'] = (df['target'] > 0).astype(int)`. Do not try to predict continuous values with a classifier.
        
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

    def fix_code(self, original_code: str, error_msg: str, schema_analysis: dict, error_summary: str = None) -> str:
        summary_section = f"\nAI Error Analysis:\n{error_summary}\n" if error_summary else ""
        
        prompt = f"""
        You are a Machine Learning Engineer. The following Python code failed to execute. Fix it.
        
        Error Message:
        {error_msg}
        {summary_section}
        
        Original Code:
        {original_code}
        
        Dataset Analysis:
        {schema_analysis.get('analysis', '')}
        
        Raw Schema:
         {schema_analysis.get('raw_schema', '')}
        
        tasks:
        1. Analyze the error, the AI summary (if provided), and the code.
        2. Fix the code to resolve the error. Ensure imports are correct and data types are handled.
        3. IMPORTANT: If using sklearn, ensure X.columns are converted to strings (X.columns = X.columns.astype(str)). 
        4. IMPORTANT: Drop any Datetime/Timestamp columns from X, or convert them to numeric (e.g. .astype(int) / 10**9). Sklearn cannot handle Timestamps.
        5. IF error is related to missing columns/tables: STRICTLY check the 'Raw Schema' provided above and use the exact column names found there.
           - NOTE: 'casinos' table usually has 'id', not 'casino_id'. 'games' table has 'id', not 'game_id'. Check your merge keys carefully.
        6. IF clustering (kmeans/hierarchical), ensure to use the provided 'optimize_clusters' or 'optimize_hierarchical' functions in the template logic instead of hardcoding n_clusters.
        7. IGNORE DeprecationWarnings or FutureWarnings unless they are the direct cause of the crash. Focus on the 'Traceback' and the final 'Exception'.
        8. CRITICAL: DO NOT wrap the code in a `try-except` block that prints an error and continues or exits with 0. Let the script crash with a traceback, or use `traceback.print_exc(); sys.exit(1)` if you must catch it. The system needs a non-zero exit code to know it failed.
        9. IMPORTANT: If the error is regarding 'OneHotEncoder' and 'sparse', replace `sparse=False` with `sparse_output=False`.
        10. IMPORTANT: Avoid the error "Columns must be same length as key" by NOT assigning get_dummies to a single column. Use `df = pd.get_dummies(df, columns=['col_name'])` instead.
        11. IF the error is "Classification metrics can't handle a mix of continuous and binary targets", it means you are using a Classifier on a Regression target. Fix this by converting the target variable `y` to binary (e.g., `y = (y > y.mean()).astype(int)`) or using a Regressor instead.
        11. Output the full valid Python code.
        """
        
        fixed_code_response = self.llm.generate_response(prompt)
        
        import re
        code_match = re.search(r'```(?:python)?\s*(.*?)```', fixed_code_response, re.DOTALL)
        if code_match:
            return code_match.group(1).strip()
            
        return fixed_code_response.strip()
