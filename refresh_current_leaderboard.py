"""Read-only refresh of the Kaggriculture leaderboard JSON."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--kaggle", required=True)
    parser.add_argument("--competition", default="kaggriculture")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--page-size", type=int, default=200)
    parser.add_argument(
        "--pages",
        type=int,
        default=1,
        help="Number of leaderboard pages to fetch (Kaggle allows up to 200 rows per page).",
    )
    args = parser.parse_args()

    rows = []
    page_token = None
    pages_fetched = 0
    for _ in range(max(1, int(args.pages))):
        command = [
            args.kaggle,
            "competitions",
            "leaderboard",
            args.competition,
            "--show",
            "--format",
            "json",
            "--page-size",
            str(args.page_size),
            "-q",
        ]
        if page_token:
            command.extend(["--page-token", page_token])
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        raw = result.stdout
        start = raw.find("[")
        if start < 0:
            raise RuntimeError(f"Kaggle CLI returned no leaderboard JSON: {raw[:500]}")
        page_rows = json.loads(raw[start:].replace("NaN", "null"))
        if not isinstance(page_rows, list):
            raise RuntimeError(f"Expected a leaderboard list, got {type(page_rows).__name__}")
        rows.extend(page_rows)
        pages_fetched += 1
        token_match = re.search(r"Next Page Token\s*=\s*(\S+)", raw[:start])
        page_token = token_match.group(1) if token_match else None
        if not page_token or not page_rows:
            break

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({
        "rows": len(rows),
        "pages_fetched": pages_fetched,
        "next_page_available": bool(page_token),
        "top": rows[0] if rows else None,
        "output": str(args.output.resolve()),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
