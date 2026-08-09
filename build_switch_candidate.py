#!/usr/bin/env python3
"""Build a test agent that keeps V36's opening and switches books later.

This is deliberately a small experiment helper.  The generated agent keeps
the public-state legality, weed recovery, market safety, and terminal logic
from ``main.py``; only the action book after ``--threshold`` is replaced.
"""

from __future__ import annotations

import argparse
import gzip
import json
import pprint
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def build(route: Path, destination: Path, threshold: int) -> None:
    text = (ROOT / "main.py").read_text(encoding="utf-8")
    with gzip.open(route.resolve(), "rt", encoding="utf-8") as handle:
        actions = json.load(handle)["actions"]
    literal = pprint.pformat(actions, width=120, compact=True, sort_dicts=False)
    marker = "_BOOK_MODE = {0: \"kakuteki\", 1: \"kakuteki\"}\n"
    if marker not in text:
        raise RuntimeError("main.py book marker not found")
    insert = (
        "_SWITCH_ACTIONS = " + literal + "\n"
        "_SWITCH_THRESHOLD = " + str(int(threshold)) + "\n\n"
    )
    text = text.replace(marker, insert + marker, 1)
    needle = "    global _ACTIONS\n"
    replacement = (
        "    global _ACTIONS\n"
        "    if step >= _SWITCH_THRESHOLD:\n"
        "        _ACTIONS = _SWITCH_ACTIONS\n"
        "        return\n"
    )
    text = text.replace(needle, replacement, 1)
    text = text.replace(
        "Transparent V36 Kaggriculture leader-meta agent.",
        "Transparent V37 opening-preserving switch experiment.",
        1,
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(text, encoding="utf-8", newline="\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--route", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--threshold", type=int, default=144)
    args = parser.parse_args()
    build(args.route, args.output, args.threshold)
    print(args.output.resolve())


if __name__ == "__main__":
    main()
