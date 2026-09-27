"""Identify exact common-prefix boundaries among sampled public routes."""

from __future__ import annotations

from itertools import combinations
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPLAYS = HERE / "shunki_replays"


def common_prefix(a: list, b: list) -> int:
    n = 0
    for left, right in zip(a, b):
        if left != right:
            break
        n += 1
    return n


def main() -> None:
    sample = json.loads((HERE / "shunki_sample_profile.json").read_text(encoding="utf8"))
    routes = []
    for row in sample["rows"]:
        replay = json.loads((REPLAYS / f"episode-{row['episode_id']}-replay.json").read_text(encoding="utf8"))
        seat = row["source_seat"]
        actions = [(frame[seat].get("action") or {}) for frame in replay["steps"][1:]]
        routes.append({"id": row["episode_id"], "shops": row["shops_day6"],
                       "hash": row["action_sha256"], "actions": actions})
    pairs = []
    for left, right in combinations(routes, 2):
        if left["shops"][0] == right["shops"][0] or left["shops"] == right["shops"]:
            pairs.append({"left": left["id"], "right": right["id"],
                          "left_shops": left["shops"], "right_shops": right["shops"],
                          "same_first_shop": left["shops"][0] == right["shops"][0],
                          "same_pair": left["shops"] == right["shops"],
                          "common_actions": common_prefix(left["actions"], right["actions"]),
                          "same_full_action_hash": left["hash"] == right["hash"]})
    same_first = [row for row in pairs if row["same_first_shop"]]
    same_pair = [row for row in pairs if row["same_pair"]]
    result = {"sample_routes": len(routes),
              "distinct_full_routes": len({row["hash"] for row in routes}),
              "same_first_shop_pair_count": len(same_first),
              "same_first_shop_min_prefix": min((row["common_actions"] for row in same_first), default=None),
              "same_pair_pair_count": len(same_pair),
              "same_pair_min_prefix": min((row["common_actions"] for row in same_pair), default=None),
              "pairs": pairs}
    (HERE / "shunki_branching.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf8")
    print({key: result[key] for key in result if key != "pairs"})
    for row in pairs:
        print(row["left"], row["right"], row["left_shops"], row["right_shops"],
              row["common_actions"], row["same_full_action_hash"])


if __name__ == "__main__":
    main()
