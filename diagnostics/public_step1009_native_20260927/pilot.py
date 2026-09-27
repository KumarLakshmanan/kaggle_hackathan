from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from paired_benchmark import _load_module, make, TimedAgent, _timing_dict, engine_version

OLD = ROOT / "main_uploaded_disjoint_integrated_20260927_c68fa46f.py"


def errors(module):
    found = {}
    for name, value in vars(module).items():
        if isinstance(value, dict) and ("REPORT" in name or "STATS" in name):
            for key, count in value.items():
                if isinstance(key, str) and ("error" in key.lower() or "collision" in key.lower()) and isinstance(count, (int, float)):
                    found[name + "." + key] = count
    return found


def play(job):
    path, digest, seed, seat = job
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == digest
    assert hashlib.sha256(OLD.read_bytes()).hexdigest() == "c68fa46f6f0c52b9779a2f135bee8024b8f56310934a17b3683e5023686fbdad"
    candidate = _load_module(Path(path), "public_step1009")
    rival = _load_module(OLD, "public_step1009_rival")
    assert candidate.agent.__name__ == "step1009_step1008_fortyfirst_final_fixedsell_closure_agent"

    def candidate_call(obs, cfg):
        visible = dict(cfg)
        visible["seed"] = None
        return candidate.agent(obs, visible)

    def rival_call(obs, cfg):
        visible = dict(cfg)
        visible["seed"] = None
        return rival.agent(obs, visible)

    timed_candidate = TimedAgent(candidate_call, capture_step=144)
    timed_rival = TimedAgent(rival_call)
    try:
        env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}, debug=False)
        started = time.perf_counter()
        env.run([timed_candidate, timed_rival] if seat == 0 else [timed_rival, timed_candidate])
        final = env.steps[-1]
        own, other = float(final[seat].reward or 0), float(final[1-seat].reward or 0)
        margin = own - other
        return {"seed": seed, "candidate_seat": seat, "candidate_reward": own, "opponent_reward": other,
                "margin": margin, "result": "win" if margin > 0 else "loss" if margin < 0 else "draw",
                "candidate_status": final[seat].status, "opponent_status": final[1-seat].status,
                "frames": len(env.steps), "wall_seconds": time.perf_counter() - started,
                "candidate_timing": _timing_dict(timed_candidate), "opponent_timing": _timing_dict(timed_rival),
                "candidate_capture": timed_candidate.capture, "candidate_errors": errors(candidate),
                "opponent_errors": errors(rival), "candidate_telemetry": dict(candidate.agent.telemetry),
                "opening_mode": candidate._ALT_MODE, "configuration_seed_visible": None}
    finally:
        sys.modules.pop(candidate.__name__, None)
        sys.modules.pop(rival.__name__, None)


if __name__ == "__main__":
    manifest = json.loads((HERE / "build_manifest.json").read_text())
    assert not (HERE / "pilot.json").exists(), "Inspect existing pilot instead of replaying results"
    seeds = list(range(2697000, 2697008))
    jobs = [(manifest["candidate"], manifest["candidate_sha256"], seed, seat) for seed in seeds for seat in (0, 1)]
    output = {"started_at_utc": datetime.now(timezone.utc).isoformat(), "candidate_sha256": manifest["candidate_sha256"],
              "engine_version": engine_version, "seeds": seeds, "configuration_seed_masked": True,
              "complete": False, "games": []}

    def save():
        (HERE / "pilot.json").write_text(json.dumps(output, indent=2), encoding="utf8")

    save()
    with ProcessPoolExecutor(max_workers=4) as pool:
        for future in as_completed([pool.submit(play, job) for job in jobs]):
            game = future.result()
            output["games"].append(game)
            output["games"].sort(key=lambda g: (g["seed"], g["candidate_seat"]))
            save()
            print(f"{len(output['games'])}/16 seed={game['seed']} seat={game['candidate_seat']} "
                  f"{game['result']} {game['margin']:+.0f} {game['candidate_status']}/{game['opponent_status']} "
                  f"errors={sum(game['candidate_errors'].values())}", flush=True)
    games = output["games"]
    points = sum(1 if g["result"] == "win" else .5 if g["result"] == "draw" else 0 for g in games)
    all_done = all(g["candidate_status"] == g["opponent_status"] == "DONE" and g["frames"] == 720 for g in games)
    error_count = sum(sum(g["candidate_errors"].values()) + sum(g["opponent_errors"].values()) for g in games)
    output.update(complete=True, completed_at_utc=datetime.now(timezone.utc).isoformat(), points=points,
                  all_done=all_done, errors=error_count, passed=points >= 12 and all_done and error_count == 0)
    save()
    print("RESULT " + json.dumps({k: v for k, v in output.items() if k != "games"}), flush=True)
