"""Compare two full replay manifests by physical route identity.

The route identity includes the raw-file digest, action digest, seed, and
configuration digest. Duplicate physical aliases are collapsed only if their
seat results agree.
"""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path


def _route_rows(path: Path) -> dict[tuple, dict]:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    executions = manifest["executions"]
    rows: dict[tuple, dict] = {}
    for route in manifest["routes"]:
        if route.get("status") != "ready":
            continue
        keys = route.get("execution_keys") or {}
        games = [executions.get(keys.get(str(seat), "")) for seat in (0, 1)]
        if any(game is None for game in games):
            continue
        if any(game.get("candidate_status") != "DONE" or game.get("opponent_status") != "DONE" for game in games):
            continue
        identity = (
            route["raw_file_sha256"], route["action_sha256"],
            int(route["seed"]), route["configuration_sha256"],
        )
        value = {
            "path": route["path"],
            "team": route.get("team"),
            "seed": route["seed"],
            "pair_margin": sum(float(game["margin"]) for game in games),
            "candidate_cash": sum(float(game["candidate_reward"]) for game in games),
            "opponent_cash": sum(float(game["opponent_reward"]) for game in games),
            "seat_margins": [float(game["margin"]) for game in games],
        }
        if identity in rows and rows[identity]["seat_margins"] != value["seat_margins"]:
            raise ValueError(f"Conflicting duplicate route identity at {route['path']}")
        rows[identity] = value
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("baseline", type=Path)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--limit", type=int, default=30)
    args = parser.parse_args()
    base = _route_rows(args.baseline)
    test = _route_rows(args.candidate)
    joined = []
    for identity in sorted(base.keys() & test.keys()):
        a, b = base[identity], test[identity]
        joined.append({
            "path": b["path"], "team": b["team"], "seed": b["seed"],
            "base": a["pair_margin"], "test": b["pair_margin"],
            "margin_delta": b["pair_margin"] - a["pair_margin"],
            "own_cash_delta": b["candidate_cash"] - a["candidate_cash"],
            "opponent_cash_delta": b["opponent_cash"] - a["opponent_cash"],
            "base_seats": a["seat_margins"], "test_seats": b["seat_margins"],
        })
    counts = Counter(("W" if row["base"] > 0 else "L", "W" if row["test"] > 0 else "L") for row in joined)
    print(f"joined={len(joined)} baseline={len(base)} candidate={len(test)} transitions={dict(counts)}")
    print("\nOutcome flips:")
    for row in sorted((r for r in joined if (r["base"] > 0) != (r["test"] > 0)), key=lambda r: r["margin_delta"]):
        print(json.dumps(row, ensure_ascii=False))
    print("\nLargest margin regressions:")
    for row in sorted((r for r in joined if r["margin_delta"] < 0), key=lambda r: r["margin_delta"])[:args.limit]:
        print(json.dumps(row, ensure_ascii=False))


if __name__ == "__main__":
    main()
