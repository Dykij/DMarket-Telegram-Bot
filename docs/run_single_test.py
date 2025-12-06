#!/usr/bin/env python
"""Script to run a single test and capture output."""

import subprocess
import sys

# Test to run
test_path = "tests/telegram_bot/handlers/test_market_alerts_handler.py::TestAlertsCommand::test_alerts_command_exception_handling"

# Run pytest
result = subprocess.run(
    [sys.executable, "-m", "pytest", test_path, "-xvs", "--tb=long"],
    check=False,
    capture_output=True,
    text=True,
)

print("STDOUT:")
print(result.stdout)
print("\nSTDERR:")
print(result.stderr)
print(f"\nReturn code: {result.returncode}")
