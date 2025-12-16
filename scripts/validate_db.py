
import sys
import os
from unittest.mock import MagicMock, patch

# Adjust path to import backend modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from app.services.db_inspector import DatabaseInspector

def test_sqlite_connection():
    print("\nTesting SQLite Connection...")
    # Should work with existing file or memory
    try:
        # :memory: is always valid
        inspector = DatabaseInspector("sqlite:///:memory:")
        print("✅ SQLite :memory: connection successful.")
    except Exception as e:
        print(f"❌ SQLite :memory: failed: {e}")

def test_postgres_connection_mock():
    print("\nTesting Postgres Connection (Mocked)...")
    with patch('sqlalchemy.create_engine') as mock_create_engine:
        mock_engine = MagicMock()
        mock_connection = MagicMock()
        mock_engine.connect.return_value.__enter__.return_value = mock_connection
        mock_create_engine.return_value = mock_engine
        
        try:
            inspector = DatabaseInspector("postgresql://user:pass@localhost:5432/mydb")
            print("✅ Postgres connection string accepted.")
            mock_create_engine.assert_called_with("postgresql://user:pass@localhost:5432/mydb")
        except Exception as e:
            print(f"❌ Postgres connection failed: {e}")

def test_hana_connection_mock():
    print("\nTesting HANA Connection (Mocked)...")
    with patch('sqlalchemy.create_engine') as mock_create_engine:
        mock_engine = MagicMock()
        mock_connection = MagicMock()
        mock_engine.connect.return_value.__enter__.return_value = mock_connection
        mock_create_engine.return_value = mock_engine
        
        try:
            inspector = DatabaseInspector("hana://user:pass@host:30015")
            print("✅ HANA connection string accepted.")
            mock_create_engine.assert_called_with("hana://user:pass@host:30015")
        except Exception as e:
            print(f"❌ HANA connection failed: {e}")

if __name__ == "__main__":
    test_sqlite_connection()
    test_postgres_connection_mock()
    test_hana_connection_mock()
