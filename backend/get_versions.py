
import pkg_resources
required = [
    'fastapi', 'uvicorn', 'pydantic', 'pandas', 'sqlalchemy', 'alembic', 
    'asyncpg', 'python-multipart', 'requests', 'python-dotenv', 
    'scikit-learn', 'statsmodels', 'mlxtend', 'immutabledict', 
    'absl-py', 'ortools'
]
installed = {pkg.key: pkg.version for pkg in pkg_resources.working_set}
output = []
for r in required:
    ver = installed.get(r, 'MISSING')
    print(f"{r}=={ver}")
