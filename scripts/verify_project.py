#!/usr/bin/env python3
"""Run lightweight project checks from any working directory."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMMANDS = [
    ("Python compile", [sys.executable, "-m", "compileall", "-q", "backend"]),
    ("Offline unit tests", [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"]),
    ("JavaScript syntax", ["node", "--check", "frontend/app.js"]),
]


def main() -> int:
    failures = 0
    print(f"Rain2Risk verification: {ROOT}")
    for label, command in COMMANDS:
        completed = subprocess.run(command, cwd=ROOT)
        status = "PASS" if completed.returncode == 0 else "FAIL"
        print(f"{status:4}  {label}")
        failures += completed.returncode != 0
    print("Live provider smoke test: run scripts/global_smoke_test.py separately; it requires network and an OpenWeather key.")
    return int(failures)


if __name__ == "__main__":
    raise SystemExit(main())
