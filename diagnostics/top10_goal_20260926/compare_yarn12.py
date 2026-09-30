"""Match route-12 treatment to the frozen incumbent by exact saved route."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "diagnostics" / "top100_current_2026-09-25"
OUT = Path(__file__).resolve().parent


def main() -> None:
    baseline = json.loads((SOURCE / "main_100routes.json").read_text(encoding="utf-8"))
    treatment = json.loads((OUT / "yarn12_28routes.json").read_text(encoding="utf-8"))
    probes = json.loads((SOURCE / "shop_pair_probe.json").read_text(encoding="utf-8"))
    shops = {(int(p["episode_id"]), int(p["seat"])): tuple(p["shops"]) for p in probes}
    base_by_key = {(r["action_sha256"], int(r["seed"]), int(r["source_seat"])): r for r in baseline["rows"]}
    totals = {"yarn": {"routes": 0, "base_wins": 0, "treatment_wins": 0, "rescued": 0, "reversed": 0,
                       "own_cash_delta": 0, "rival_cash_delta": 0},
              "control": {"routes": 0, "base_wins": 0, "treatment_wins": 0, "rescued": 0, "reversed": 0,
                          "own_cash_delta": 0, "rival_cash_delta": 0}}
    details = []
    for row in treatment["rows"]:
        key = (row["action_sha256"], int(row["seed"]), int(row["source_seat"]))
        base = base_by_key[key]
        assert row["opponent_path"] == base["opponent_path"]
        assert [g["candidate_seat"] for g in row["games"]] == [g["candidate_seat"] for g in base["games"]]
        assert all(g["candidate_status"] == g["opponent_status"] == "DONE" for g in row["games"])
        pair = shops[(int(row["episode_id"]), 0)]
        cohort = "yarn" if "YARN_STORE" in pair else "control"
        selected = sum(g["candidate_telemetry"].get("selected", 0) for g in row["games"])
        assert selected in (0, 2), (row["team"], selected)
        if cohort == "control":
            assert selected == 0
        own_delta = sum(c["candidate_reward"] - b["candidate_reward"] for b, c in zip(base["games"], row["games"]))
        rival_delta = sum(c["opponent_reward"] - b["opponent_reward"] for b, c in zip(base["games"], row["games"]))
        base_win = base["pair_margin"] > 0
        treatment_win = row["pair_margin"] > 0
        if selected == 0:
            assert own_delta == rival_delta == 0 and base["pair_margin"] == row["pair_margin"]
        t = totals[cohort]
        t["routes"] += 1
        t["base_wins"] += base_win
        t["treatment_wins"] += treatment_win
        t["rescued"] += not base_win and treatment_win
        t["reversed"] += base_win and not treatment_win
        t["own_cash_delta"] += own_delta
        t["rival_cash_delta"] += rival_delta
        details.append({"team": row["team"], "episode_id": row["episode_id"], "shops": pair,
                        "cohort": cohort, "base_margin": base["pair_margin"],
                        "treatment_margin": row["pair_margin"], "own_cash_delta": own_delta,
                        "rival_cash_delta": rival_delta, "selected": selected})

    assert totals["yarn"]["routes"] == 22 and totals["control"]["routes"] == 6
    payload = {"totals": totals, "details": details}
    (OUT / "yarn12_comparison.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(totals, indent=2))
    for d in details:
        if d["cohort"] == "yarn":
            print(f"{d['team']}: {d['base_margin']/2:+.0f} -> {d['treatment_margin']/2:+.0f}, "
                  f"own {d['own_cash_delta']/2:+.0f}, rival {d['rival_cash_delta']/2:+.0f}, {','.join(d['shops'])}")


if __name__ == "__main__":
    main()
