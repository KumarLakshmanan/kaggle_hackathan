"""Read public day-6 state and early market similarity for the gate changes."""

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main() -> None:
    comparison = json.loads((HERE / "live40_comparison.json").read_text(encoding="utf-8"))
    changed = set(comparison["summary"]["rescued_episodes"])
    changed.update(comparison["summary"]["reversed_episodes"])
    records = []
    for row in comparison["rows"]:
        episode = int(row["episode_id"])
        replay = json.loads((HERE / f"episode-{episode}-replay.json").read_text(encoding="utf-8"))
        seat = row["our_live_seat"]
        # Replay frame 144 contains the state after turn 143 and before turn 144.
        observation = replay["steps"][144][seat]["observation"]
        assert int(observation.get("step", 144)) == 144
        farms = observation["farms"]
        early_equal = sum(
            (replay["steps"][t][0].get("action") or {}).get("market")
            == (replay["steps"][t][1].get("action") or {}).get("market")
            for t in range(1, 145)
        )
        own_money = farms[seat]["money"]
        rival_money = farms[1-seat]["money"]
        records.append({
            "episode_id": episode, "team": row["team"],
            "old_pair_margin": row["submitted_pair_margin"],
            "new_pair_margin": row["local_pair_margin"],
            "outcome_change": "rescue" if episode in comparison["summary"]["rescued_episodes"]
                              else "reversal" if episode in comparison["summary"]["reversed_episodes"]
                              else "same",
            "own_cash_day6": own_money, "rival_cash_day6": rival_money,
            "cash_gap_day6": own_money - rival_money,
            "absolute_cash_gap_day6": abs(own_money - rival_money),
            "market_equal_first144": early_equal,
            "physical_equal_day6": (farms[0]["tiles"] == farms[1]["tiles"]
                                    and farms[0]["farmer"] == farms[1]["farmer"]
                                    and farms[0]["hands"] == farms[1]["hands"]),
            "clone_advance_turns": sum(s["clone_advance_turns"] for s in row["seats"]),
        })
    (HERE / "gate_feature_audit.json").write_text(
        json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")
    for row in records:
        if row["episode_id"] in changed:
            print(row)
    print("wrote", len(records), "records")


if __name__ == "__main__":
    main()
