from app.services.llm_service import LLMService

class InsightsAgent:
    def __init__(self, llm_service: LLMService):
        self.llm = llm_service

    def generate_insights(self, execution_report: dict, schema_analysis: dict) -> str:
        """
        Generates a narrative report based on the execution metrics and schema context.
        """
        prompt = f"""
        You are a Data Analyst. Analyze the results of the Machine Learning model execution and provide a business-friendly report.
        
        Context (Schema):
        {schema_analysis['analysis']}
        
        Model Performance Results:
        {execution_report}
        
        Write a concise summary covering:
        1. Whether the model performed well (interpret the metrics).
        2. What this means for the data (business implications).
        3. Recommendations for next steps.
        """
        
        insights = self.llm.generate_response(prompt)
        return insights
