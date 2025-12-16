
import pandas as pd
from langchain_ollama import ChatOllama
from ai_data_science_team.ds_agents import EDAToolsAgent
import os
import json
from app.services.db_inspector import DatabaseInspector

class EDAService:
    def __init__(self, model_name: str = None, api_key: str = None, base_url: str = None):
        """
        Initialize EDA Service with LLM configuration.
        Supports both Ollama (local) and OpenAI-compatible endpoints.
        """
        # Get LLM configuration from environment
        llm_provider = os.getenv("LLM_PROVIDER", "ollama")
        llm_model = model_name or os.getenv("LLM_MODEL", "qwen2.5-coder:7b")
        llm_url = base_url or os.getenv("LLM_API_URL", "http://localhost:11434")
        
        # Configure LLM based on provider
        if llm_provider == "ollama" or "11434" in llm_url:
            # Use ChatOllama for Ollama endpoints (with tool calling support)
            # Extract base URL without /api/generate if present
            if "/api/generate" in llm_url:
                llm_url = llm_url.replace("/api/generate", "")
            
            self.llm = ChatOllama(
                model=llm_model,
                base_url=llm_url,
                temperature=0.1
            )
        else:
            # Use ChatOpenAI for OpenAI-compatible endpoints (vLLM, etc.)
            from langchain_openai import ChatOpenAI
            self.llm = ChatOpenAI(
                model=llm_model,
                api_key=api_key if api_key else os.getenv("OPENAI_API_KEY", "dummy-key"),
                base_url=llm_url,
                temperature=0.1
            )
        
    def process_query(self, question: str, data: pd.DataFrame):
        """
        Invokes the EDA Agent with the question and data.
        Returns a dictionary with message, tool calls, and artifacts.
        """
        try:
            # Initialize Agent
            eda_agent = EDAToolsAgent(
                self.llm,
                invoke_react_agent_kwargs={"recursion_limit": 10},
            )
            
            # Enforce no hyperlinks instruction to avoid hallucinations
            instruction = question + " Don't return hyperlinks to files in the response."
            
            print(f"[EDA] Processing query: {question}")
            print(f"[EDA] Data shape: {data.shape}")
            
            # Invoke Agent
            result = eda_agent.invoke_agent(
                user_instructions=instruction,
                data_raw=data
            )
            
            print(f"[EDA] Agent invocation result: {result}")
            
            # Extract results
            tool_calls = eda_agent.get_tool_calls()
            ai_message = eda_agent.get_ai_message(markdown=False)
            artifacts = eda_agent.get_artifacts(as_dataframe=False)
            
            print(f"[EDA] Tool calls: {tool_calls}")
            print(f"[EDA] AI message: {ai_message[:200] if ai_message else 'None'}...")
            print(f"[EDA] Artifacts keys: {list(artifacts.keys()) if isinstance(artifacts, dict) else type(artifacts)}")
            
            # Process Artifacts for Serialization
            processed_artifacts = artifacts
            if isinstance(artifacts, dict):
                 # Ensure deep serialization if necessary, but returning as is for now
                 # FastAPI will handle dict -> JSON conversion if types are standard
                 pass

            return {
                "ai_message": ai_message,
                "tool_calls": tool_calls,
                "artifacts": processed_artifacts
            }
        except Exception as e:
            print(f"[EDA] Error processing query: {str(e)}")
            import traceback
            traceback.print_exc()
            raise

    @staticmethod
    def load_data_from_db(connection_string: str, query: str = None, limit: int = 1000) -> pd.DataFrame:
        """
        Helper to load data from DB into DataFrame.
        If query is not provided, it tries to load a sample from the first table found (risky but demo-friendly).
        """
        from sqlalchemy import create_engine, inspect
        engine = create_engine(connection_string)
        
        if query:
            return pd.read_sql(query, engine)
        
        # Auto-discovery
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        if not tables:
            raise ValueError("No tables found in database.")
        
        # Just pick first table
        table = tables[0]
        # Sanitize table name? usually safe from inspector
        return pd.read_sql(f"SELECT * FROM {table} LIMIT {limit}", engine)
