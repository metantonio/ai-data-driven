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

    def chat_with_insights(self, query: str, history: list, execution_report: dict, model_type: str) -> str:
        """
        Handles a conversational follow-up query using the provided history.
        """
        history_str = ""
        for msg in history[-5:]: # Keep last 5 messages for context
            role = "User" if msg['role'] == 'user' else "AI"
            history_str += f"{role}: {msg['content']}\n"

        prompt = f"""
        You are a Data Analyst expert. You are having a conversation with a user about a Machine Learning model execution.
        
        Model Type: {model_type}
        Execution Results: {execution_report}
        
        Conversation History:
        {history_str}
        
        User's latest question: {query}
        
        Provide a helpful and technical but understandable response based on the model results. 
        If they ask for something not in the report, politely explain that you only have access to these specific results.
        """
        return self.llm.generate_response(prompt)
