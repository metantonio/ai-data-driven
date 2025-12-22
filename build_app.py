import subprocess
import shutil
import os
from pathlib import Path

def run_command(command, cwd=None, env=None):
    print(f"Executing: {command} in {cwd or 'current directory'}")
    # Merge current env with provided env
    full_env = os.environ.copy()
    if env:
        full_env.update(env)
    
    # Use stdin=subprocess.DEVNULL to prevent PyInstaller sub-processes from 
    # trying to open the console input buffer on Windows, which causes crashes.
    result = subprocess.run(
        command, 
        shell=True, 
        cwd=cwd, 
        env=full_env, 
        stdin=subprocess.DEVNULL
    )
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
    
    # Extract version from backend/app/version.py
    version = "unknown"
    version_file = backend_dir / "app" / "version.py"
    if version_file.exists():
        with open(version_file, "r") as f:
            content = f.read()
            import re
            match = re.search(r'VERSION\s*=\s*["\']([^"\']+)["\']', content)
            if match:
                version = match.group(1)
    
    app_name = f"QLX-AI-Data-Science-App-v{version}"
    print(f"Building version: {version} -> {app_name}")

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
        "--collect-all scipy "
        "--collect-all lightgbm "
        "--collect-all imblearn "
        "--add-data \"static;static\" "
        "--add-data \"app;app\" "
        "--add-data \"../ml_template;ml_template\" "
        "--add-data \"../pipeline.py;.\" "
        f"--name \"{app_name}\" "
        "server.py"
    )
    
    # Critical Fix for PyInstaller crash on Windows: Disable isolated python analysis
    # and ensure it's in the environment for all subsequent calls.
    os.environ["PYINSTALLER_ISOLATED_PYTHON"] = "0"
    run_command(pyinstaller_cmd, cwd=str(backend_dir))

    print("\n--- Success! ---")
    print(f"Your executable can be found in: {backend_dir / 'dist' / (app_name + '.exe')}")

if __name__ == "__main__":
    build_app()
