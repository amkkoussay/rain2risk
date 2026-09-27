#!/usr/bin/env python3
"""Run one Rain2Risk analysis through the same service orchestration as the API.

This wrapper is intentionally dependency-light. It is useful for demos, manual
verification, and producing a saved JSON artifact without starting the HTTP UI.
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from api.analyze import analyze  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the Rain2Risk analysis pipeline for one location")
    parser.add_argument("--lat", type=float, required=True, help="Latitude from -90 to 90")
    parser.add_argument("--lon", type=float, required=True, help="Longitude from -180 to 180")
    parser.add_argument("--output", type=Path, help="Optional JSON output path")
    args = parser.parse_args()
    try:
        result = analyze(args.lat, args.lon)
    except Exception as error:  # provider errors are surfaced as a readable CLI failure
        print(f"Rain2Risk analysis failed: {error}", file=sys.stderr)
        return 1
    serialized = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        output = args.output if args.output.is_absolute() else ROOT / args.output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(serialized + "\n", encoding="utf-8")
        print(f"Saved analysis to {output}")
    else:
        print(serialized)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
