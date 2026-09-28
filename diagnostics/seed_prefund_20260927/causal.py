"""Compare matched old/new native traces for the three activated top-20 losses."""

from collections import Counter
import gzip
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
DIAG = HERE.parent / "new_main_failure_diagnosis_20260927"
CASES = {
    "Boey": (DIAG / "trace_top20_Boey_s0.json.gz", HERE / "trace_prefund_Boey_s0.json.gz"),
    "Vadim": (DIAG / "trace_top20_Vadim_s0.json.gz", HERE / "trace_prefund_Vadim_s0.json.gz"),
    "DECEM": (HERE / "trace_base_DECEM_s0.json.gz", HERE / "trace_prefund_DECEM_s0.json.gz"),
}


def load(path):
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        return json.load(fh)


def tiles(obs, seat):
    result = Counter()
    for row in obs["farms"][seat]["tiles"]:
        for tile in row:
            if isinstance(tile, dict):
                name = tile.get("crop") or tile.get("animal")
                if name:
                    result[name] += 1
    return dict(result)


def snap(trace, step):
    obs = trace["traces"][0][step]["observation"]
    own = obs["farms"][0]
    rival = obs["farms"][1]
    return {"step": step, "cash": [own["money"], rival["money"]],
            "margin": own["money"] - rival["money"],
            "seed": {k: v for k, v in obs["private"]["seeds"].items() if v},
            "own_tiles": tiles(obs, 0), "rival_tiles": tiles(obs, 1),
            "shops": obs["town"]["unlocked_shops"]}


def main():
    rows = []
    for name, (base_path, candidate_path) in CASES.items():
        old, new = load(base_path), load(candidate_path)
        assert old["candidate_seat"] == new["candidate_seat"] == 0
        assert old["seed"] == new["seed"]
        assert old["opponent"] == new["opponent"]
        old_records, new_records = old["traces"][0], new["traces"][0]
        changed_actions = [i for i in range(719) if old_records[i]["action"] != new_records[i]["action"]]
        changed_worker = [i for i in range(719)
                          if {k: old_records[i]["action"].get(k) for k in ("farmer", "hands")}
                          != {k: new_records[i]["action"].get(k) for k in ("farmer", "hands")}]
        first = changed_actions[0]
        assert sorted(map(str, old_records[first]["action"]["market"])) == sorted(map(str, new_records[first]["action"]["market"]))
        milestones = sorted({0, 144, first, first+1, first+24, 216, 288, 360,
                             432, 504, 576, 648, 718})
        milestones = [m for m in milestones if 0 <= m <= 718]
        rows.append({
            "team": name, "seed": old["seed"], "base": str(base_path), "candidate": str(candidate_path),
            "base_final_cash": [old["candidate_reward"], old["opponent_reward"]],
            "candidate_final_cash": [new["candidate_reward"], new["opponent_reward"]],
            "base_margin": old["margin"], "candidate_margin": new["margin"],
            "delta_own": new["candidate_reward"] - old["candidate_reward"],
            "delta_rival": new["opponent_reward"] - old["opponent_reward"],
            "first_changed_action": first,
            "base_market_at_first": old_records[first]["action"]["market"],
            "candidate_market_at_first": new_records[first]["action"]["market"],
            "total_changed_actions": len(changed_actions),
            "first_changed_worker_action": changed_worker[0] if changed_worker else None,
            "total_changed_worker_actions": len(changed_worker),
            "milestones": [{"step": step, "base": snap(old, step), "candidate": snap(new, step)}
                           for step in milestones],
        })
    (HERE / "causal.json").write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
    for row in rows:
        print(row["team"], row["first_changed_action"], "delta", row["delta_own"],
              row["delta_rival"], "workers", row["first_changed_worker_action"],
              "changed worker actions", row["total_changed_worker_actions"])


if __name__ == "__main__":
    main()
