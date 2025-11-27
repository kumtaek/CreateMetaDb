import subprocess
import sys

def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

if __name__ == "__main__":
    print("Installing runtime dependencies...")
    try:
        install("javalang")
        print("Successfully installed runtime dependencies.")
    except Exception as e:
        print(f"Error installing dependencies: {e}")
        sys.exit(1)
