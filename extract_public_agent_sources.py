#!/usr/bin/env python3
"""Extract literal agent source strings from downloaded public notebooks.

Only literal assignments that parse as Python and define ``agent`` are
accepted.  The output manifest preserves the originating Kaggle reference.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path


ROOT = Path("pipelines/kaggle_public")
OUTPUT = Path("pipelines/kaggle_public_agents")
PREFERRED = (
    "MAIN_SOURCE",
    "AGENT_SOURCE",
    "AGENT_CODE",
    "agent_code",
    "agent_export_code",
    "_TOP_AGENT_SOURCE",
    "V22_SOURCE",
    "PREMIUM_SOURCE",
)


def chunks(path: Path) -> list[str]:
    if path.suffix == ".py":
        return [path.read_text(errors="replace")]
    notebook = json.loads(path.read_text())
    return [
        "".join(cell.get("source", []))
        if isinstance(cell.get("source"), list)
        else cell.get("source", "")
        for cell in notebook.get("cells", [])
        if cell.get("cell_type") == "code"
    ]


def literal_assignments(source: str) -> list[tuple[str, str]]:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []
    found: list[tuple[str, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        value = node.value
        if not isinstance(value, ast.Constant) or not isinstance(value.value, str):
            continue
        for target in targets:
            if isinstance(target, ast.Name):
                found.append((target.id, value.value))
    return found


def is_agent(source: str) -> bool:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return False
    return any(isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "agent" for node in tree.body)


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    rows = []
    for folder in sorted(ROOT.iterdir()):
        if not folder.is_dir():
            continue
        metadata_path = folder / "kernel-metadata.json"
        metadata = json.loads(metadata_path.read_text()) if metadata_path.exists() else {}
        candidates: list[tuple[int, int, str, str, Path]] = []
        for path in sorted(folder.iterdir()):
            if path.suffix not in {".py", ".ipynb"}:
                continue
            for cell_index, source in enumerate(chunks(path)):
                for variable, value in literal_assignments(source):
                    if variable not in PREFERRED or not is_agent(value):
                        continue
                    candidates.append((PREFERRED.index(variable), -len(value), variable, value, path))
        if not candidates:
            continue
        _, _, variable, source, origin = min(candidates)
        output = OUTPUT / f"{folder.name}.py"
        output.write_text(source.rstrip() + "\n")
        rows.append(
            {
                "kaggleRef": metadata.get("id"),
                "origin": str(origin),
                "variable": variable,
                "bytes": output.stat().st_size,
                "path": str(output.resolve()),
            }
        )
    manifest = OUTPUT / "manifest.json"
    manifest.write_text(json.dumps(rows, indent=2) + "\n")
    print(f"agents={len(rows)} manifest={manifest}")


if __name__ == "__main__":
    main()
