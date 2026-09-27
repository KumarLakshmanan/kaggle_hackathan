"""Record only the native incumbent's exogenous shop path for a matched-shop audit."""

from __future__ import annotations

import json
from pathlib import Path
import sys

from kaggle_environments import make

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from paired_benchmark import _load_agent  # noqa: E402


def main() -> None:
    seed = int(sys.argv[1])
    rows = {}
    first, _ = _load_agent(str(ROOT / "main.py"), "shop_audit_0")
    second, _ = _load_agent(str(ROOT / "main.py"), "shop_audit_1")

    def record(observation, configuration=None):
        step = int(observation["step"])
        if step % 24 == 0:
            day = step // 24
            rows[day] = dict(day=day,
                             shops=list(observation["town"]["unlocked_shops"]))
        return first(observation, configuration)

    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
    env.run([record, second])
    final = env.steps[-1]
    assert all(player.status == "DONE" for player in final)
    payload = dict(seed=seed, candidate="main.py", daily=[rows[d] for d in sorted(rows)],
                   cash=[player.reward for player in final])
    output = Path(__file__).with_name(f"incumbent_shop_path_{seed}.json")
    output.write_text(json.dumps(payload, indent=2), encoding="utf8")
    print(output, payload["cash"])


if __name__ == "__main__":
    main()
