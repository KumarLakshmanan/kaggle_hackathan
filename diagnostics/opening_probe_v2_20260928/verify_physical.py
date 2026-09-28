"""Full observation parity for all incumbent branches before outcome tests."""
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
import copy
import gc
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from diagnostics.opening_probe_20260928.verify_physical import physical
from paired_benchmark import _load_agent, make


def snapshot(path, fixture, seat):
    candidate, candidate_timing = _load_agent(str(path), "opening_physical")
    opponent, opponent_timing = _load_agent("rawroute:" + fixture["path"], "opening_rival")
    try:
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
    finally:
        for timed in (candidate_timing, opponent_timing):
            if timed is not None and timed.module_name:
                sys.modules.pop(timed.module_name, None)


def clean(obs):
    obs = copy.deepcopy(obs)
    obs.pop("remainingOverageTime", None)
    return obs


def check(job):
    record, fixture, seat = job
    assert hashlib.sha256(Path(record["path"]).read_bytes()).hexdigest() == record["sha256"]
    assert hashlib.sha256((ROOT / record["source"]).read_bytes()).hexdigest() == record["source_sha256"]
    parent = snapshot(ROOT / record["source"], fixture, seat)
    gc.collect()
    candidate = snapshot(Path(record["path"]), fixture, seat)
    gc.collect()
    if record["arm"] == "4ee":
        p, c = clean(parent[3]), clean(candidate[3])
    else:
        p, c = physical(parent[3], "v43", False), physical(candidate[3], "v43", True)
    row = {"arm": record["arm"], "candidate_sha256": record["sha256"],
           "fixture_id": fixture["fixture_id"], "team": fixture["team"],
           "seat": seat, "physical_equal_step3": p == c,
           "candidate_step1": clean(candidate[1]),
           "parent_cash_step3": parent[3]["farms"][seat]["money"],
           "candidate_cash_step3": candidate[3]["farms"][seat]["money"]}
    if p != c:
        row.update(parent_step3=p, candidate_step3=c)
    return row


def main():
    manifest_path = ROOT / "diagnostics/loss_class_20260927/local_target_manifest_180951.json"
    assert hashlib.sha256(manifest_path.read_bytes()).hexdigest() == "524bc1bfa2f852b3865b94c4d7a37c67be9cc56690b56d2ed0a9a201e4412e20"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    fixtures = manifest["live_losses"] + manifest["current_top20"]
    for fixture in fixtures:
        fixture["path"] = fixture["source_action_tape_path"]
    records = json.loads((HERE / "candidates.json").read_text())
    jobs = [(record, fixture, seat) for record in records for fixture in fixtures for seat in (0, 1)
            if record["arm"] == "4ee" or (fixture["fixture_id"].startswith("top20-") and
               fixture["team"] in ("DECEM", "Boey", "Vadim Vasilenko", "DSM", "Majkel1337"))]
    checkpoint = HERE / "physical.jsonl"
    results = [json.loads(line) for line in checkpoint.read_text(encoding="utf-8").splitlines()] if checkpoint.exists() else []
    keys = {(r["arm"], r["fixture_id"], r["seat"]) for r in results}
    assert len(keys) == len(results)
    expected = {(r["arm"], f["fixture_id"], seat): r["sha256"] for r, f, seat in jobs}
    assert all(r["candidate_sha256"] == expected[(r["arm"], r["fixture_id"], r["seat"])] for r in results)
    pending = [job for job in jobs if (job[0]["arm"], job[1]["fixture_id"], job[2]) not in keys]
    print(f"Resuming {len(results)}/{len(jobs)} prefix checks", flush=True)
    with checkpoint.open("a", encoding="utf-8") as output:
        for start in range(0, len(pending), 16):
            with ProcessPoolExecutor(max_workers=4) as pool:
                for future in as_completed([pool.submit(check, job) for job in pending[start:start+16]]):
                    row = future.result()
                    results.append(row)
                    output.write(json.dumps(row, ensure_ascii=False) + "\n")
                    output.flush()
                    if len(results) % 10 == 0 or not row["physical_equal_step3"]:
                        print(len(results), "/", len(jobs), row["arm"], row["team"], row["physical_equal_step3"], flush=True)
    assert len(results) == len(jobs)
    by_key = {}
    shared = True
    for row in results:
        key = (row["fixture_id"], row["seat"])
        if key in by_key:
            shared = shared and row["candidate_step1"] == by_key[key]
        else:
            by_key[key] = row["candidate_step1"]
    payload = {"results": results, "candidate_hashes": records,
               "physical_gate_pass": all(r["physical_equal_step3"] for r in results),
               "common_step1_observations": shared,
               "incumbent_full_observation_checks": sum(r["arm"] == "4ee" for r in results),
               "interpretation": "Four-turn runs only, full 720-turn configuration, no complete-game outcomes."}
    (HERE / "physical.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k:payload[k] for k in ("physical_gate_pass", "common_step1_observations", "incumbent_full_observation_checks")}))


if __name__ == "__main__":
    main()
