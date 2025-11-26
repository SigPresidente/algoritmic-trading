import os
import subprocess
import sys
import platform

VENV_DIR = ".venv"

def run(cmd):
    print("> " + " ".join(cmd))
    subprocess.check_call(cmd)

# 1. Create venv
print("Creating virtual environment...")
run([sys.executable, "-m", "venv", VENV_DIR])

# 2. Select correct activation script
if platform.system() == "Windows":
    activate = os.path.join(VENV_DIR, "Scripts", "activate")
else:
    activate = os.path.join(VENV_DIR, "bin", "activate")

print(f"Activate it manually with: source {activate}")

# 3. Use venv's pip
pip_path = os.path.join(VENV_DIR, "Scripts" if platform.system() == "Windows" else "bin", "pip")

print("Installing requirements...")
run([pip_path, "install", "--upgrade", "pip"])
run([pip_path, "install", "-r", "requirements.txt"])

print("Installation complete!")
