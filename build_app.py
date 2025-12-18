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
    # We bundle 'static' into the executable
    # --add-data "static;static" (Windows syntax)
    # We target server.py
    pyinstaller_cmd = (
        "pyinstaller --noconfirm --onefile --windowed "
        "--add-data \"static;static\" "
        "--add-data \"app;app\" "
        "--name \"AI-Data-Driven-App\" "
        "server.py"
    )
    run_command(pyinstaller_cmd, cwd=str(backend_dir))

    print("\n--- Success! ---")
    print(f"Your executable can be found in: {backend_dir / 'dist' / 'AI-Data-Driven-App.exe'}")

if __name__ == "__main__":
    build_app()
