# QLX AI Powered ML System

QLX AI Powered ML System is a demo web application that uses machine learning to analyze and predict data from a database.

<img src="./portada.png" alt="QLX AI Powered ML System">

## Prerequisites
- Python 3.11.6+
- Node.js 24.11.1+

## 1. Start Support Services
Open a terminal and run the backend:
```bash
cd backend
# Create and activate virtual environment
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/Mac:
# source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
# Set environment variables
cp .env.example .env
# Run server
uvicorn app.main:app --reload
```

## 2. Start Frontend
Open another terminal:
```bash
cd frontend
# Install dependencies (if not done)
npm install --legacy-peer-deps
# Run dev server
npm run dev
```

## 3. Database Connection Examples

### SQLite (Default)
`sqlite:///../example.db`
`sqlite:///../example_casino.db`

### SAP HANA
`hana://user:password@host:port`
- Ensure `hdbcli` and `sqlalchemy-hana` are installed (included in requirements.txt).
- The port is typically 3xx15 where xx is the instance number (e.g., 30015 for instance 00).

### PostgreSQL / AWS RDS (PostgreSQL)
`postgresql://user:password@host:port/dbname`
- For AWS RDS, the host is usually the endpoint provided in the AWS Console (e.g., `mydb.cabc123.us-east-1.rds.amazonaws.com`).

### MySQL / AWS RDS (MySQL/MariaDB)
`mysql+pymysql://user:password@host:port/dbname`
- For AWS RDS, ensure the Security Group allows inbound traffic on port 3306 from your IP.

## 4. End-to-End Test Scenario
1. Open Browser to `http://localhost:5173`.
2. In the "Database Connection String" field, enter a valid string (see examples above).
   (Note: `example.db` was created in the root directory. The path is relative to where the backend runs. Since we run from `backend/`, we use `../example.db`. Alternatively, use absolute path).
3. Click "Analyze Database".
4. Monitor the "Pipeline Results" page:
   - **Adaptation**: Check if Python code appears in the code block.
   - **Execution**: Check if "Model Performance" metrics (MSE, R2) appear.
   - **Insights**: Check if a text summary appears.

## Troubleshooting
- **Connection Error**: Ensure the path to `example.db` is correct relative to the running backend process, or use absolute path.
- **Missing Dependencies**: Check [requirements.txt](file:///c:/Repositorios/ai-data-driven/backend/requirements.txt) for `scikit-learn` (it might be missing).

> `scikit-learn` was not explicitly added to [backend/requirements.txt](file:///c:/Repositorios/ai-data-driven/backend/requirements.txt) but is needed by the *generated* code. The execution environment needs it.

## Example Database (`example.db`)
A sample SQLite database is created in the root directory for testing.

**Table: `houses`**
| Column | Type | Description |
|:---|:---|:---|
| `sqft` | INTEGER | Square footage of the property |
| `bedrooms` | INTEGER | Number of bedrooms |
| `price` | REAL | Calculated price (Target Variable) |

Use connection string: `sqlite:///../example.db` (if running from `backend/` dir) or auto-resolved path in Dashboard.
