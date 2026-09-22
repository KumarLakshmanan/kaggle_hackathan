"""Build a verify_main_panel-compatible summary from compact route files."""

from __future__ import annotations

import argparse
import gzip
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--routes", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = []
    for path in sorted(args.routes.glob("*.json.gz")):
        with gzip.open(path, "rt", encoding="utf-8") as handle:
            payload = json.load(handle)
        metadata = payload.get("metadata", {})
        rows.append({
            "path": str(path.resolve()),
            "team": metadata.get("opponent_team", metadata.get("team")),
            "episode_id": metadata.get("episode_id"),
            "seed": metadata.get("seed"),
            "source_seat": metadata.get("source_seat"),
            "action_sha256": metadata.get("action_sha256"),
        })
    args.output.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"routes": len(rows), "output": str(args.output.resolve())}))


if __name__ == "__main__":
    main()
