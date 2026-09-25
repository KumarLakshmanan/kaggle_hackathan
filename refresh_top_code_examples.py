"""Pull public Kaggriculture code examples listed by the Kaggle API.

The utility only calls ``kernels list`` and ``kernels pull``.  It never calls
competition submission endpoints.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path


def _safe(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("-")[:90] or "kernel"


def _json_from_cli(text: str):
    starts = [index for index in (text.find("["), text.find("{")) if index >= 0]
    if not starts:
        raise RuntimeError(f"Kaggle CLI returned no JSON: {text[:500]}")
    return json.loads(text[min(starts) :])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--kaggle", required=True)
    parser.add_argument("--listing", type=Path)
    parser.add_argument("--competition")
    parser.add_argument("--page", type=int, default=1)
    parser.add_argument("--page-size", type=int, default=20)
    parser.add_argument("--sort-by", default="scoreDescending")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=100)
    args = parser.parse_args()

    if args.listing is not None:
        raw = args.listing.read_text(encoding="utf-8-sig")
    else:
        if not args.competition:
            parser.error("provide either --listing or --competition")
        command = [
            args.kaggle,
            "kernels",
            "list",
            "--competition",
            args.competition,
            "--sort-by",
            args.sort_by,
            "--page",
            str(args.page),
            "--page-size",
            str(args.page_size),
            "--format",
            "json",
        ]
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        raw = result.stdout
    listing = _json_from_cli(raw)
    rows = listing[: max(1, int(args.limit))]
    args.output.mkdir(parents=True, exist_ok=True)
    pulled = []
    for index, row in enumerate(rows, 1):
        ref = str(row["ref"])
        destination = args.output / f"{index:03d}-{_safe(ref.replace('/', '__'))}"
        destination.mkdir(parents=True, exist_ok=True)
        result = subprocess.run(
            [args.kaggle, "kernels", "pull", ref, "-p", str(destination), "-m"],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        ok = result.returncode == 0
        pulled.append({
            "rank": index,
            "ref": ref,
            "title": row.get("title"),
            "author": row.get("author"),
            "lastRunTime": row.get("lastRunTime"),
            "totalVotes": row.get("totalVotes"),
            "path": str(destination.resolve()),
            "ok": ok,
            "stderr": result.stderr[-500:] if not ok else "",
        })
        print(f"[{index:03d}/{len(rows):03d}] {'ok' if ok else 'FAILED'} {ref}", flush=True)

    manifest = args.output / "manifest.json"
    manifest.write_text(json.dumps(pulled, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({
        "requested": len(rows),
        "pulled": sum(item["ok"] for item in pulled),
        "failed": sum(not item["ok"] for item in pulled),
        "manifest": str(manifest.resolve()),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
