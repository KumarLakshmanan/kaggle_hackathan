"""Post-promotion Kaggle path smoke on the final main.py filename."""

import ast
import hashlib
import json
from pathlib import Path

from kaggle_environments import make
from kaggle_environments.agent import get_last_callable

ROOT = Path(__file__).resolve().parents[2]
MAIN = ROOT / "main.py"
CANDIDATE = ROOT / "exp_entrypoint_fix_20260926.py"
OLD = ROOT / "main_before_top10_goal_20260926_04b0bdc3.py"
OUTPUT = Path(__file__).with_name("entrypoint_promoted_smoke.json")
SEED = 2610902


def run(path, seat):
    agents = [str(path), str(OLD)] if seat == 0 else [str(OLD), str(path)]
    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": SEED},
               debug=False)
    env.run(agents)
    end = env.steps[-1]
    return {
        "own_cash": float(end[seat].reward),
        "rival_cash": float(end[1 - seat].reward),
        "own_status": end[seat].status,
        "rival_status": end[1 - seat].status,
        "first_action": env.steps[1][seat].action,
    }


def main():
    code = MAIN.read_text(encoding="utf8")
    ast.parse(code, filename=str(MAIN))
    main_hash = hashlib.sha256(MAIN.read_bytes()).hexdigest()
    candidate_hash = hashlib.sha256(CANDIDATE.read_bytes()).hexdigest()
    assert main_hash == candidate_hash
    loaded = get_last_callable(code, path=str(MAIN))
    assert loaded.__name__ == "kaggle_main_entrypoint"
    rows = []
    for seat in (0, 1):
        promoted = run(MAIN, seat)
        source = run(CANDIDATE, seat)
        assert promoted == source
        assert promoted["own_status"] == promoted["rival_status"] == "DONE"
        assert promoted["first_action"]["market"]
        rows.append({"seat": seat, "promoted": promoted})
        print(f"seat={seat} own={promoted['own_cash']:.0f} "
              f"rival={promoted['rival_cash']:.0f} exact_candidate=True", flush=True)
    OUTPUT.write_text(json.dumps({
        "main_sha256": main_hash,
        "selected_callable": loaded.__name__,
        "seed": SEED,
        "rows": rows,
    }, indent=2), encoding="utf8")
    print(OUTPUT)


if __name__ == "__main__":
    main()
