#!/usr/bin/env python3
"""Generate Markdown, DOCX, figures and manifest from a DisclosurePackage."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from pipeline import PackageValidationError, render_package  # type: ignore
else:
    from .pipeline import PackageValidationError, render_package


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="DisclosurePackage JSON")
    parser.add_argument("output", type=Path, help="输出目录")
    parser.add_argument("--reference-docx", type=Path, default=None, help="样例版式参考 DOCX；sample_fidelity/sample_exact 模式可显式传入")
    args = parser.parse_args()
    try:
        manifest = render_package(args.input, args.output, reference_docx=args.reference_docx)
    except (OSError, UnicodeError, json.JSONDecodeError, PackageValidationError, TypeError, ValueError) as exc:
        print(f"生成失败：{exc}", file=sys.stderr)
        return 2
    print(json.dumps({"output": str(args.output), "files": len(manifest["files"]), "figures": len(manifest["figures"])}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
