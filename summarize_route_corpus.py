#!/usr/bin/env python3
"""Build one deduplicated summary from compact replay-route directories."""

from __future__ import annotations

import argparse
import gzip
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("directories", nargs="+", type=Path)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()

    rows = []
    seen = set()
    for directory in args.directories:
        for path in sorted(directory.glob("*.json.gz")):
            with gzip.open(path, "rt", encoding="utf-8") as handle:
                metadata = dict(json.load(handle).get("metadata", {}))
            digest = metadata.get("action_sha256")
            if not digest or digest in seen:
                continue
            seen.add(digest)
            metadata["path"] = str(path.resolve())
            rows.append(metadata)
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(json.dumps(rows, indent=2, ensure_ascii=False) + "\n")
    print(f"routes={len(rows)} summary={args.summary.resolve()}")


if __name__ == "__main__":
    main()
