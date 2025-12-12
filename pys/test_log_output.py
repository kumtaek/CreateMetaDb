
print("Starting test_log_output.py")
import sys
import os

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from util.logger import info, error, handle_error
    print("Imported util.logger")
except Exception as e:
    print(f"Failed to import util.logger: {e}")
    sys.exit(1)

def test_logging():
    print("Running test_logging")
    info("This is an info message")
    error("This is an error message")

def test_exception():
    print("Running test_exception")
    try:
        1 / 0
    except Exception as e:
        handle_error(e, "Zero division error")

if __name__ == "__main__":
    test_logging()
    # We expect handle_error to exit, so run it last or in a separate run
    test_exception()
