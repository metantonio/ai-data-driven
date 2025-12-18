from sqlalchemy import create_engine, inspect
from typing import Dict, Any, List

class DatabaseInspector:
    def __init__(self, connection_string: str):
        import os
        import sys
        from pathlib import Path

        # 1. Path Robustness for SQLite
        if connection_string.startswith("sqlite:///"):
            original_path = connection_string.replace("sqlite:///", "")
            
            if original_path != ":memory:":
                # Try to resolve the path
                path_to_check = Path(original_path)
                
                # If path doesn't exist, try common alternatives (like ../../ in .exe)
                if not path_to_check.exists():
                    alternatives = []
                    # If frozen, the execution context is different
                    if getattr(sys, 'frozen', False):
                        # The .exe is in backend/dist/, so ../../ might be the project root
                        alternatives.append(Path(sys.executable).parent / ".." / ".." / original_path.replace("../", ""))
                        alternatives.append(Path(sys.executable).parent / original_path)
                    
                    # Also try relative to current working directory
                    alternatives.append(Path(os.getcwd()) / original_path)
                    
                    for alt in alternatives:
                        if alt.exists():
                            path_to_check = alt
                            connection_string = f"sqlite:///{alt.absolute()}"
                            print(f"Database found at alternative path: {alt}")
                            break
                
                # Final check
                if not path_to_check.exists():
                    abs_path = os.path.abspath(original_path)
                    raise FileNotFoundError(f"Database file not found. Original: {original_path}, Absolute: {abs_path}")

        self.engine = create_engine(connection_string)
        
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
