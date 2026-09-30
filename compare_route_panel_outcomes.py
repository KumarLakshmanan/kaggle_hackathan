"""Compare route-panel benchmarks by exact route identity, never by seed alone."""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path


def _load(path: Path) -> tuple[dict, dict[tuple, dict]]:
    report = json.loads(path.read_text(encoding="utf-8"))
    routes: dict[tuple, dict] = {}
    for row in report["rows"]:
        identity = (
            str(Path(row["opponent_path"]).resolve()).casefold(),
            row["action_sha256"],
            int(row["seed"]),
            int(row["source_seat"]),
        )
        games = sorted(row["games"], key=lambda game: int(game["candidate_seat"]))
        if len(games) != 2 or [int(game["candidate_seat"]) for game in games] != [0, 1]:
            raise ValueError(f"Route missing one candidate seat: {row['opponent_path']}")
        if any(game["candidate_status"] != "DONE" or game["opponent_status"] != "DONE" for game in games):
            raise ValueError(f"Incomplete route: {row['opponent_path']}")
        margins = [float(game["margin"]) for game in games]
        value = {
            "path": row["opponent_path"],
            "team": row.get("team"),
            "seed": int(row["seed"]),
            "margins": margins,
            "pair_margin": sum(margins),
            "candidate_cash": sum(float(game["candidate_reward"]) for game in games),
            "opponent_cash": sum(float(game["opponent_reward"]) for game in games),
            "telemetry": [game.get("candidate_telemetry") or {} for game in games],
        }
        if identity in routes:
            raise ValueError(f"Duplicate route identity: {row['opponent_path']}")
        routes[identity] = value
    return report, routes


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("baseline", type=Path)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--limit", type=int, default=30)
    args = parser.parse_args()
    base_report, baseline = _load(args.baseline)
    test_report, candidate = _load(args.candidate)
    if base_report.get("engine_version") != test_report.get("engine_version"):
        raise ValueError("Engine versions differ")
    if base_report.get("summary_sha256") != test_report.get("summary_sha256"):
        raise ValueError("Route-summary digest differs")
    joined = []
    for identity in sorted(baseline.keys() & candidate.keys()):
        a, b = baseline[identity], candidate[identity]
        joined.append({
            "path": b["path"], "team": b["team"], "seed": b["seed"],
            "baseline": a["margins"], "candidate": b["margins"],
            "baseline_pair": a["pair_margin"], "candidate_pair": b["pair_margin"],
            "pair_delta": b["pair_margin"] - a["pair_margin"],
            "own_cash_delta": b["candidate_cash"] - a["candidate_cash"],
            "opponent_cash_delta": b["opponent_cash"] - a["opponent_cash"],
            "candidate_telemetry": b["telemetry"],
        })
    transitions = Counter(
        ("W" if row["baseline_pair"] > 0 else "L", "W" if row["candidate_pair"] > 0 else "L")
        for row in joined
    )
    seat_wins = (
        sum(margin > 0 for row in joined for margin in row["baseline"]),
        sum(margin > 0 for row in joined for margin in row["candidate"]),
    )
    print(f"joined={len(joined)} baseline_routes={len(baseline)} candidate_routes={len(candidate)} "
          f"transitions={dict(transitions)} seat_wins={seat_wins[0]}->{seat_wins[1]}")
    print("Changed margins:")
    for row in sorted((row for row in joined if row["pair_delta"]),
                      key=lambda row: row["pair_delta"])[:args.limit]:
        print(json.dumps(row, ensure_ascii=True))


if __name__ == "__main__":
    main()
