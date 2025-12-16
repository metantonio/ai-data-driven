from sqlalchemy import create_engine, inspect
from typing import Dict, Any, List

class DatabaseInspector:
    def __init__(self, connection_string: str):
        self.engine = create_engine(connection_string)
        
        # SQLite specific validations
        if connection_string.startswith("sqlite:///"):
            path = connection_string.replace("sqlite:///", "")
            # Only check if it's a file path (not :memory:)
            if path != ":memory:":
                import os
                # Provide absolute path for clarity in error
                abs_path = os.path.abspath(path)
                if not os.path.exists(path):
                    raise FileNotFoundError(f"Database file not found at: {abs_path}")
        
        # Test connection immediately to fail fast
        try:
            with self.engine.connect() as conn:
                pass
        except Exception as e:
            # Re-raise with clear context
            raise ConnectionError(f"Failed to connect to database: {str(e)}")

        self.inspector = inspect(self.engine)

    def get_schema_summary(self) -> Dict[str, Any]:
        """
        Returns a dictionary summarizing the database schema:
        {
            "tables": {
                "table_name": {
                    "columns": [{"name": "col1", "type": "INTEGER", "primary_key": True}, ...],
                    "foreign_keys": [...]
                }
            }
        }
        """
        summary = {"tables": {}}
        
        for table_name in self.inspector.get_table_names():
            columns = []
            for col in self.inspector.get_columns(table_name):
                columns.append({
                    "name": col["name"],
                    "type": str(col["type"]),
                    "primary_key": col.get("primary_key", False),
                    "nullable": col.get("nullable", True)
                })
            
            fks = self.inspector.get_foreign_keys(table_name)
            
            summary["tables"][table_name] = {
                "columns": columns,
                "foreign_keys": fks
            }
            
        return summary
