#!/usr/bin/env python3
"""Executable smoke evaluation for the structured disclosure pipeline."""

from __future__ import annotations

import copy
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / ".agents" / "skills" / "patent-disclosure-distiller" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from pipeline import load_json, render_package, validate_outputs, validate_package  # noqa: E402


def minimal_mode(source: dict, mode: str) -> dict:
    value = copy.deepcopy(source)
    value["metadata"]["delivery_mode"] = mode
    value["sections"] = [
        {
            "id": "intake",
            "title": "交付说明",
            "level": 1,
            "blocks": [
                {"type": "paragraph", "text": "当前只形成待补证据的最小技术链。", "evidence": ["ev-q-effect"]}
            ],
        }
    ]
    value["figures"] = []
    value.pop("mode_contract", None)
    value.pop("requested_sections", None)
    value.pop("rewrite_audit", None)
    if mode == "TARGETED_SECTION":
        value["requested_sections"] = ["intake"]
    elif mode == "REWRITE_AUDIT":
        value["rewrite_audit"] = [{"original": "原句", "problem": "缺证据", "rewrite": "保留待确认标记"}]
    return value


def main() -> int:
    fixture = ROOT / ".agents" / "skills" / "patent-disclosure-distiller" / "examples" / "map-preload" / "package.json"
    source = load_json(fixture)
    failures = []
    if validate_package(source):
        failures.append("FULL_DISCLOSURE fixture should pass")
    for mode in ("INTAKE_DRAFT", "REWRITE_AUDIT", "TARGETED_SECTION"):
        candidate = minimal_mode(source, mode)
        if validate_package(candidate):
            failures.append(f"{mode} minimal package should pass")
        else:
            with tempfile.TemporaryDirectory() as directory:
                candidate_path = Path(directory) / "package.json"
                candidate_path.write_text(__import__("json").dumps(candidate, ensure_ascii=False), encoding="utf-8")
                output = Path(directory) / "output"
                from pipeline import render_package
                render_package(candidate_path, output)
                if validate_outputs(output):
                    failures.append(f"{mode} artifact output should pass")
                if mode == "REWRITE_AUDIT":
                    markdown = (output / "disclosure.md").read_text(encoding="utf-8")
                    for marker in ("原句", "缺证据", "保留待确认标记"):
                        if marker not in markdown:
                            failures.append(f"REWRITE_AUDIT missing rendered marker: {marker}")
                    manifest = __import__("json").loads((output / "manifest.json").read_text(encoding="utf-8"))
                    if not manifest.get("rewrite_audit"):
                        failures.append("REWRITE_AUDIT missing manifest rows")
    blocked = copy.deepcopy(source)
    blocked["audit"]["p0"] = ["unclosed"]
    if not validate_package(blocked):
        failures.append("P0 package should fail closed")
    with tempfile.TemporaryDirectory() as directory:
        output = Path(directory)
        render_package(fixture, output)
        if validate_outputs(output):
            failures.append("generated output should pass")
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1
    print("PASS: FULL_DISCLOSURE + INTAKE_DRAFT + REWRITE_AUDIT + TARGETED_SECTION + output smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
