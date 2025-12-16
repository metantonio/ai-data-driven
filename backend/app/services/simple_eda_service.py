
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

class SimpleEDAService:
    """
    Simplified EDA service that performs common exploratory data analysis tasks
    without requiring complex LLM tool calling.
    """
    
    def __init__(self):
        # Set seaborn style
        sns.set_style("darkgrid")
        
    def analyze_dataset(self, df: pd.DataFrame, query: str) -> Dict[str, Any]:
        """
        Analyze dataset based on user query.
        Returns structured response with message and artifacts.
        """
        query_lower = query.lower()
        
        # Determine what analysis to perform based on query
        if any(word in query_lower for word in ['describe', 'summary', 'overview', 'info']):
            return self._describe_dataset(df)
        elif any(word in query_lower for word in ['missing', 'null', 'nan']):
            return self._analyze_missing_data(df)
        elif any(word in query_lower for word in ['correlation', 'correlate']):
            return self._analyze_correlations(df)
        elif any(word in query_lower for word in ['distribution', 'histogram', 'hist']):
            return self._analyze_distributions(df)
        elif any(word in query_lower for word in ['first', 'head', 'sample', 'rows']):
            return self._show_sample(df, query)
        else:
            # Default: provide overview
            return self._describe_dataset(df)
    
    def _describe_dataset(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Provide dataset description and statistics."""
        
        # Basic info
        n_rows, n_cols = df.shape
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        # Generate description
        message = f"""## Dataset Overview

**Shape:** {n_rows} rows × {n_cols} columns

**Column Types:**
- Numeric columns ({len(numeric_cols)}): {', '.join(numeric_cols[:5])}{'...' if len(numeric_cols) > 5 else ''}
- Categorical columns ({len(categorical_cols)}): {', '.join(categorical_cols[:5])}{'...' if len(categorical_cols) > 5 else ''}

**Missing Values:** {df.isnull().sum().sum()} total missing values

**Memory Usage:** {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB
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
    
    def _fig_to_base64(self, fig) -> str:
        """Convert matplotlib figure to base64 string."""
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=100, bbox_inches='tight', facecolor='#0f172a')
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')
        buf.close()
        return img_base64
