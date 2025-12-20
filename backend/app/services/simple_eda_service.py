
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64
from typing import Dict, Any, List
import json
from .llm_service import LLMService


class SimpleEDAService:
    """
    Simplified EDA service that performs common exploratory data analysis tasks
    without requiring complex LLM tool calling.
    """
    
    def __init__(self):
        # Set seaborn style
        sns.set_style("darkgrid")
        
        # Initialize Ollama API settings for context interpretation (optional)
        import os
        """ self.ollama_url = os.getenv("LLM_API_URL", "http://localhost:11434")
        self.ollama_model = os.getenv("LLM_MODEL", "qwen2.5-coder:7b")
        self.use_llm = os.getenv("LLM_PROVIDER", "ollama") == "ollama" """
        self.llm = LLMService()
        self.use_llm = self.llm.provider != "mock"
    
    def _call_llm(self, prompt: str) -> str:
        """
        Call the configured LLM via LLMService.
        """
        try:
            print(f"[EDA] Calling LLMService with prompt length {len(prompt)}")
            response = self.llm.generate_response(prompt)
            print(f"[EDA] LLM response length: {len(response)}")
            return response.strip()
        except Exception as e:
            print(f"[EDA] LLM error: {type(e).__name__}: {e}")
            return ""
    
    def _call_ollama(self, prompt: str) -> str:
        """
        Call Ollama API directly without langchain.
        """
        import requests
        
        try:
            print(f"[EDA] Calling Ollama at {self.ollama_url} with model {self.ollama_model}")
            print(f"[EDA] Prompt length: {len(prompt)} characters")
            
            response = requests.post(
                f"{self.ollama_url}",
                json={
                    "model": self.ollama_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1
                    }
                },
                timeout=30
            )
            
            print(f"[EDA] Ollama response status: {response.status_code}")
            response.raise_for_status()
            
            result = response.json()
            generated_text = result.get("response", "").strip()
            
            print(f"[EDA] Generated response length: {len(generated_text)} characters")
            print(f"[EDA] Generated response preview: {generated_text[:200]}...")
            
            return generated_text
            
        except requests.exceptions.ConnectionError as e:
            print(f"[EDA] Connection error to Ollama: {e}")
            print(f"[EDA] Make sure Ollama is running at {self.ollama_url}")
            return ""
        except requests.exceptions.Timeout as e:
            print(f"[EDA] Timeout calling Ollama: {e}")
            return ""
        except requests.exceptions.HTTPError as e:
            print(f"[EDA] HTTP error from Ollama: {e}")
            print(f"[EDA] Response content: {e.response.text if hasattr(e, 'response') else 'N/A'}")
            return ""
        except Exception as e:
            print(f"[EDA] Unexpected error calling Ollama: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return ""
    
    def _interpret_question_with_context(self, question: str) -> str:
        """
        Use Ollama to interpret question with context and extract the actual intent.
        Falls back to original question if Ollama is not available.
        """
        if not self.use_llm or not question.startswith("Context:"):
            return question
        
        prompt = f"""You are helping interpret a user's follow-up question in a data analysis conversation.

{question}

Extract ONLY the actual data analysis task the user wants to perform. Respond with a single clear question or command that can be used for EDA analysis.

Examples:
- If user asks "Why is this correlation high?", respond: "explain correlation"
- If user asks "Show me more details", respond: "show more details about the data"
- If user asks "What about missing values?", respond: "analyze missing data"

Respond with just the interpreted question, nothing else."""

        interpreted = self._call_llm(prompt)
        
        if interpreted:
            print(f"[EDA] Interpreted question: {interpreted}")
            return interpreted
        
        # Fallback: extract the part after "Now the user asks:"
        if "Now the user asks:" in question:
            return question.split("Now the user asks:")[-1].strip()
        return question

    def generate_sql_with_retry(self, connection_string: str, question: str) -> Dict[str, Any]:
        """
        Generate SQL query, execute it, and retry on error (max 3 times).
        """
        import pandas as pd
        from sqlalchemy import create_engine
        
        # 1. Get Schema Context
        schema_context = self._get_schema_info(connection_string)
        
        history = []
        max_retries = 3
        last_error = None
        current_sql = ""
        
        # We try initial attempt + max_retries
        for attempt in range(max_retries + 1):
            # Generate SQL
            prompt = self._build_sql_prompt(question, schema_context, connection_string, history)
            current_sql = self._call_llm(prompt)
            
            # Clean SQL
            current_sql = current_sql.replace("```sql", "").replace("```", "").strip()
            
            # Basic validation
            if not current_sql:
                continue
                
            try:
                print(f"[EDA] Executing SQL Attempt {attempt+1}: {current_sql}")
                # Execute
                engine = create_engine(connection_string)
                
                # Safety check for destructive operations if possible, but for now rely on prompt/user
                if any(keyword in current_sql.upper() for keyword in ["DROP ", "DELETE ", "UPDATE ", "INSERT ", "ALTER ", "TRUNCATE "]):
                     raise ValueError("Destructive queries (DROP, DELETE, UPDATE, etc.) are not allowed.")

                df = pd.read_sql(current_sql, engine)
                
                # Success!
                history.append({
                    "attempt": attempt + 1,
                    "sql": current_sql,
                    "status": "success",
                    "error": None
                })
                
                # Return result
                message = f"## SQL Analysis Successful\n\n**Query executed:**\n```sql\n{current_sql}\n```\n\nResult has {len(df)} rows."
                
                artifacts = {
                    'describe_df': df.head(100).to_dict('records'), # Limit for UI display
                    'sql_history': history,
                    'executed_sql': current_sql
                }
                
                # Call Visualization Agent
                try:
                    viz_result = self._decide_and_generate_visualization(df, question)
                    if viz_result:
                        if 'plotly' in viz_result:
                            artifacts['plotly'] = viz_result['plotly']
                            artifacts['title'] = viz_result['title']
                        else:
                            artifacts['generated_plot'] = viz_result['plot']
                            
                        message += f"\n\n📊 **Visualization generated:** {viz_result['title']}"
                except Exception as e:
                    print(f"Visualization agent failed: {e}")
                
                return {
                    'ai_message': message,
                    'tool_calls': ['generate_sql_with_retry'],
                    'artifacts': artifacts
                }
                
            except Exception as e:
                # Failure
                last_error = str(e)
                print(f"[EDA] SQL Attempt {attempt + 1} failed: {last_error}")
                history.append({
                    "attempt": attempt + 1,
                    "sql": current_sql,
                    "status": "error",
                    "error": last_error
                })
        
        # If we get here, all retries failed
        message = f"❌ **Failed to generate valid SQL after {max_retries + 1} attempts.**\n\n**Last error:** {last_error}\n\n**Final Query Attempt:**\n```sql\n{current_sql}\n```"
        return {
            'ai_message': message,
            'tool_calls': ['generate_sql_with_retry'],
            'artifacts': {'sql_history': history}
        }

    def _get_schema_info(self, connection_string: str) -> str:
        """
        Introspect database to get schema info for the LLM.
        """
        from sqlalchemy import create_engine, inspect
        try:
            engine = create_engine(connection_string)
            inspector = inspect(engine)
            
            schema_info = []
            for table_name in inspector.get_table_names():
                try:
                    columns = inspector.get_columns(table_name)
                    cols_desc = ", ".join([f"{col['name']} ({str(col['type'])})" for col in columns])
                    schema_info.append(f"Table: {table_name}\nColumns: {cols_desc}")
                except Exception as e:
                    schema_info.append(f"Table: {table_name} (Error reading columns: {e})")
            
            return "\\n\\n".join(schema_info)
        except Exception as e:
            return f"Error retrieving schema: {str(e)}"

    def _build_sql_prompt(self, question: str, schema_context: str, connection_string: str, history: List[Dict]) -> str:
        """
        Build prompt for SQL generation with history context.
        """
        dialect = "SQLite" # Default
        if "postgresql" in connection_string: dialect = "PostgreSQL"
        elif "mysql" in connection_string: dialect = "MySQL"
        elif "oracle" in connection_string: dialect = "Oracle"
        elif "mssql" in connection_string: dialect = "SQL Server"
        
        prompt = f"""You are an expert SQL Data Analyst. Your task is to generate a valid {dialect} SQL query to answer the user's question.
        
Database Schema:
{schema_context}

User Question: {question}

"""
        if history:
            prompt += "\nPrevious Attempts and Errors (Fix these errors):\n"
            for item in history:
                if item['status'] == 'error':
                    prompt += f"- Attempt {item['attempt']}:\n  Query: {item['sql']}\n  Error: {item['error']}\n"
            prompt += "\nPlease fix the errors from the previous attempts and provide a corrected query.\n"
            
        prompt += """
Return ONLY the SQL query. Do not include markdown code blocks (```sql), explanations, or any other text. Start the response directly with the SQL query.
Important:
- Use only read-only `SELECT` queries.
- Limit results to 100 rows if checking samples, unless aggregation is requested.
"""
        return prompt

    def _decide_and_generate_visualization(self, df: pd.DataFrame, question: str) -> Dict[str, Any]:
        """
        Visualization Agent: Decides if a plot is needed and generates it.
        """
        if df.empty or len(df) < 2:
            return None
            
        import json
        
        # 1. Ask LLM what to plot
        prompt = self._build_visualization_prompt(df, question)
        response = self._call_llm(prompt)
        
        try:
            # Clean response to get JSON
            json_str = response.replace("```json", "").replace("```", "").strip()
            # Find JSON object start/end if extra text exists
            if "{" in json_str:
                json_str = json_str[json_str.find("{"):json_str.rfind("}")+1]
                
            viz_plan = json.loads(json_str)
            
            if not viz_plan.get("visualize", False):
                return None
                
            print(f"[EDA] Visualization Agent planned: {viz_plan}")
            
            # 2. Generate Plotly Data
            plotly_data = self._generate_plotly_from_plan(df, viz_plan)
            if plotly_data:
                return {
                    "plotly": plotly_data,
                    "title": viz_plan.get("title")
                }
            
            # Fallback to Matplotlib if Plotly fails or isn't requested
            return self._generate_plot_from_plan(df, viz_plan)
            
        except Exception as e:
            print(f"[EDA] Visualization decision failed: {e}")
            return None

    def _generate_plotly_from_plan(self, df: pd.DataFrame, plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate Plotly JSON representation from a visualization plan.
        """
        try:
            chart_type = plan.get("type")
            x = plan.get("x")
            y = plan.get("y")
            hue = plan.get("hue") if plan.get("hue") in df.columns else None
            title = plan.get("title", f"{chart_type.title()} Plot")

            data = []
            if chart_type == 'pie':
                data = [{
                    "values": df[y].tolist() if y else [1]*len(df),
                    "labels": df[x].tolist() if x else None,
                    "type": "pie",
                    "hole": .4
                }]
            elif chart_type == 'bar':
                if hue:
                    for val in df[hue].unique():
                        sub = df[df[hue] == val]
                        data.append({
                            "x": sub[x].tolist(),
                            "y": sub[y].tolist(),
                            "name": str(val),
                            "type": "bar"
                        })
                else:
                    data = [{
                        "x": df[x].tolist(),
                        "y": df[y].tolist(),
                        "type": "bar",
                        "marker": {"color": "#22d3ee"}
                    }]
            elif chart_type == 'line':
                if hue:
                    for val in df[hue].unique():
                        sub = df[df[hue] == val]
                        data.append({
                            "x": sub[x].tolist(),
                            "y": sub[y].tolist(),
                            "name": str(val),
                            "type": "scatter",
                            "mode": "lines+markers"
                        })
                else:
                    data = [{
                        "x": df[x].tolist(),
                        "y": df[y].tolist(),
                        "type": "scatter",
                        "mode": "lines+markers",
                        "line": {"color": "#22d3ee"}
                    }]
            elif chart_type == 'scatter':
                if hue:
                    for val in df[hue].unique():
                        sub = df[df[hue] == val]
                        data.append({
                            "x": sub[x].tolist(),
                            "y": sub[y].tolist(),
                            "name": str(val),
                            "type": "scatter",
                            "mode": "markers"
                        })
                else:
                    data = [{
                        "x": df[x].tolist(),
                        "y": df[y].tolist(),
                        "type": "scatter",
                        "mode": "markers",
                        "marker": {"color": "#22d3ee", "size": 10}
                    }]
            elif chart_type == 'histogram':
                data = [{
                    "x": df[x].tolist(),
                    "type": "histogram",
                    "marker": {"color": "#22d3ee"}
                }]
            elif chart_type == 'box':
                data = [{
                    "y": df[y].tolist(),
                    "x": df[x].tolist() if x else None,
                    "type": "box",
                    "marker": {"color": "#22d3ee"}
                }]

            layout = {
                "title": title,
                "paper_bgcolor": "rgba(15, 23, 42, 0.5)",
                "plot_bgcolor": "rgba(15, 23, 42, 0.5)",
                "font": {"color": "#cbd5e1"},
                "xaxis": {"gridcolor": "#334155", "zerolinecolor": "#334155"},
                "yaxis": {"gridcolor": "#334155", "zerolinecolor": "#334155"},
                "margin": {"t": 40, "b": 40, "l": 40, "r": 40}
            }

            return {"data": data, "layout": layout}
        except Exception as e:
            print(f"[EDA] Plotly generation failed: {e}")
            return None

    def _build_visualization_prompt(self, df: pd.DataFrame, question: str) -> str:
        columns = list(df.columns)
        dtypes = {col: str(df[col].dtype) for col in df.columns}
        sample = df.head(3).to_dict('records')
        
        prompt = f"""You are a Data Visualization Expert.
User Question: "{question}"
Data Result Columns: {columns}
Data Types: {dtypes}
Sample Data: {sample}

Decide if a visualization is appropriate to augment the table data.
If yes, choose the BEST chart type from: 'bar', 'line', 'scatter', 'pie', 'histogram', 'box'.

Return a JSON object ONLY (no markdown):
{{
  "visualize": true/false,
  "type": "chart_type",
  "x": "column_for_x_axis",
  "y": "column_for_y_axis",
  "hue": "optional_column_for_color_grouping",
  "title": "Chart Title",
  "reason": "Why this chart?"
}}
"""
        return prompt

    def _generate_plot_from_plan(self, df: pd.DataFrame, plan: Dict[str, Any]) -> Dict[str, Any]:
        import matplotlib.pyplot as plt
        import seaborn as sns
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        try:
            chart_type = plan.get("type")
            x = plan.get("x")
            y = plan.get("y")
            hue = plan.get("hue") if plan.get("hue") in df.columns else None
            
            if chart_type == 'bar':
                sns.barplot(data=df, x=x, y=y, hue=hue, ax=ax, palette='viridis')
            elif chart_type == 'line':
                sns.lineplot(data=df, x=x, y=y, hue=hue, ax=ax)
            elif chart_type == 'scatter':
                sns.scatterplot(data=df, x=x, y=y, hue=hue, ax=ax)
            elif chart_type == 'histogram':
                sns.histplot(data=df, x=x, hue=hue, ax=ax, kde=True)
            elif chart_type == 'box':
                sns.boxplot(data=df, x=x, y=y, hue=hue, ax=ax)
            elif chart_type == 'pie':
                if y and x:
                    plt.pie(df[y], labels=df[x], autopct='%1.1f%%')
                else:
                    return None
            else:
                return None
                
            ax.set_title(plan.get("title", f"{chart_type.title()} Plot"))
            ax.set_facecolor('#0f172a')
            fig.patch.set_facecolor('#0f172a')
            
            # Styling
            ax.tick_params(colors='#cbd5e1')
            ax.xaxis.label.set_color('#cbd5e1')
            ax.yaxis.label.set_color('#cbd5e1')
            ax.title.set_color('#22d3ee')
            if ax.get_legend():
                plt.setp(ax.get_legend().get_texts(), color='#cbd5e1')
                
            plt.tight_layout()
            
            img = self._fig_to_base64(fig)
            plt.close(fig)
            
            return {
                "plot": img,
                "title": plan.get("title")
            }
            
        except Exception as e:
            print(f"[EDA] Plot generation failed: {e}")
            plt.close(fig)
            return None
    
    def show_available_tables(self, connection_string: str) -> Dict[str, Any]:
        """
        Show all available tables in the database.
        """
        from sqlalchemy import create_engine, inspect as sql_inspect
        
        try:
            engine = create_engine(connection_string)
            inspector = sql_inspect(engine)
            tables = inspector.get_table_names()
            
            if not tables:
                message = "⚠️ **No tables found in the database.**"
                return {
                    'ai_message': message,
                    'tool_calls': ['show_tables'],
                    'artifacts': {}
                }
            
            message = f"""## Available Tables

**Total Tables:** {len(tables)}

**Table List:**
"""
            
            table_info = []
            for table in tables:
                # Get row count for each table
                try:
                    from sqlalchemy import text
                    with engine.connect() as conn:
                        result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                        row_count = result.scalar()
                    message += f"\n- **{table}** ({row_count:,} rows)"
                    table_info.append({
                        'Table': table,
                        'Rows': f"{row_count:,}"
                    })
                except Exception as e:
                    message += f"\n- **{table}**"
                    table_info.append({
                        'Table': table,
                        'Rows': 'N/A'
                    })
            
            artifacts = {
                'describe_df': table_info
            }
            
            return {
                'ai_message': message,
                'tool_calls': ['show_tables'],
                'artifacts': artifacts
            }
            
        except Exception as e:
            return {
                'ai_message': f"❌ **Error connecting to database:** {str(e)}",
                'tool_calls': ['show_tables'],
                'artifacts': {}
            }
        
    def analyze_dataset(self, df: pd.DataFrame, query: str) -> Dict[str, Any]:
        """
        Analyze dataset based on user query.
        Returns structured response with message and artifacts.
        """
        query_lower = query.lower()
        result = None
        
        # Determine what analysis to perform based on query
        if any(word in query_lower for word in ['describe', 'summary', 'overview', 'info']):
            result = self._describe_dataset(df)
        elif any(word in query_lower for word in ['missing', 'null', 'nan']):
            result = self._analyze_missing_data(df)
        elif any(word in query_lower for word in ['correlation', 'correlate']):
            result = self._analyze_correlations(df)
        elif any(word in query_lower for word in ['distribution', 'histogram', 'hist']):
            result = self._analyze_distributions(df)
        elif any(word in query_lower for word in ['first', 'head', 'sample', 'rows']) and not 'all' in query_lower:
            result = self._show_sample(df, query)
        elif any(word in query_lower for word in ['all', 'entire', 'full', 'complete']) and any(word in query_lower for word in ['data', 'rows', 'dataset']):
            result = self._show_all_data(df)
        elif any(word in query_lower for word in ['column', 'columns', 'field', 'fields', 'dtypes', 'types']):
            result = self._show_column_info(df)
        elif any(word in query_lower for word in ['unique', 'distinct', 'values']):
            result = self._show_unique_values(df, query)
        elif any(word in query_lower for word in ['outlier', 'anomal', 'extreme']):
            result = self._detect_outliers(df)
        elif any(word in query_lower for word in ['count', 'frequency', 'frequencies']):
            result = self._show_value_counts(df, query)
        elif any(word in query_lower for word in ['tail', 'last', 'bottom']):
            result = self._show_tail(df, query)
        else:
            # Default: provide overview
            result = self._describe_dataset(df)

        # Integration of Visualization Agent for non-SQL mode
        # If the analysis didn't already produce a plot, let the viz agent decide
        if result and 'artifacts' in result and not any(k in result['artifacts'] for k in ['bar_plot', 'heatmap_plot', 'distribution_plot', 'outlier_plot', 'plotly', 'generated_plot']):
            try:
                viz_result = self._decide_and_generate_visualization(df, query)
                if viz_result:
                    if 'plotly' in viz_result:
                        result['artifacts']['plotly'] = viz_result['plotly']
                        result['artifacts']['title'] = viz_result['title']
                    else:
                        result['artifacts']['generated_plot'] = viz_result['plot']
                    
                    result['ai_message'] += f"\n\n📊 **Visualization generated:** {viz_result['title']}"
            except Exception as e:
                print(f"[EDA] Visualization agent failed in analyze_dataset: {e}")

        return result
    
    def generate_reply(self, df: pd.DataFrame, question: str, context: str) -> Dict[str, Any]:
        """
        Generate a conversational response using LLM based on the context and data.
        This is used for follow-up questions via the /reply endpoint.
        """
        if not self.use_llm:
            return {
                'ai_message': "Conversational replies require LLM to be configured. Please set LLM_PROVIDER=ollama in your .env file.",
                'tool_calls': ['reply'],
                'artifacts': {}
            }
        
        # Get basic dataset info for context
        n_rows, n_cols = df.shape
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        # Create context for LLM
        data_context = f"""Dataset Information:
- Shape: {n_rows} rows x {n_cols} columns
- Numeric columns: {', '.join(numeric_cols[:5])}
- Categorical columns: {', '.join(categorical_cols[:5])}
- Sample data (first 3 rows): {df.head(3).to_dict('records')}
"""
        
        prompt = f'''You are an expert data analyst helping a user understand their data.

Previous Context:
{context}

User's Follow-up Question:
{question}

{data_context}

Provide a helpful, insightful response to the user's follow-up question. Be specific and reference actual values from the dataset when relevant. Keep your response concise (2-3 paragraphs max).

If the question asks "why" or requests explanation, provide data-driven insights based on the statistics and patterns you can see.'''

        response_text = self._call_llm(prompt)
        
        if not response_text:
            response_text = "I couldn't generate a detailed response. Try asking a more specific question or use one of the analysis options."
        
        return {
            'ai_message': response_text,
            'tool_calls': ['reply'],
            'artifacts': {}
        }
    
    def _describe_dataset(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Provide dataset description and statistics."""
        
        # Basic info
        n_rows, n_cols = df.shape
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        # Generate description
        message = f"""## Dataset Overview

**Shape:** {n_rows} rows x {n_cols} columns

**Column Types:**
- Numeric columns ({len(numeric_cols)}): {', '.join(numeric_cols[:5])}{'...' if len(numeric_cols) > 5 else ''}
- Categorical columns ({len(categorical_cols)}): {', '.join(categorical_cols[:5])}{'...' if len(categorical_cols) > 5 else ''}

**Missing Values:** {df.isnull().sum().sum()} total missing values

**Memory Usage:** {(df.memory_usage(deep=True).sum() / 1048576):.2f} MB
"""
        
        # Statistical summary
        describe_df = df.describe(include='all').fillna('').to_dict('records')
        
        artifacts = {
            'describe_df': describe_df
        }
        
        return {
            'ai_message': message,
            'tool_calls': ['describe_dataset'],
            'artifacts': artifacts
        }
    
    def _analyze_missing_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze missing data patterns."""
        
        missing_counts = df.isnull().sum()
        missing_pct = (missing_counts / len(df) * 100).round(2)
        
        cols_with_missing = missing_counts[missing_counts > 0].sort_values(ascending=False)
        
        if len(cols_with_missing) == 0:
            message = "✅ **No missing values found in the dataset!**"
            return {
                'ai_message': message,
                'tool_calls': ['visualize_missing'],
                'artifacts': {}
            }
        
        message = f"""## Missing Data Analysis

**Total missing values:** {missing_counts.sum()} ({(missing_counts.sum() / df.size * 100):.2f}% of all data)

**Columns with missing data:**
"""
        for col in cols_with_missing.index[:10]:
            message += f"\n- **{col}**: {cols_with_missing[col]} missing ({missing_pct[col]:.1f}%)"
        
        # Create visualization
        fig, ax = plt.subplots(figsize=(10, 6))
        cols_with_missing[:15].plot(kind='barh', ax=ax, color='#22d3ee')
        ax.set_xlabel('Number of Missing Values')
        ax.set_title('Missing Values by Column')
        ax.set_facecolor('#0f172a')
        fig.patch.set_facecolor('#0f172a')
        ax.tick_params(colors='#cbd5e1')
        ax.xaxis.label.set_color('#cbd5e1')
        ax.yaxis.label.set_color('#cbd5e1')
        ax.title.set_color('#22d3ee')
        
        bar_plot = self._fig_to_base64(fig)
        plt.close(fig)
        
        artifacts = {
            'bar_plot': bar_plot
        }
        
        return {
            'ai_message': message,
            'tool_calls': ['visualize_missing'],
            'artifacts': artifacts
        }
    
    def _analyze_correlations(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze correlations between numeric columns."""
        
        numeric_df = df.select_dtypes(include=[np.number])
        
        if numeric_df.shape[1] < 2:
            message = "⚠️ **Not enough numeric columns for correlation analysis.** Need at least 2 numeric columns."
            return {
                'ai_message': message,
                'tool_calls': ['generate_correlation_funnel'],
                'artifacts': {}
            }
        
        corr_matrix = numeric_df.corr()
        
        message = f"""## Correlation Analysis

Analyzed correlations between {numeric_df.shape[1]} numeric columns.

**Strongest positive correlations:**
"""
        
        # Get top correlations (excluding diagonal)
        corr_pairs = []
        for i in range(len(corr_matrix.columns)):
            for j in range(i+1, len(corr_matrix.columns)):
                corr_pairs.append({
                    'col1': corr_matrix.columns[i],
                    'col2': corr_matrix.columns[j],
                    'correlation': corr_matrix.iloc[i, j]
                })
        
        corr_pairs_sorted = sorted(corr_pairs, key=lambda x: abs(x['correlation']), reverse=True)
        
        for pair in corr_pairs_sorted[:5]:
            message += f"\n- **{pair['col1']}** ↔ **{pair['col2']}**: {pair['correlation']:.3f}"
        
        # Create heatmap
        fig, ax = plt.subplots(figsize=(10, 8))
        sns.heatmap(corr_matrix, annot=True, fmt='.2f', cmap='coolwarm', 
                    center=0, ax=ax, cbar_kws={'label': 'Correlation'})
        ax.set_title('Correlation Heatmap')
        ax.set_facecolor('#0f172a')
        fig.patch.set_facecolor('#0f172a')
        
        heatmap_plot = self._fig_to_base64(fig)
        plt.close(fig)
        
        artifacts = {
            'heatmap_plot': heatmap_plot
        }
        
        return {
            'ai_message': message,
            'tool_calls': ['generate_correlation_funnel'],
            'artifacts': artifacts
        }
    
    def _analyze_distributions(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze distributions of numeric columns."""
        
        numeric_df = df.select_dtypes(include=[np.number])
        
        if numeric_df.shape[1] == 0:
            message = "⚠️ **No numeric columns found for distribution analysis.**"
            return {
                'ai_message': message,
                'tool_calls': ['analyze_distributions'],
                'artifacts': {}
            }
        
        message = f"""## Distribution Analysis

Showing distributions for {min(6, numeric_df.shape[1])} numeric columns.
"""
        
        # Create distribution plots
        n_cols = min(6, numeric_df.shape[1])
        fig, axes = plt.subplots(2, 3, figsize=(15, 10))
        axes = axes.flatten()
        
        for idx, col in enumerate(numeric_df.columns[:n_cols]):
            axes[idx].hist(numeric_df[col].dropna(), bins=30, color='#22d3ee', edgecolor='#0f172a')
            axes[idx].set_title(col, color='#22d3ee')
            axes[idx].set_facecolor('#0f172a')
            axes[idx].tick_params(colors='#cbd5e1')
        
        # Hide unused subplots
        for idx in range(n_cols, 6):
            axes[idx].set_visible(False)
        
        fig.patch.set_facecolor('#0f172a')
        fig.tight_layout()
        
        dist_plot = self._fig_to_base64(fig)
        plt.close(fig)
        
        artifacts = {
            'distribution_plot': dist_plot
        }
        
        return {
            'ai_message': message,
            'tool_calls': ['analyze_distributions'],
            'artifacts': artifacts
        }
    
    def _show_sample(self, df: pd.DataFrame, query: str) -> Dict[str, Any]:
        """Show sample rows from dataset."""
        
        # Extract number from query if present
        import re
        numbers = re.findall(r'\d+', query)
        n_rows = int(numbers[0]) if numbers else 5
        n_rows = min(n_rows, 20)  # Cap at 20 rows
        
        sample_df = df.head(n_rows).to_dict('records')
        
        message = f"""## Dataset Sample

Showing first {n_rows} rows of the dataset.
"""
        
        artifacts = {
            'sample_df': sample_df
        }
        
        return {
            'ai_message': message,
            'tool_calls': ['show_sample'],
            'artifacts': artifacts
        }
    
    def _show_tail(self, df: pd.DataFrame, query: str) -> Dict[str, Any]:
        """Show last rows from dataset."""
        
        import re
        numbers = re.findall(r'\d+', query)
        n_rows = int(numbers[0]) if numbers else 5
        n_rows = min(n_rows, 20)
        
        tail_df = df.tail(n_rows).to_dict('records')
        
        message = f"""## Dataset Tail

Showing last {n_rows} rows of the dataset.
"""
        
        artifacts = {
            'sample_df': tail_df
        }
        
        return {
            'ai_message': message,
            'tool_calls': ['show_tail'],
            'artifacts': artifacts
        }
    
    def _show_all_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Show all data (with reasonable limit)."""
        
        max_rows = 100
        n_rows = min(len(df), max_rows)
        
        if len(df) > max_rows:
            message = f"""## Full Dataset (Limited)

⚠️ Dataset has {len(df)} rows. Showing first {max_rows} rows for performance.
"""
        else:
            message = f"""## Full Dataset

Showing all {len(df)} rows.
"""
        
        all_data = df.head(max_rows).to_dict('records')
        
        artifacts = {
            'sample_df': all_data
        }
        
        return {
            'ai_message': message,
            'tool_calls': ['show_all_data'],
            'artifacts': artifacts
        }
    
    def _show_column_info(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Show detailed column information."""
        
        col_info = []
        for col in df.columns:
            info = {
                'Column': col,
                'Type': str(df[col].dtype),
                'Non-Null': df[col].count(),
                'Null': df[col].isnull().sum(),
                'Unique': df[col].nunique(),
                'Sample': str(df[col].iloc[0]) if len(df) > 0 else 'N/A'
            }
            col_info.append(info)
        
        message = f"""## Column Information

**Total Columns:** {len(df.columns)}

**Data Types:**
"""
        
        type_counts = df.dtypes.value_counts()
        for dtype, count in type_counts.items():
            message += f"\n- {dtype}: {count} columns"
        
        artifacts = {
            'describe_df': col_info
        }
        
        return {
            'ai_message': message,
            'tool_calls': ['show_column_info'],
            'artifacts': artifacts
        }
    
    def _show_unique_values(self, df: pd.DataFrame, query: str) -> Dict[str, Any]:
        """Show unique values for categorical columns."""
        
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        if not categorical_cols:
            message = "⚠️ **No categorical columns found in the dataset.**"
            return {
                'ai_message': message,
                'tool_calls': ['show_unique_values'],
                'artifacts': {}
            }
        
        message = f"""## Unique Values Analysis

Analyzing {len(categorical_cols)} categorical columns.

**Unique value counts:**
"""
        
        unique_info = []
        for col in categorical_cols[:10]:  # Limit to 10 columns
            n_unique = df[col].nunique()
            message += f"\n- **{col}**: {n_unique} unique values"
            
            # If few unique values, show them
            if n_unique <= 10:
                top_values = df[col].value_counts().head(10).to_dict()
                unique_info.append({
                    'Column': col,
                    'Unique_Count': n_unique,
                    'Top_Values': ', '.join([f"{k} ({v})" for k, v in list(top_values.items())[:5]])
                })
        
        artifacts = {}
        if unique_info:
            artifacts['describe_df'] = unique_info
        
        return {
            'ai_message': message,
            'tool_calls': ['show_unique_values'],
            'artifacts': artifacts
        }
    
    def _detect_outliers(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Detect outliers using IQR method."""
        
        numeric_df = df.select_dtypes(include=[np.number])
        
        if numeric_df.shape[1] == 0:
            message = "⚠️ **No numeric columns found for outlier detection.**"
            return {
                'ai_message': message,
                'tool_calls': ['detect_outliers'],
                'artifacts': {}
            }
        
        outlier_info = []
        message = f"""## Outlier Detection (IQR Method)

Analyzing {numeric_df.shape[1]} numeric columns.

**Outliers found:**
"""
        
        for col in numeric_df.columns:
            Q1 = numeric_df[col].quantile(0.25)
            Q3 = numeric_df[col].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            outliers = numeric_df[(numeric_df[col] < lower_bound) | (numeric_df[col] > upper_bound)][col]
            n_outliers = len(outliers)
            
            if n_outliers > 0:
                pct = (n_outliers / len(df) * 100)
                message += f"\n- **{col}**: {n_outliers} outliers ({pct:.1f}%)"
                outlier_info.append({
                    'Column': col,
                    'Outliers': n_outliers,
                    'Percentage': f"{pct:.1f}%",
                    'Lower_Bound': f"{lower_bound:.2f}",
                    'Upper_Bound': f"{upper_bound:.2f}"
                })
        
        if not outlier_info:
            message += "\n\n✅ **No outliers detected in any numeric column.**"
        
        # Create boxplot
        fig, axes = plt.subplots(1, min(4, numeric_df.shape[1]), figsize=(15, 5))
        if numeric_df.shape[1] == 1:
            axes = [axes]
        
        for idx, col in enumerate(numeric_df.columns[:4]):
            axes[idx].boxplot(numeric_df[col].dropna(), vert=True)
            axes[idx].set_title(col, color='#22d3ee')
            axes[idx].set_facecolor('#0f172a')
            axes[idx].tick_params(colors='#cbd5e1')
        
        fig.patch.set_facecolor('#0f172a')
        fig.tight_layout()
        
        boxplot = self._fig_to_base64(fig)
        plt.close(fig)
        
        artifacts = {
            'outlier_plot': boxplot
        }
        
        if outlier_info:
            artifacts['describe_df'] = outlier_info
        
        return {
            'ai_message': message,
            'tool_calls': ['detect_outliers'],
            'artifacts': artifacts
        }
    
    def _show_value_counts(self, df: pd.DataFrame, query: str) -> Dict[str, Any]:
        """Show value counts for categorical columns."""
        
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        if not categorical_cols:
            message = "⚠️ **No categorical columns found.**"
            return {
                'ai_message': message,
                'tool_calls': ['show_value_counts'],
                'artifacts': {}
            }
        
        # Try to extract column name from query
        target_col = None
        for col in df.columns:
            if col.lower() in query.lower():
                target_col = col
                break
        
        # If no specific column, use first categorical
        if not target_col:
            target_col = categorical_cols[0]
        
        value_counts = df[target_col].value_counts().head(20)
        
        message = f"""## Value Counts: {target_col}

**Top {len(value_counts)} values:**
"""
        
        for val, count in value_counts.items():
            pct = (count / len(df) * 100)
            message += f"\n- **{val}**: {count} ({pct:.1f}%)"
        
        # Create bar chart
        fig, ax = plt.subplots(figsize=(10, 6))
        value_counts.plot(kind='barh', ax=ax, color='#22d3ee')
        ax.set_xlabel('Count')
        ax.set_title(f'Value Counts: {target_col}')
        ax.set_facecolor('#0f172a')
        fig.patch.set_facecolor('#0f172a')
        ax.tick_params(colors='#cbd5e1')
        ax.xaxis.label.set_color('#cbd5e1')
        ax.yaxis.label.set_color('#cbd5e1')
        ax.title.set_color('#22d3ee')
        
        bar_plot = self._fig_to_base64(fig)
        plt.close(fig)
        
        artifacts = {
            'bar_plot': bar_plot,
            'describe_df': [{'Value': str(k), 'Count': int(v), 'Percentage': f"{(v/len(df)*100):.1f}%"} for k, v in value_counts.items()]
        }
        
        return {
            'ai_message': message,
            'tool_calls': ['show_value_counts'],
            'artifacts': artifacts
        }
    
    def _fig_to_base64(self, fig) -> str:
        """Convert matplotlib figure to base64 string."""
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=100, bbox_inches='tight', facecolor='#0f172a')
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')
        buf.close()
        return img_base64
