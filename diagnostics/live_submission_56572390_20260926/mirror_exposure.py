"""Read public replays to measure observable physical-mirror opportunities."""

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUTPUT = HERE / "mirror_exposure.json"


def summarize(path):
    replay = json.loads(path.read_text(encoding="utf8"))
    matches = 0
    eligible = 0
    for step in range(144, min(718, len(replay["steps"]))):
        frame = replay["steps"][step]
        observation = frame[0]["observation"]
        farms = observation["farms"]
        eligible += 1
        matches += (farms[0]["tiles"] == farms[1]["tiles"]
                    and farms[0]["farmer"] == farms[1]["farmer"]
                    and farms[0]["hands"] == farms[1]["hands"])
    return {"episode_id": replay["info"]["EpisodeId"],
            "teams": replay["info"]["TeamNames"],
            "eligible_turns": eligible, "physical_mirror_turns": matches,
            "margin_first_minus_second": replay["rewards"][0] - replay["rewards"][1]}


def main():
    rows = [summarize(path) for path in sorted(HERE.glob("episode-*-replay.json"))
            if "113604202" not in path.name]
    OUTPUT.write_text(json.dumps(rows, indent=2) + "\n", encoding="utf8")
    print(json.dumps(rows, indent=2))


if __name__ == "__main__":
    main()
