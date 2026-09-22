"""Safely extract complete Kaggriculture agent sources from downloaded notebooks.

This script only parses notebook JSON and Python literals.  It does not execute
any notebook cell or imported agent.  A notebook is accepted when it either
contains a ``%%writefile main.py`` cell or a literal ``SOURCE_BYTES`` payload.
The resulting files are benchmark artifacts, not automatic submissions.
"""

from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
ARCHIVE = ROOT / "kaggle_top_code_2026-09-21"
OUT = ROOT / "kaggle_extracted_agents_2026-09-21"

TARGETS = {
    "aurax7_v7": "aurax7__kaggriculture-shop-router-reactive-v7",
    "goodpjw_melon_2749": "goodpjw2008__kaggriculture-melon-threshold-squeeze-2749",
    "haideptry_master_2965": "haideptry__the-2965-master-hybrid-engine",
    "nathan_pipe16": "nathanjacob__kaggriculture-pipe16-idle-workers",
    "yamakawanin_public_router": "yamakawanin__kaggriculture-adaptive-public-state-multi-route",
    "dmitrii_one_more_wheat": "dmitriigluzdov__kaggriculture-one-more-wheat",
    "tetsutani_demand_timing": "tetsutani__demand-preserving-turn-sale-timing",
}


def _source(cell: dict[str, Any]) -> str:
    return "".join(cell.get("source", []) or [])


def _literal_source(code: str) -> tuple[bytes, str] | None:
    """Return a literal source payload, without evaluating arbitrary code."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return None
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        names = [target.id for target in node.targets if isinstance(target, ast.Name)]
        if "SOURCE_BYTES" not in names:
            continue
        value = node.value
        if not isinstance(value, ast.Call) or len(value.args) != 1:
            continue
        try:
            parts = ast.literal_eval(value.args[0])
        except (ValueError, TypeError, MemoryError):
            continue
        if not isinstance(parts, tuple) or not all(isinstance(part, bytes) for part in parts):
            continue
        return b"".join(parts), "SOURCE_BYTES literal"
    return None


def _extract(notebook: Path) -> tuple[bytes, str, int]:
    data = json.loads(notebook.read_text(encoding="utf-8"))
    for index, cell in enumerate(data.get("cells", [])):
        if cell.get("cell_type") != "code":
            continue
        code = _source(cell)
        if "%%writefile main.py" in code:
            lines = code.splitlines(keepends=True)
            start = next(i for i, line in enumerate(lines) if "%%writefile main.py" in line)
            payload = "".join(lines[start + 1 :]).encode("utf-8")
            return payload, "writefile cell", index
        literal = _literal_source(code)
        if literal is not None:
            payload, mode = literal
            return payload, mode, index
    raise ValueError(f"no complete agent source found in {notebook}")


def _audit(source: bytes) -> dict[str, Any]:
    text = source.decode("utf-8")
    tree = ast.parse(text)
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module or "")
    return {
        "sha256": hashlib.sha256(source).hexdigest(),
        "bytes": len(source),
        "lines": text.count("\n") + 1,
        "imports": sorted(set(imports)),
        "parse_ok": True,
    }


def main() -> None:
    OUT.mkdir(exist_ok=True)
    manifest: dict[str, Any] = {"archive": str(ARCHIVE), "agents": []}
    for name, folder in TARGETS.items():
        matches = sorted((ARCHIVE / folder).glob("*.ipynb"))
        if not matches:
            manifest["agents"].append({"name": name, "status": "missing", "folder": folder})
            continue
        notebook = matches[0]
        try:
            source, mode, cell = _extract(notebook)
            audit = _audit(source)
            destination = OUT / f"{name}.py"
            destination.write_bytes(source)
            manifest["agents"].append(
                {
                    "name": name,
                    "status": "extracted",
                    "folder": folder,
                    "notebook": str(notebook.relative_to(ROOT)),
                    "cell": cell,
                    "mode": mode,
                    "path": str(destination.relative_to(ROOT)),
                    **audit,
                }
            )
        except Exception as exc:
            manifest["agents"].append(
                {"name": name, "status": "error", "folder": folder, "error": repr(exc)}
            )
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
