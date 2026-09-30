"""Compare the uploaded agent's Kaggle validation replay to local file-path play."""

import hashlib
import json
from pathlib import Path

from kaggle_environments import make
from kaggle_environments.agent import get_last_callable


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
MAIN = ROOT / "main.py"
REPLAY = HERE / "episode-113604202-replay.json"
OUTPUT = HERE / "validation_parity.json"
EXPECTED_HASH = "489fe8e4e80b03e7e6485b5969f3bec1861fa8389473f361969f064e484f6c7b"


def main():
    source_hash = hashlib.sha256(MAIN.read_bytes()).hexdigest()
    assert source_hash == EXPECTED_HASH, source_hash
    loaded = get_last_callable(MAIN.read_text(encoding="utf8"), path=str(MAIN)).__name__
    assert loaded == "kaggle_main_entrypoint", loaded

    replay = json.loads(REPLAY.read_text(encoding="utf8"))
    assert replay["info"]["seed"] == 0
    assert replay["statuses"] == ["DONE", "DONE"]
    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 0}, debug=False)
    env.run([str(MAIN), str(MAIN)])
    local_statuses = [x.status for x in env.steps[-1]]
    local_rewards = [float(x.reward) for x in env.steps[-1]]
    remote_rewards = [float(x) for x in replay["rewards"]]
    local_first = [env.steps[1][seat].action for seat in (0, 1)]
    remote_first = [replay["steps"][1][seat]["action"] for seat in (0, 1)]
    assert local_statuses == replay["statuses"]
    assert local_rewards == remote_rewards, (local_rewards, remote_rewards)
    assert local_first == remote_first
    assert all(action["market"] for action in local_first)

    result = {
        "submission": 56572390,
        "validation_episode": 113604202,
        "seed": 0,
        "source_sha256": source_hash,
        "loaded_name": loaded,
        "remote_statuses": replay["statuses"],
        "local_statuses": local_statuses,
        "remote_rewards": remote_rewards,
        "local_rewards": local_rewards,
        "first_actions_match": True,
    }
    OUTPUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
