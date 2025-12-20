import subprocess
import shutil
import os
from pathlib import Path

def run_command(command, cwd=None):
    print(f"Executing: {command} in {cwd or 'current directory'}")
    result = subprocess.run(command, shell=True, cwd=cwd)
    if result.returncode != 0:
        print(f"Error executing command: {command}")
        exit(1)

def build_app():
    root_dir = Path(__file__).parent.absolute()
    frontend_dir = root_dir / "frontend"
    backend_dir = root_dir / "backend"
    dist_dir = frontend_dir / "dist"
    static_dir = backend_dir / "static"

    print("--- 1. Building Frontend ---")
    run_command("npm install --legacy-peer-deps", cwd=str(frontend_dir))
    run_command("npm run build", cwd=str(frontend_dir))

    print("--- 2. Preparing Backend Static Folder ---")
    if static_dir.exists():
        shutil.rmtree(static_dir)
    shutil.copytree(dist_dir, static_dir)
    print(f"Copied frontend build to {static_dir}")

    print("--- 3. Running PyInstaller ---")
    
    # Ensure we use the virtual environment binaries if they exist
    venv_python = backend_dir / "venv" / "Scripts" / "python.exe"
    pyinstaller_base = "python -m PyInstaller"
    
    if venv_python.exists():
        pyinstaller_base = f'"{venv_python}" -m PyInstaller'
        print(f"Using virtual environment Python for PyInstaller: {venv_python}")
    else:
        print("Warning: Virtual environment python not found in backend/venv. Using global python.")

    pyinstaller_cmd = (
        f"{pyinstaller_base} --noconfirm --onefile --windowed "
        "--collect-all fastapi "
        "--collect-all uvicorn "
        "--collect-all pydantic "
        "--collect-all pandas "
        "--collect-all numpy "
        "--collect-all scikit-learn "
        "--collect-all sklearn "
        "--collect-all matplotlib "
        "--collect-all seaborn "
        "--collect-all joblib "
        "--collect-all statsmodels "
        "--collect-all mlxtend "
        "--collect-all ortools "
        "--collect-all sqlalchemy "
        "--collect-all plotly "
        "--collect-all shap "
        "--collect-all xgboost "
        "--collect-all lightgbm "
        "--collect-all imblearn "
        "--add-data \"static;static\" "
        "--add-data \"app;app\" "
        "--add-data \"../ml_template;ml_template\" "
        "--add-data \"../pipeline.py;.\" "
        "--name \"QLX-AI-Data-Science-App\" "
        "server.py"
    )
    run_command(pyinstaller_cmd, cwd=str(backend_dir))

    print("\n--- Success! ---")
    print(f"Your executable can be found in: {backend_dir / 'dist' / 'QLX-AI-Data-Science-App.exe'}")

if __name__ == "__main__":
    build_app()
