"""Extract every complete ``main.py`` payload from the Kaggle archive.

Notebook cells are not concatenated blindly: a Kaggle ``%%writefile`` or
literal source payload is selected, then parsed before it becomes a candidate.
No notebook code is executed.
"""

from __future__ import annotations

import ast
import hashlib
import json
import re
from pathlib import Path

from extract_kaggle_agents import _extract


ROOT = Path(__file__).resolve().parent
ARCHIVE = ROOT / "kaggle_top_code_2026-09-21"
OUT = ROOT / "kaggle_complete_agents_2026-09-21"


def main() -> None:
    OUT.mkdir(exist_ok=True)
    rows = []
    for notebook in sorted(ARCHIVE.rglob("*.ipynb")):
        try:
            source_bytes, mode, cell = _extract(notebook)
            source = source_bytes.decode("utf-8")
            ast.parse(source)
            if not re.search(r"(?m)^\s*def\s+(?:agent|kaggle_submission_agent)\s*\(", source):
                rows.append({"notebook": str(notebook.relative_to(ROOT)), "status": "no_agent"})
                continue
            digest = hashlib.sha256(str(notebook).encode("utf-8")).hexdigest()[:12]
            name = re.sub(r"[^A-Za-z0-9_.-]+", "_", notebook.parent.name)
            destination = OUT / f"{name}__{digest}.py"
            destination.write_bytes(source_bytes)
            rows.append(
                {
                    "notebook": str(notebook.relative_to(ROOT)),
                    "source": str(destination.relative_to(ROOT)),
                    "status": "extracted",
                    "mode": mode,
                    "cell": cell,
                    "bytes": len(source_bytes),
                    "lines": source.count("\n") + 1,
                }
            )
        except Exception as error:  # noqa: BLE001 - archive audit should continue
            rows.append({"notebook": str(notebook.relative_to(ROOT)), "status": "error", "error": repr(error)})
    manifest = {
        "archive": str(ARCHIVE),
        "agents": rows,
        "extracted": sum(row.get("status") == "extracted" for row in rows),
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps({"notebooks": len(rows), "extracted": manifest["extracted"]}, sort_keys=True))


if __name__ == "__main__":
    main()

