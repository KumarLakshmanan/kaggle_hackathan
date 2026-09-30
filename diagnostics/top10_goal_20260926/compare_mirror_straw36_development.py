"""Compare the 36-turn pilot with submitted 24-turn development replays."""

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PANELS = (
    ("older_live_losses", "mirror_straw24_live_losses6.json", "mirror_straw36_live_losses6.json"),
    ("later_public_routes", "mirror_straw24_recent7_candidate.json", "mirror_straw36_recent7.json"),
)
OUTPUT = HERE / "mirror_straw36_development_comparison.json"


def games(path):
    data = json.loads((HERE / path).read_text(encoding="utf8"))
    return {(row["episode_id"], game["candidate_seat"]): game
            for row in data["rows"] for game in row["games"]}


def main():
    out = {}
    for label, old_path, new_path in PANELS:
        old = games(old_path)
        new = games(new_path)
        assert old.keys() == new.keys()
        changed = []
        for key in sorted(old):
            previous, current = old[key], new[key]
            assert previous["candidate_status"] == previous["opponent_status"] == "DONE"
            assert current["candidate_status"] == current["opponent_status"] == "DONE"
            if previous["margin"] != current["margin"]:
                changed.append({
                    "episode_id": key[0], "seat": key[1],
                    "old_margin": previous["margin"],
                    "new_margin": current["margin"],
                    "own_delta": current["candidate_reward"] - previous["candidate_reward"],
                    "rival_delta": current["opponent_reward"] - previous["opponent_reward"],
                })
        out[label] = {
            "games": len(old),
            "changed_games": len(changed),
            "rescues": sum(x["old_margin"] < 0 < x["new_margin"] for x in changed),
            "reversals": sum(x["old_margin"] > 0 > x["new_margin"] for x in changed),
            "margin_delta": sum(x["new_margin"] - x["old_margin"] for x in changed),
            "own_delta": sum(x["own_delta"] for x in changed),
            "rival_delta": sum(x["rival_delta"] for x in changed),
            "changed": changed,
        }
    OUTPUT.write_text(json.dumps(out, indent=2) + "\n", encoding="utf8")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
