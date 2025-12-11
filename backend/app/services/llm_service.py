class LLMService:
    def __init__(self, api_key: str = "mock"):
        self.api_key = api_key

    def generate_response(self, prompt: str) -> str:
        """
        Mock LLM response generator. 
        In a real scenario, this would call OpenAI/Gemini API.
        """
        print(f"[LLM Prompt]: {prompt[:100]}...")
        
        # Simple heuristic response for demonstration
        if "analyze the following database schema" in prompt.lower():
            return "The database contains user data and activity logs. The 'users' table is the central entity."
        
        if "adapt the following python code" in prompt.lower():
            return "# Adapted code would go here\nprint('Hello from adapted code')"
            
        return "I am a mock AI agent."
