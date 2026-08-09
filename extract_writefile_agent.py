#!/usr/bin/env python3
"""Extract one self-contained public agent from a Kaggle notebook safely.

The extractor accepts only a single ``%%writefile`` cell, validates its AST,
and rejects filesystem, process, network, or dynamic-execution primitives.
It is intentionally narrow so downloaded notebooks are never executed.
"""

from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path


ALLOWED_IMPORTS = {"base64", "copy", "json", "math", "zlib"}
FORBIDDEN_CALLS = {
    "__import__",
    "compile",
    "eval",
    "exec",
    "input",
    "open",
}


def _cell_source(cell: dict) -> str:
    source = cell.get("source", "")
    return "".join(source) if isinstance(source, list) else str(source)


def _validate(source: str) -> None:
    tree = ast.parse(source)
    has_agent = False
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "agent":
            has_agent = True
        elif isinstance(node, ast.Import):
            if any(alias.name.split(".", 1)[0] not in ALLOWED_IMPORTS for alias in node.names):
                raise RuntimeError("agent imports a module outside the safe allow-list")
        elif isinstance(node, ast.ImportFrom):
            if not node.module or node.module.split(".", 1)[0] not in ALLOWED_IMPORTS:
                raise RuntimeError("agent imports a module outside the safe allow-list")
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in FORBIDDEN_CALLS:
                raise RuntimeError(f"agent uses forbidden call {node.func.id}()")
        elif isinstance(node, ast.Attribute) and node.attr in {
            "connect", "download", "popen", "remove", "rmdir", "system", "unlink",
        }:
            raise RuntimeError(f"agent uses forbidden attribute {node.attr}")
    if not has_agent:
        raise RuntimeError("no top-level agent function found")


def extract(notebook: Path, destination: Path) -> None:
    payload = json.loads(notebook.read_text(encoding="utf-8"))
    matches = []
    for cell in payload.get("cells", []):
        if cell.get("cell_type") != "code":
            continue
        source = _cell_source(cell)
        lines = source.splitlines()
        if lines and lines[0].lstrip().startswith("%%writefile") and "def agent(" in source:
            matches.append("\n".join(lines[1:]).rstrip() + "\n")
    if len(matches) != 1:
        raise RuntimeError(f"expected one agent writefile cell, found {len(matches)}")
    source = matches[0]
    _validate(source)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(source, encoding="utf-8", newline="\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("notebook", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    extract(args.notebook.resolve(), args.destination.resolve())
    print(args.destination.resolve())
    print(f"bytes={args.destination.stat().st_size}")


if __name__ == "__main__":
    main()
