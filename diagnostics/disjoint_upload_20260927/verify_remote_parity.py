import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from paired_benchmark import _load_module, make
from kaggle_environments.agent import get_last_callable


if __name__ == "__main__":
    path = ROOT / "main_uploaded_disjoint_integrated_20260927_c68fa46f.py"
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    assert digest == "c68fa46f6f0c52b9779a2f135bee8024b8f56310934a17b3683e5023686fbdad"
    remote = json.loads((HERE / "episode-114057799-replay.json").read_text(encoding="utf8"))
    seed = int(remote["info"]["seed"])
    loaded = get_last_callable(path.read_text(encoding="utf8"), path=str(path)).__name__
    assert loaded == "kaggle_disjoint_integrated_entrypoint"
    modes = []
    for mode in ("file", "direct"):
        modules = []
        if mode == "file":
            agents = [str(path), str(path)]
        else:
            modules = [_load_module(path, f"remote_parity_seat{seat}") for seat in (0, 1)]
            agents = [m.agent for m in modules]
        try:
            env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}, debug=False)
            env.run(agents)
            cash = [float(x.reward) for x in env.steps[-1]]
            statuses = [x.status for x in env.steps[-1]]
            actions_equal = [all(frame[seat].action == remote["steps"][step][seat]["action"]
                                 for step, frame in enumerate(env.steps[1:], 1)) for seat in (0, 1)]
            row = {"mode": mode, "cash": cash, "statuses": statuses,
                   "all_actions_match_remote": actions_equal, "frames": len(env.steps)}
            modes.append(row)
            print(json.dumps(row), flush=True)
            assert cash == remote["rewards"] and statuses == ["DONE", "DONE"]
            assert all(actions_equal) and len(env.steps) == 720
        finally:
            for module in modules:
                sys.modules.pop(module.__name__, None)
    result = {"submission_id": 56602057, "validation_episode_id": 114057799,
              "candidate_sha256": digest, "loaded_name": loaded, "seed": seed,
              "seed_source": "replay.info.seed", "remote_cash": remote["rewards"],
              "rows": modes, "passed": True}
    (HERE / "validation_parity.json").write_text(json.dumps(result, indent=2), encoding="utf8")
