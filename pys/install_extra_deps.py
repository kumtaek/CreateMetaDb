#!/usr/bin/env python3
"""install_extra_deps.py

Utility script to install only the *additional* (non‑standard‑library) Python packages
required for development and testing of the SourceAnalyzer project.

The project itself depends solely on the Python standard library and internal
modules under the `util/` package.  The only external dependencies are listed in
`requirements-dev.txt` (e.g., pytest, pytest‑cov, coverage).  This script reads
that file – if it exists – and invokes ``pip`` to install the packages into the
current environment.

Usage:
    python install_extra_deps.py   # installs the dev dependencies

The script is safe to run multiple times; ``pip`` will skip already‑installed
packages.
"""
import os
import subprocess
import sys
from pathlib import Path

def main() -> None:
    """Install development dependencies defined in ``requirements-dev.txt``.

    The function performs the following steps:
    1. Locate ``requirements-dev.txt`` in the same directory as this script.
    2. Verify that the file exists; if not, print a friendly message and exit.
    3. Call ``python -m pip install -r <file>`` using ``subprocess.run``.
       ``check=True`` ensures an exception is raised on failure.
    4. Forward the exit code of the pip process to the caller.
    """
    script_dir = Path(__file__).resolve().parent
    req_file = script_dir / "requirements-dev.txt"

    if not req_file.is_file():
        print("[install_extra_deps] No 'requirements-dev.txt' found – nothing to install.")
        sys.exit(0)

    print(f"[install_extra_deps] Installing packages from {req_file} ...")
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", str(req_file)],
            check=True,
        )
        print("[install_extra_deps] Installation completed successfully.")
    except subprocess.CalledProcessError as exc:
        print(f"[install_extra_deps] pip failed with exit code {exc.returncode}")
        sys.exit(exc.returncode)

if __name__ == "__main__":
    main()
