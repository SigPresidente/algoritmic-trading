import os
import subprocess
import sys
import platform

VENV_DIR = ".venv"

def run(cmd):
    print("> " + " ".join(cmd))
    subprocess.check_call(cmd)

def main():
    # 1) Create virtual environment
    print("Creating virtual environment...")
    run([sys.executable, "-m", "venv", VENV_DIR])

    # 2) Determine correct paths based on OS
    if platform.system() == "Windows":
        python_path = os.path.join(VENV_DIR, "Scripts", "python")
        pip_path = os.path.join(VENV_DIR, "Scripts", "pip")
        activate_cmd = os.path.join(VENV_DIR, "Scripts", "activate")
    else:  # macOS/Linux
        python_path = os.path.join(VENV_DIR, "bin", "python")
        pip_path = os.path.join(VENV_DIR, "bin", "pip")
        activate_cmd = f"source {os.path.join(VENV_DIR, 'bin', 'activate')}"

    # 3) Upgrade pip
    print("\nUpgrading pip...")
    run([python_path, "-m", "pip", "install", "--upgrade", "pip"])

    if platform.system() == "Darwin":  #specific for macOS
        print("\nNote: TA-Lib requires the C library.")
        print("If not installed, run: brew install ta-lib")
        input("Press Enter to continue...")

    # 4) Install requirements
    print("\nInstalling requirements...")
    run([pip_path, "install", "-r", "requirements.txt"])

    print("\n" + "="*60)
    print("Installation complete!")
    print("="*60)
    print(f"\nTo activate the virtual environment, run:")
    print(f"  {activate_cmd}")
    print(f"\nThen run your main script with:")
    print(f"  python main.py")
    print("="*60)

if __name__ == "__main__":
    main()
