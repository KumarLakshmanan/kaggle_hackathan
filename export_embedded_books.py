"""Export embedded action tables from an agent as compact research routes."""

from __future__ import annotations

import argparse
import gzip
import importlib.util
import io
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("agent", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()

    spec = importlib.util.spec_from_file_location("embedded_agent", args.agent.resolve())
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import {args.agent}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    names = {
        "primary": "_PRIMARY_ACTIONS",
        "wufang": "_ALTERNATE_ACTIONS",
        "thunder": "_THUNDER_COUNTER_ACTIONS",
        "aastik": "_AASTIK_COUNTER_ACTIONS",
        "seb202": "_SEB_202_COUNTER_ACTIONS",
        "seb210": "_SEB_210_COUNTER_ACTIONS",
    }
    args.destination.mkdir(parents=True, exist_ok=True)
    for label, attribute in names.items():
        actions = getattr(module, attribute)
        output = args.destination / f"{label}.json.gz"
        with output.open("wb") as raw:
            with gzip.GzipFile(fileobj=raw, mode="wb", compresslevel=9, mtime=0) as zipped:
                with io.TextIOWrapper(zipped, encoding="utf-8") as text:
                    json.dump({"actions": actions}, text, sort_keys=True, separators=(",", ":"))
        print(output.resolve())


if __name__ == "__main__":
    main()
