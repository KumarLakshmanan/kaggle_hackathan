from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import random
import statistics
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from paired_benchmark import run_game, engine_version

OLD = ROOT / "main_uploaded_disjoint_integrated_20260927_c68fa46f.py"
RIVALS = {
    "c68": OLD,
    "1f": ROOT / "exp_shunki_visible_repair_20260927.py",
    "489": ROOT / "main_uploaded_mirror_straw24_20260926_489fe8e4.py",
    "C95": ROOT / "diagnostics/public_rayk_top_meta/public_c95_main.py",
}
ERROR_KEYS = ("queue_errors", "quantity_errors", "mirror_quantity_errors", "farmice_errors",
              "integration_gate_collisions", "purchase_queue_errors")


def play(job):
    path, digest, rival, rival_digest, version, seed, seat = job
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == digest
    assert hashlib.sha256(RIVALS[rival].read_bytes()).hexdigest() == rival_digest
    game = run_game(path, str(RIVALS[rival]), seed, seat, False, 144, {})
    return {"version": version, "rival": rival, **game}


def point(game):
    return 1.0 if game["result"] == "win" else 0.5 if game["result"] == "draw" else 0.0


if __name__ == "__main__":
    manifest = json.loads((HERE / "build_manifest.json").read_text())
    panels = json.loads((HERE / "panels.json").read_text())
    assert panels["complete"] and panels["passed"] and panels["candidate_sha256"] == manifest["candidate_sha256"]
    assert not (HERE / "confirmation.json").exists(), "Inspect the saved confirmation before resuming"
    seeds = list(range(2696000, 2696016))
    hashes = {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in RIVALS.items()}
    assert hashes["c68"] == "c68fa46f6f0c52b9779a2f135bee8024b8f56310934a17b3683e5023686fbdad"
    versions = {"old": (str(OLD), hashes["c68"]), "new": (manifest["candidate"], manifest["candidate_sha256"])}
    jobs = [(path, digest, rival, hashes[rival], version, seed, seat)
            for seed in seeds for rival in RIVALS for version, (path, digest) in versions.items() for seat in (0, 1)]
    output = {"started_at_utc": datetime.now(timezone.utc).isoformat(), "candidate_sha256": manifest["candidate_sha256"],
              "engine_version": engine_version, "rival_hashes": hashes, "seeds": seeds, "complete": False, "games": []}

    def save():
        (HERE / "confirmation.json").write_text(json.dumps(output, indent=2), encoding="utf8")

    save()
    with ProcessPoolExecutor(max_workers=4) as pool:
        for future in as_completed([pool.submit(play, job) for job in jobs]):
            game = future.result()
            output["games"].append(game)
            output["games"].sort(key=lambda g: (g["seed"], g["rival"], g["version"], g["candidate_seat"]))
            save()
            print(f"{len(output['games'])}/256 {game['version']} vs {game['rival']} "
                  f"seed={game['seed']} seat={game['candidate_seat']} {game['result']} {game['margin']:+.0f}", flush=True)
    games = output["games"]
    scores = {rival: {version: sum(point(g) for g in games if g["rival"] == rival and g["version"] == version)
                      for version in versions} for rival in RIVALS}
    seed_deltas = [sum(point(g) * (1 if g["version"] == "new" else -1) for g in games if g["seed"] == seed) / 8
                   for seed in seeds]
    rng = random.Random(2696099)
    bootstrap = sorted(statistics.fmean(rng.choices(seed_deltas, k=len(seeds))) for _ in range(10000))
    interval = [bootstrap[250], bootstrap[9749]]
    all_done = all(g["candidate_status"] == g["opponent_status"] == "DONE" and g["frames"] == 720 for g in games)
    errors = {key: sum(int((g.get("candidate_telemetry") or {}).get(key, 0)) for g in games) for key in ERROR_KEYS}
    nonregression = all(score["new"] >= score["old"] for score in scores.values())
    output.update(complete=True, completed_at_utc=datetime.now(timezone.utc).isoformat(), scores=scores,
                  seed_deltas=seed_deltas, paired_seed_bootstrap_95=interval, all_done=all_done, errors=errors,
                  reference_nonregression=nonregression,
                  passed=all_done and not any(errors.values()) and scores["c68"]["new"] >= 24
                  and nonregression and interval[0] > 0)
    save()
    print("RESULT " + json.dumps({k: output[k] for k in ("scores", "paired_seed_bootstrap_95", "all_done", "errors", "passed")}), flush=True)
