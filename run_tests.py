"""Test runner script to bypass PowerShell encoding issues."""

import subprocess
import sys

if __name__ == "__main__":
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "tests/test_crash_notif.py",
        "-v",
        "--tb=short",
        "--color=yes",
    ]

    result = subprocess.run(cmd, check=False, capture_output=False, text=True)
    sys.exit(result.returncode)
