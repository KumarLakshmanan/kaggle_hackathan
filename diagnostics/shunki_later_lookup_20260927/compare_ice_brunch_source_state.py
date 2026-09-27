"""Compare a failed route replay with its selected public source state."""

from __future__ import annotations

from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from trace_paired_game import run  # noqa: E402

EPISODE = 113445495
SEED = 2027389298
MANIFEST = ROOT / "diagnostics" / "shunki_portfolio_20260927" / "route_manifest.json"
REPLAY = ROOT / "diagnostics" / "shunki_portfolio_20260927" / "incoming" / f"episode-{EPISODE}-replay.json"
CANDIDATE = ROOT / "exp_shunki_later_lookup_20260927.py"
PANEL = HERE / "top100_analysis.json"
STEPS = (72, 144, 216, 240, 288, 360, 480, 600, 718)


def tile_counter(farm: dict) -> Counter:
    counter = Counter()
    for row in farm["tiles"]:
        for tile in row:
            if isinstance(tile, dict):
                counter[(tile.get("kind"), tile.get("crop"), tile.get("animal"))] += 1
    return counter


def at(obs: dict) -> dict:
    player = int(obs["player"])
    farm = obs["farms"][player]
    return {"shops": obs["town"]["unlocked_shops"],
            "money": farm["money"], "hands": len(farm["hands"]),
            "farmer": farm["farmer"],
            "tiles": {"|".join(str(x) for x in key): count
                      for key, count in tile_counter(farm).items()},
            "shed": obs["private"]["shed"],
            "prices": obs["market"]["prices"]}


def main() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf8"))
    source = next(row for row in manifest["rows"] if row["episode_id"] == EPISODE)
    raw = REPLAY.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == source["replay_sha256"]
    replay = json.loads(raw)
    seat = int(source["source_seat"])
    assert replay["info"]["TeamNames"][seat] == "ShunkiKyoya"
    target = next(row for row in json.loads(PANEL.read_text(encoding="utf8"))["rows"]
                  if row["seed"] == SEED and row["team"] == "Dipam Chakraborty")
    data = run(str(CANDIDATE), f"rawroute:{target['opponent_path']}", SEED, 0)
    assert data["candidate_reward"] - data["opponent_reward"] == (
        target["seat_margins"]["0"]["candidate"])
    with gzip.open(source["route_path"], "rt", encoding="utf8") as handle:
        source_actions = json.load(handle)["actions"]
    candidate_actions = [row["action"] for row in data["traces"][0]]
    action_diffs = [step for step, (own, original) in
                    enumerate(zip(candidate_actions, source_actions)) if own != original]
    snapshots = []
    for step in STEPS:
        source_obs = replay["steps"][step][seat]["observation"]
        candidate_obs = data["traces"][0][step]["observation"]
        snapshots.append({"step": step, "source": at(source_obs),
                          "candidate": at(candidate_obs)})
    result = {"source_episode": EPISODE, "source_seat": seat,
              "source_seed": source["seed"], "candidate_seed": SEED,
              "candidate_cash": [data["candidate_reward"], data["opponent_reward"]],
              "action_difference_count": len(action_diffs),
              "first_action_differences": action_diffs[:25],
              "snapshots": snapshots}
    (HERE / "ice_brunch_source_state_comparison.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf8")
    print("action differences", len(action_diffs), action_diffs[:25])
    for row in snapshots:
        a, b = row["source"], row["candidate"]
        print(row["step"], "shops", a["shops"], b["shops"],
              "money", a["money"], b["money"],
              "hands", a["hands"], b["hands"],
              "tiles", a["tiles"], b["tiles"])


if __name__ == "__main__":
    main()
