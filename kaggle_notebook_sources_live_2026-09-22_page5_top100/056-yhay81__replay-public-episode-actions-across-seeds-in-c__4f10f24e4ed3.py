%%bash
set -euo pipefail

SOURCE_FILE=$(find /kaggle/input -type f -name evaluate.cpp -print -quit)
test -n "$SOURCE_FILE"
SOURCE=$(dirname "$SOURCE_FILE")
echo "source: $SOURCE"
g++ -O3 -std=c++17 -pthread \
  -I"$SOURCE" \
  "$SOURCE/evaluate.cpp" \
  -o /kaggle/working/evaluate

/kaggle/working/evaluate --list-agents


%%bash
/kaggle/working/evaluate \
  --agents carrot pass \
  --episodes 10000 \
  --threads 8 \
  --seed 1


%%bash
set -euo pipefail

SOURCE_FILE=$(find /kaggle/input -type f -name episode_to_tape.py -print -quit)
test -n "$SOURCE_FILE"
SOURCE=$(dirname "$SOURCE_FILE")
EPISODE_ID=102248386
PLAYER=0

python "$SOURCE/episode_to_tape.py" \
  "$EPISODE_ID" \
  --player "$PLAYER" \
  --output "/kaggle/working/episode-${EPISODE_ID}-player${PLAYER}.txt"


import contextlib
import copy
import io
import json
import subprocess
import time
import urllib.request

from IPython.display import Markdown, display

with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
    from kaggle_environments import make


episode_id = 102248386
player = 0
tape_path = f"/kaggle/working/episode-{episode_id}-player{player}.txt"

# Stable C++ measurement: 5,000 seeds with both player positions.
cpp_result = json.loads(subprocess.check_output([
    "/kaggle/working/evaluate",
    "--agents", f"tape:{tape_path}", "pass",
    "--episodes", "10000",
    "--threads", "8",
    "--seed", "1",
], text=True))

# Read the same selected player's public action history for the official runner.
url = f"https://www.kaggleusercontent.com/episodes/{episode_id}.json"
request = urllib.request.Request(url, headers={"User-Agent": "kaggriculture-cpp-notebook/1.0"})
with urllib.request.urlopen(request, timeout=90) as response:
    replay = json.load(response)
if isinstance(replay.get("replay"), str):
    replay = json.loads(replay["replay"])
elif isinstance(replay.get("replay"), dict):
    replay = replay["replay"]
actions = [joint[player].get("action") or {} for joint in replay["steps"][1:]]
assert len(actions) == 719


def read(value, key, default=None):
    if isinstance(value, dict):
        return value.get(key, default)
    getter = getattr(value, "get", None)
    return getter(key, default) if callable(getter) else getattr(value, key, default)


def tape_agent(observation, configuration=None):
    del configuration
    raw_step = read(observation, "step")
    step = int(raw_step) if raw_step is not None else (
        int(read(observation, "day", 0) or 0) * 24
        + int(read(observation, "hour", 0) or 0)
    )
    action = copy.deepcopy(actions[min(max(step, 0), len(actions) - 1)])
    current_player = int(read(observation, "player", 0) or 0)
    farms = list(read(observation, "farms", []) or [])
    expected_hands = len(read(farms[current_player], "hands", []) or [])
    hands = list(action.get("hands") or [])
    hands.extend([["PASS"] for _ in range(max(0, expected_hands - len(hands)))])
    action["hands"] = hands[:expected_hands]
    return action


def official_episode(seed, tape_first):
    environment = make(
        "kaggriculture",
        configuration={"episodeSteps": 720, "seed": seed},
        debug=False,
    )
    environment.run([tape_agent, "pass"] if tape_first else ["pass", tape_agent])


# Warm up imports and environment initialization outside the measurement.
official_episode(0, True)
python_episodes = 8
started = time.perf_counter()
for seed in range(1, python_episodes // 2 + 1):
    official_episode(seed, True)
    official_episode(seed, False)
python_seconds = time.perf_counter() - started
python_eps = python_episodes / python_seconds
cpp_eps = float(cpp_result["episodes_per_second"])
speedup = cpp_eps / python_eps

table = f"""
| environment | episodes | seconds | episode/second | speedup |
|---|---:|---:|---:|---:|
| Official Python | {python_episodes:,} | {python_seconds:.3f} | {python_eps:.3f} | 1.0× |
| C++ | {cpp_result['episodes']:,} | {cpp_result['seconds']:.3f} | {cpp_eps:,.1f} | {speedup:,.0f}× |
"""
display(Markdown(table))
print(f"Official Python: {python_eps:.3f} episode/s | C++: {cpp_eps:.1f} episode/s | {speedup:.0f}x")


from pathlib import Path

source = next(
    path for path in Path("/kaggle/input").rglob("evaluate.cpp")
    if (path.parent / "source_manifest.json").is_file()
)
text = source.read_text()
start = text.index("Action carrot_agent(")
end = text.index("\n}\n", start) + 2
print(text[start:end])
