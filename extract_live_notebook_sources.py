"""Extract code cells from a freshly pulled Kaggle notebook corpus.

The notebook JSON is parsed as data.  Cells are never executed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    rows = []
    for notebook in sorted(args.archive.rglob("*.ipynb")):
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
            destination = args.output / f"{name}__{digest}.py"
            destination.write_text(source, encoding="utf-8")
            rows.append({
                "notebook": str(notebook),
                "source": str(destination),
                "bytes": len(source.encode("utf-8")),
                "lines": source.count("\n") + 1,
                "has_agent": bool(re.search(r"(?m)^\s*def\s+agent\s*\(", source)),
                "has_writefile": "%%writefile" in source,
            })
        except Exception as error:  # noqa: BLE001 - preserve corpus progress
            rows.append({"notebook": str(notebook), "error": repr(error)})
    manifest = {
        "archive": str(args.archive.resolve()),
        "sources": rows,
        "code_cell_notebooks": sum("source" in row for row in rows),
        "agent_candidates": sum(row.get("has_agent", False) for row in rows),
    }
    (args.output / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(json.dumps({key: manifest[key] for key in ("code_cell_notebooks", "agent_candidates")}))


if __name__ == "__main__":
    main()
