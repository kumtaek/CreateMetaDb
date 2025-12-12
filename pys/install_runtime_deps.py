import subprocess
import sys

def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

if __name__ == "__main__":
    print("No runtime dependencies required.")
    print("Using regex-based parsing only - no external libraries needed.")
