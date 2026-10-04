#!/usr/bin/env python3
"""Validate a DisclosurePackage JSON or a generated artifact directory."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from pipeline import validate_output_or_input  # type: ignore
else:
    from .pipeline import validate_output_or_input


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, help="输入 JSON 或生成产物目录")
    args = parser.parse_args()
    errors = validate_output_or_input(args.path)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"VALID: {args.path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
