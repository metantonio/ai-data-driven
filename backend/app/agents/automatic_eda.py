import pandas as pd
import numpy as np
import json
import asyncio
from typing import AsyncGenerator, Dict, Any, List
from sqlalchemy import create_engine, inspect as sql_inspect
from app.services.llm_service import LLMService
from app.services.simple_eda_service import SimpleEDAService

class AutomaticEDAAgent:
    def __init__(self, llm_service: LLMService):
        self.llm = llm_service
        self.eda_service = SimpleEDAService()

    async def run_analysis(self, connection_string: str, user_comments: Dict[str, Any], algorithm_type: str, ml_objective: str = None) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Runs a comprehensive EDA and yields progress updates.
        """
        try:
            yield {"status": "info", "message": "Initializing AI EDA Agent...", "data": None}
            
            # Insight accumulation
            insights_summary = []
            yield {"status": "info", "message": "Loading data for analysis...", "data": None}
            
            # Resolve connection string early for both loading methods
            from app.services.db_inspector import DatabaseInspector
            resolved_connection_string = DatabaseInspector.resolve_connection_string(connection_string)
            
            if ml_objective:
                yield {"status": "info", "message": "Crafting custom SQL query for your objective...", "data": None}
                # Get schema context for SQL generation
                inspector = DatabaseInspector(resolved_connection_string)
                schema_summary = inspector.get_schema_summary()
                
                sql_prompt = f"""
                You are a SQL expert. Based on the following database schema and the user's Machine Learning objective, generate a single SQL SELECT query that joins necessary tables and selects relevant columns to build a dataset for this model.
                
                OBJECTIVE: {ml_objective}
                ALGORITHM: {algorithm_type}
                USER CONTEXT: {json.dumps(user_comments)}
                SCHEMA: {json.dumps(schema_summary)}
                
                RULES:
                1. Output ONLY the SQL query. No explanations.
                2. Use the correct dialect for this connection: {resolved_connection_string}
                3. JOIN tables if necessary to fulfill the objective.
                4. Limit the result to 2000 rows for EDA performance.
                5. If you cannot fulfill the objective with the given schema, return a generic "SELECT * FROM [main_table] LIMIT 2000" and explain why.
                """
                try:
                    query = self.llm.generate_response(sql_prompt).strip()
                    # Clean markdown if present
                    if "```sql" in query:
                        query = query.split("```sql")[1].split("```")[0].strip()
                    elif "```" in query:
                        query = query.split("```")[1].split("```")[0].strip()
                    
                    df = pd.read_sql(query, create_engine(resolved_connection_string))
                    yield {"status": "info", "message": f"Custom dataset loaded via objective-driven SQL.", "data": {"query": query}}
                    insights_summary.append(f"Custom Dataset Query:\n```sql\n{query}\n```")
                except Exception as e:
                    yield {"status": "info", "message": f"Failed to generate custom SQL, falling back to default loading.", "data": {"error": str(e)}}
                    df = self._load_data(resolved_connection_string)
            else:
                df = self._load_data(resolved_connection_string)

            if df.empty:
                yield {"status": "error", "message": "No data found for analysis.", "data": None}
                return

            yield {"status": "info", "message": f"Data loaded: {df.shape[0]} rows, {df.shape[1]} columns.", "data": {"shape": df.shape}}

            # 2. General Statistics & "Self-Questions"
            yield {"status": "step", "message": "Phase 1: General Data Statistics", "data": {"phase": "statistics"}}
            stats = self.eda_service._describe_dataset(df)
            
            question_prompt = f"""
            Based on these statistics: {json.dumps(stats['artifacts']['describe_df'][:5])}
            And the target algorithm: {algorithm_type}
            {"And the ML Objective: " + ml_objective if ml_objective else ""}
            
            What are 2 critical questions you should ask yourself about the data quality for this task?
            Respond only with the 2 questions, one per line.
            """
            try:
                questions_raw = self.llm.generate_response(question_prompt).strip()
                questions = [q for q in questions_raw.split('\n') if q.strip()][:2]
            except Exception as e:
                print(f"LLM Error in Phase 1: {e}")
                questions = ["What is the primary key and its distribution?", "Are there any obvious outliers in the features?"]
            
            if not questions:
                questions = ["What is the primary key and its distribution?", "Are there any obvious outliers in the features?"]
            
            yield {
                "status": "thought", 
                "message": "AI self-questioning...", 
                "data": {"thought": questions, "results": stats['ai_message']}
            }
            insights_summary.append(f"Phase 1 - Data Quality Questions:\n" + "\n".join([f"- {q}" for q in questions]))
            await asyncio.sleep(1) # Visual pacing

            # 3. Missing Data Analysis
            yield {"status": "step", "message": "Phase 2: Missing Data Patterns", "data": {"phase": "missing_data"}}
            missing = self.eda_service._analyze_missing_data(df)
            
            insight_prompt = f"""
            Missing Data Report: {missing['ai_message']}
            Algorithm: {algorithm_type}
            {"Objective: " + ml_objective if ml_objective else ""}
            
            As an AI Agent, what is your insight about how missing data affects the proposed {algorithm_type} model?
            Keep it very concise.
            """
            try:
                insight = self.llm.generate_response(insight_prompt).strip()
            except Exception as e:
                print(f"LLM Error in Phase 2: {e}")
                insight = "Missing data might introduce bias. Consider imputation or removal of rows."
                
            if not insight:
                insight = "Missing data might introduce bias. Consider imputation or removal of rows."

            yield {
                "status": "thought", 
                "message": "Analyzing data gaps...", 
                "data": {"thought": [insight], "results": missing['ai_message'], "visualization": missing['artifacts'].get('bar_plot')}
            }
            insights_summary.append(f"Phase 2 - Missing Data Insights:\n- {insight}")
            await asyncio.sleep(1)

            # 4. Correlation Analysis
            yield {"status": "step", "message": "Phase 3: Correlation & Feature Relationships", "data": {"phase": "correlation"}}
            corrs = self.eda_service._analyze_correlations(df)
            
            corr_thought_prompt = f"""
            Correlation Summary: {corrs['ai_message']}
            Algorithm: {algorithm_type}
            {"Objective: " + ml_objective if ml_objective else ""}
            
            What features seem most promising or problematic for {algorithm_type}?
            """
            try:
                corr_thought = self.llm.generate_response(corr_thought_prompt).strip()
            except Exception as e:
                print(f"LLM Error in Phase 3: {e}")
                corr_thought = "Standard correlation analysis shows some relationship between numeric variables."

            if not corr_thought:
                corr_thought = "Standard correlation analysis shows some relationship between numeric variables."

            yield {
                "status": "thought", 
                "message": "Mapping feature relationships...", 
                "data": {"thought": [corr_thought], "results": corrs['ai_message'], "visualization": corrs['artifacts'].get('heatmap_plot')}
            }
            insights_summary.append(f"Phase 3 - Correlation Insights:\n- {corr_thought}")
            await asyncio.sleep(1)

            # 5. Suggested Models
            yield {"status": "step", "message": "Phase 4: Optimization Suggestions", "data": {"phase": "suggestions"}}
            
            available_models = [
                "linear_regression", "logistic_regression", "kmeans", "hierarchical", 
                "time_series", "linear_programming", "mixed_integer_programming", 
                "reinforcement_learning", "association_rules", "random_forest", "decision_tree"
            ]

            suggestion_prompt = f"""
            You have analyzed the data. 
            User current choice: {algorithm_type}
            User context: {json.dumps(user_comments)}
            {"User goal: " + ml_objective if ml_objective else ""}
            
            Available ML models in our system: {', '.join(available_models)}
 
            Based on your EDA findings and the user objective, suggest 2 other models from the 'Available ML models' list that might work better or complement the current choice.
            
            Return a JSON list of objects: 
            [
              {{
                "name": "Model technical name (must be one from the available list)", 
                "display_name": "Human readable name",
                "reason": "Why this model specifically given the data and objective?"
              }}
            ]
            """
            try:
                suggestions_raw = self.llm.generate_response(suggestion_prompt)
                if "```json" in suggestions_raw:
                    suggestions_raw = suggestions_raw.split("```json")[1].split("```")[0].strip()
                elif "```" in suggestions_raw:
                    suggestions_raw = suggestions_raw.split("```")[1].split("```")[0].strip()
                
                suggestions = json.loads(suggestions_raw)
                # Ensure s is a dict and has 'name' in available_models
                suggestions = [s for s in suggestions if isinstance(s, dict) and s.get('name') in available_models]
                if not suggestions:
                    raise ValueError("No valid suggestions in available models.")
            except:
                suggestions = [
                    {"name": "random_forest", "display_name": "Random Forest", "reason": "Good baseline for most datasets"}, 
                    {"name": "decision_tree", "display_name": "Decision Tree", "reason": "Explainable model for tabular data"}
                ]

            yield {
                "status": "success", 
                "message": "Automatic EDA Complete!", 
                "data": {
                    "suggestions": suggestions,
                    "eda_summary": "\n\n".join(insights_summary)
                }
            }

        except Exception as e:
            import traceback
            traceback.print_exc()
            yield {"status": "error", "message": f"AI Agent Analysis failed: {str(e)}", "data": None}

    def _load_data(self, connection_string: str) -> pd.DataFrame:
        engine = create_engine(connection_string)
        inspector = sql_inspect(engine)
        tables = inspector.get_table_names()
        if not tables:
            return pd.DataFrame()
        
        # Load a sample (1000 rows max) from the first table for EDA
        table = tables[0]
        return pd.read_sql(f"SELECT * FROM {table} LIMIT 1000", engine)
