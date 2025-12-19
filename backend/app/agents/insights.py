from app.services.llm_service import LLMService

class InsightsAgent:
    def __init__(self, llm_service: LLMService):
        self.llm = llm_service

    def generate_insights(self, execution_report: dict, schema_analysis: dict, model_type: str = "Unknown", ml_objective: str = None) -> str:
        """
        Generates a narrative report based on the execution metrics and schema context.
        """
        ml_objective_section = ""
        if ml_objective:
            ml_objective_section = f"\nUser ML Objective: {ml_objective}\n"

        prompt = f"""
        You are a Data Analyst. Analyze the results of the Machine Learning model execution and provide a business-friendly report.
        
        Selected Model Type: {model_type}
        {ml_objective_section}

        Context (Schema):
        {schema_analysis['analysis']}
        
        Model Performance Results:
        {execution_report}
        
        Write a concise summary covering:
        1. Whether the {model_type} model performed well to achieve the stated objective.
        2. What this means for the data (business implications related to the goal).
        3. Recommendations for next steps, and whether another approach might have been better for this objective.
        """
        
        insights = self.llm.generate_response(prompt)
        return insights
