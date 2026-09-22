"""Read-only refresh of score-descending Kaggriculture code references."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--kaggle", required=True)
    parser.add_argument("--competition", default="kaggriculture")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--page-size", type=int, default=200)
    parser.add_argument("--page", type=int, default=None)
    args = parser.parse_args()

    command = [
            args.kaggle,
            "kernels",
            "list",
            "--competition",
            args.competition,
            "--sort-by",
            "scoreDescending",
            "--page-size",
            str(args.page_size),
            "--format",
            "json",
        ]
    if args.page is not None:
        command.extend(["--page", str(args.page)])
    result = subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    raw = result.stdout
    starts = [index for index in (raw.find("["), raw.find("{")) if index >= 0]
    if not starts:
        raise RuntimeError(f"Kaggle CLI returned no code JSON: {raw[:500]}")
    payload = json.loads(raw[min(starts):])
    rows = payload if isinstance(payload, list) else payload.get("data", [])
    if not isinstance(rows, list):
        raise RuntimeError(f"Expected a code listing list, got {type(rows).__name__}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({
        "rows": len(rows),
        "top": rows[0] if rows else None,
        "output": str(args.output.resolve()),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
