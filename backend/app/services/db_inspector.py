from sqlalchemy import create_engine, inspect
from typing import Dict, Any, List

class DatabaseInspector:
    @staticmethod
    def resolve_connection_string(connection_string: str) -> str:
        """
        Resolves a connection string, handling relative SQLite paths robustly,
        especially in bundled (.exe) environments.
        """
        import os
        import sys
        from pathlib import Path

        if not connection_string.startswith("sqlite:///"):
            return connection_string

        original_path = connection_string.replace("sqlite:///", "")
        if original_path == ":memory:":
            return connection_string

        # Try to resolve the path
        path_to_check = Path(original_path)
        
        # If path doesn't exist, try common alternatives
        if not path_to_check.exists():
            alternatives = []
            # If frozen, the execution context is different
            if getattr(sys, 'frozen', False):
                # The .exe is in backend/dist/, so ../../ might be the project root
                # Original path might be ../example.db, we want to try ../../example.db
                # simplified: try relative to executable
                alternatives.append(Path(sys.executable).parent / ".." / ".." / original_path.replace("../", ""))
                alternatives.append(Path(sys.executable).parent / original_path)
            
            # Also try relative to current working directory
            alternatives.append(Path(os.getcwd()) / original_path)
            
            for alt in alternatives:
                if alt.exists():
                    print(f"Database found at alternative path: {alt}")
                    return f"sqlite:///{alt.absolute()}"
        
        return connection_string

    def __init__(self, connection_string: str):
        # Resolve the string first
        connection_string = self.resolve_connection_string(connection_string)
        
        self.engine = create_engine(connection_string)
        
        # SQLite specific validation (after resolution)
        if connection_string.startswith("sqlite:///"):
            path = connection_string.replace("sqlite:///", "")
            if path != ":memory:":
                import os
                if not os.path.exists(path):
                    abs_path = os.path.abspath(path)
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
