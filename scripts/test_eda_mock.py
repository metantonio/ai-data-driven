
import sys
import os
import pytest
from unittest.mock import MagicMock, patch

# Adjust path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from app.services.eda_service import EDAService

@patch('app.services.eda_service.EDAToolsAgent')
@patch('app.services.eda_service.ChatOpenAI')
def test_eda_service_mock(mock_chat, mock_agent_cls):
    # Setup Mock Agent
    mock_agent_instance = MagicMock()
    mock_agent_cls.return_value = mock_agent_instance
    
    # Mock methods
    mock_agent_instance.get_ai_message.return_value = "Here is the missing data visualization."
    mock_agent_instance.get_tool_calls.return_value = ["visualize_missing"]
    
    # Mock Artifacts (Dict structure as expected by frontend mapping)
    mock_artifacts = {
        "matrix_plot": "base64encodedstring...",
        "bar_plot": "base64encodedstring2...",
        "heatmap_plot": None
    }
    mock_agent_instance.get_artifacts.return_value = mock_artifacts

    # Initialize Service
    service = EDAService(api_key="sk-test")
    
    # Fake Data
    import pandas as pd
    df = pd.DataFrame({"A": [1, 2], "B": [3, 4]})
    
    # Execute
    result = service.process_query("Maximize missing values", df)
    
    # Verify
    assert result["ai_message"] == "Here is the missing data visualization."
    assert result["tool_calls"] == ["visualize_missing"]
    assert result["artifacts"]["matrix_plot"] == "base64encodedstring..."
    
    print("✅ EDAService returned expected structure.")

if __name__ == "__main__":
    # helper to run without pytest if needed, but standard is pytest
    try:
        test_eda_service_mock()
    except Exception as e:
        print(f"❌ Test Failed: {e}")
        import traceback
        traceback.print_exc()
