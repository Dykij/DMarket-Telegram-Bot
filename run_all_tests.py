"""Run all unit tests with detailed output."""

import subprocess
import sys


if __name__ == "__main__":
    print("=" * 80)
    print("Starting full test suite...")
    print("=" * 80)

    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "tests/",
        "-v",
        "--tb=short",
        "--maxfail=10",
        "--color=yes",
        "-x",
    ]

    result = subprocess.run(cmd, check=False, capture_output=False, text=True)

    print("\n" + "=" * 80)
    print(f"Tests finished with exit code: {result.returncode}")
    print("=" * 80)

    sys.exit(result.returncode)
