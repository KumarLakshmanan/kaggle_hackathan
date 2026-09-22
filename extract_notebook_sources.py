"""Extract concatenated code cells from downloaded Kaggle notebooks.

This is a read-only analysis artifact: it parses notebook JSON and never
executes cells.  Sources are benchmark candidates only.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent
ARCHIVE = ROOT / "kaggle_top_code_2026-09-21"
OUT = ROOT / "kaggle_notebook_sources_2026-09-21"


def main() -> None:
    OUT.mkdir(exist_ok=True)
    rows = []
    for notebook in sorted(ARCHIVE.rglob("*.ipynb")):
        try:
            payload = json.loads(notebook.read_text(encoding="utf-8"))
            source = "\n\n".join(
                "".join(cell.get("source", []) or [])
                for cell in payload.get("cells", [])
                if cell.get("cell_type") == "code"
            )
            if not source.strip():
                continue
            digest = hashlib.sha256(str(notebook).encode("utf-8")).hexdigest()[:12]
            name = re.sub(r"[^A-Za-z0-9_.-]+", "_", notebook.parent.name)
            destination = OUT / f"{name}__{digest}.py"
            destination.write_text(source, encoding="utf-8")
            rows.append(
                {
                    "notebook": str(notebook.relative_to(ROOT)),
                    "source": str(destination.relative_to(ROOT)),
                    "bytes": len(source.encode("utf-8")),
                    "lines": source.count("\n") + 1,
                    "has_agent": bool(re.search(r"(?m)^\s*def\s+agent\s*\(", source)),
                    "has_writefile": "%%writefile" in source,
                }
            )
        except Exception as error:  # noqa: BLE001 - preserve archive progress
            rows.append({"notebook": str(notebook.relative_to(ROOT)), "error": repr(error)})
    manifest = {
        "archive": str(ARCHIVE),
        "sources": rows,
        "code_cell_notebooks": sum("source" in row for row in rows),
        "agent_candidates": sum(row.get("has_agent", False) for row in rows),
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps({key: manifest[key] for key in ("code_cell_notebooks", "agent_candidates")}, sort_keys=True))


if __name__ == "__main__":
    main()

