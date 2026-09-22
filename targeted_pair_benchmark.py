"""Small local benchmark helper for selected extracted replay routes."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from paired_benchmark import run_game, summarize


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--seeds", nargs="+", type=int, required=True)
    parser.add_argument("--candidate-override", action="append", default=[])
    parser.add_argument("--json-out", type=Path, required=True)
    args = parser.parse_args()
    overrides = {}
    for raw in args.candidate_override:
        if "=" not in raw:
            raise ValueError(f"invalid override {raw!r}; expected NAME=JSON")
        name, value = raw.split("=", 1)
        try:
            overrides[name] = json.loads(value)
        except json.JSONDecodeError:
            overrides[name] = value
    entries = json.loads(args.summary.read_text(encoding="utf-8"))
    by_seed = {}
    for entry in entries:
        by_seed.setdefault(int(entry["seed"]), entry)
    rows = []
    for seed in args.seeds:
        entry = by_seed[seed]
        opponent = f"rawroute:{Path(entry['path']).resolve()}"
        for seat in (0, 1):
            row = run_game(
                candidate=args.candidate,
                opponent=opponent,
                seed=seed,
                candidate_seat=seat,
                debug=False,
                capture_step=None,
                candidate_overrides=overrides,
            )
            row.update({"episode_id": entry["episode_id"], "team": entry["team"]})
            rows.append(row)
            print(
                f"seed={seed} seat={seat} margin={row['margin']:+.0f} "
                f"result={row['result']}",
                flush=True,
            )
    payload = {"candidate": args.candidate, "rows": rows, "summary": summarize(rows)}
    args.json_out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print("SUMMARY " + json.dumps(payload["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
