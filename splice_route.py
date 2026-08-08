#!/usr/bin/env python3
"""Create a compact route by replacing selected fields after a turn."""

from __future__ import annotations

import argparse
import copy
import gzip
import io
import json
from pathlib import Path


def read(path: Path) -> dict:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        return json.load(handle)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("base", type=Path)
    parser.add_argument("donor", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--start-step", type=int, required=True)
    parser.add_argument("--fields", nargs="+", choices=("farmer", "hands", "market"), required=True)
    args = parser.parse_args()

    payload = read(args.base)
    donor = read(args.donor)
    actions = payload["actions"]
    donor_actions = donor["actions"]
    if len(actions) != len(donor_actions):
        raise RuntimeError("route lengths differ")
    for step in range(max(0, args.start_step), len(actions)):
        for field in args.fields:
            actions[step][field] = copy.deepcopy(donor_actions[step].get(field, []))
    payload.setdefault("metadata", {})["splice"] = {
        "donor": str(args.donor),
        "start_step": args.start_step,
        "fields": args.fields,
    }
    args.destination.parent.mkdir(parents=True, exist_ok=True)
    with args.destination.open("wb") as raw:
        with gzip.GzipFile(fileobj=raw, mode="wb", compresslevel=9, mtime=0) as zipped:
            with io.TextIOWrapper(zipped, encoding="utf-8") as text:
                json.dump(payload, text, sort_keys=True, separators=(",", ":"))
    print(args.destination.resolve())


if __name__ == "__main__":
    main()
