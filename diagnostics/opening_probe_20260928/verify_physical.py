"""Observe only the first four turns; do not collect full-game outcomes."""
from pathlib import Path
import copy
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from paired_benchmark import _load_agent, make, engine_version


def snapshot(path, fixture, seat):
    candidate, _ = _load_agent(str(path), "opening_physical")
    opponent, _ = _load_agent("rawroute:" + fixture["path"], "opening_rival")
    captures = {}
    def wrapped(obs, config):
        if int(obs["step"]) in (1, 3):
            captures[int(obs["step"])] = copy.deepcopy(dict(obs))
        return candidate(obs, config)
    agents = [wrapped, opponent] if seat == 0 else [opponent, wrapped]
    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": int(fixture["seed"])})
    env.reset(2)
    runner = env._Environment__agent_runner(agents)
    for _ in range(4):
        actions, logs = runner.act()
        env.step(actions, logs)
    assert set(captures) == {1, 3}
    assert len(env.steps) == 5 and all(s.status == "ACTIVE" for s in env.state)
    return captures


def physical(obs, arm, candidate):
    seat = int(obs["player"])
    farm = copy.deepcopy(obs["farms"][seat])
    private = copy.deepcopy(obs["private"])
    farm.pop("money")
    if arm == "v43" and candidate:
        assert len(farm["hands"]) == 4
        assert all(not bag for bag in private["inventories"][3:])
        farm["hands"] = farm["hands"][:2]
        farm["hires_today"] -= 2
        private["inventories"] = private["inventories"][:3]
    return {"farm": farm, "private": private}


def main():
    assert engine_version == "1.32.7"
    manifest_path = ROOT / "diagnostics/current_top20_20260927_172258/manifest.json"
    assert hashlib.sha256(manifest_path.read_bytes()).hexdigest() == "4cf340e5ac28eec35dc202a459c3910cee8da1c692324b41ebd3f619f70230ea"
    fixtures = [r for r in json.loads(manifest_path.read_text(encoding="utf-8"))["rows"]
                if r["team"] in ("DECEM", "Boey", "Vadim Vasilenko", "DSM", "Majkel1337")]
    records = json.loads((HERE / "candidates.json").read_text())
    results = []
    for record in records:
        candidate_path = Path(record["path"])
        parent_path = ROOT / record["source"]
        assert hashlib.sha256(candidate_path.read_bytes()).hexdigest() == record["sha256"]
        assert hashlib.sha256(parent_path.read_bytes()).hexdigest() == record["source_sha256"]
        for fixture in fixtures:
            for seat in (0, 1):
                parent = snapshot(parent_path, fixture, seat)
                candidate = snapshot(candidate_path, fixture, seat)
                p = physical(parent[3], record["arm"], False)
                c = physical(candidate[3], record["arm"], True)
                row = {"arm": record["arm"], "team": fixture["team"], "seat": seat,
                       "physical_equal_step3": p == c,
                       "parent_cash_step3": parent[3]["farms"][seat]["money"],
                       "candidate_cash_step3": candidate[3]["farms"][seat]["money"],
                       "candidate_step1": candidate[1]}
                if p != c:
                    row.update(parent_physical=p, candidate_physical=c)
                results.append(row)
                print(record["arm"], fixture["team"], seat, p == c, flush=True)
    arm_observations = {}
    shared = True
    for row in results:
        obs = copy.deepcopy(row["candidate_step1"])
        obs.pop("remainingOverageTime", None)
        key = (row["team"], row["seat"])
        if key in arm_observations:
            shared = shared and arm_observations[key] == obs
        else:
            arm_observations[key] = obs
    payload = {"results": results, "physical_gate_pass": all(r["physical_equal_step3"] for r in results),
               "common_step1_observations": shared, "candidate_hashes": records,
               "interpretation": "First-four-turn physical verification only; no complete-game outcomes."}
    (HERE / "physical.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k:payload[k] for k in ("physical_gate_pass", "common_step1_observations")}))


if __name__ == "__main__":
    main()
