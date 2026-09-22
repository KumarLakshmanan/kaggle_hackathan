"""Extract complete ``main.py`` payloads from the live Kaggle notebook pull."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
from pathlib import Path

from extract_kaggle_agents import _extract


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    rows = []
    for notebook in sorted(args.archive.rglob("*.ipynb")):
        try:
            source_bytes, mode, cell = _extract(notebook)
            source = source_bytes.decode("utf-8")
            ast.parse(source)
            if not re.search(r"(?m)^\s*def\s+(?:agent|kaggle_submission_agent)\s*\(", source):
                rows.append({"notebook": str(notebook), "status": "no_agent"})
                continue
            digest = hashlib.sha256(str(notebook).encode("utf-8")).hexdigest()[:12]
            name = re.sub(r"[^A-Za-z0-9_.-]+", "_", notebook.parent.name)
            destination = args.output / f"{name}__{digest}.py"
            destination.write_bytes(source_bytes)
            rows.append({
                "notebook": str(notebook),
                "source": str(destination),
                "status": "extracted",
                "mode": mode,
                "cell": cell,
                "bytes": len(source_bytes),
                "lines": source.count("\n") + 1,
            })
        except Exception as error:  # noqa: BLE001 - audit should continue
            rows.append({"notebook": str(notebook), "status": "error", "error": repr(error)})
    manifest = {"archive": str(args.archive.resolve()), "agents": rows}
    manifest["extracted"] = sum(row.get("status") == "extracted" for row in rows)
    (args.output / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(json.dumps({"notebooks": len(rows), "extracted": manifest["extracted"]}))


if __name__ == "__main__":
    main()
