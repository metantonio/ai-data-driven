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
        
        # If relative, make it absolute if it exists or try alternatives
        if not path_to_check.is_absolute():
            # If it exists relative to CWD, make it absolute
            if path_to_check.exists():
                 return f"sqlite:///{path_to_check.absolute()}"

            alternatives = []
            # If frozen, the execution context is different
            if getattr(sys, 'frozen', False):
                # The .exe is in backend/dist/, try relative to executable
                alternatives.append(Path(sys.executable).parent / original_path)
                # Try project root (relative to dist)
                proj_root = Path(sys.executable).parent.parent.parent
                alternatives.append(proj_root / original_path)
                # Try next to .exe stripping any leading ../
                base_name = original_path.replace("../", "")
                alternatives.append(Path(sys.executable).parent / base_name)
            
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
                    cwd = os.getcwd()
                    raise FileNotFoundError(
                        f"Database file not found at: {abs_path}\n"
                        f"Current working directory: {cwd}\n"
                        f"Original connection string: {connection_string}\n"
                        f"Tip: Use an absolute path like 'sqlite:///C:/full/path/to/database.db' "
                        f"or ensure the relative path is correct from the executable location."
                    )
        
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
