"""Locate exact earliest action divergences in collected public routes."""

from __future__ import annotations

from collections import Counter, defaultdict
import gzip
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def lcp(a: list, b: list) -> int:
    count = 0
    for x, y in zip(a, b):
        if x != y:
            break
        count += 1
    return count


def group_summary(rows: list[dict], actions: dict[int, list]) -> dict:
    anchor = actions[rows[0]["episode_id"]]
    lengths = [lcp(anchor, actions[row["episode_id"]]) for row in rows]
    first = min(lengths)
    return {"episodes": len(rows),
            "distinct_action_hashes": len({row["action_sha256"] for row in rows}),
            "common_prefix_actions": first,
            "divergence_step": first if first < 719 else None,
            "divergence_examples": [row["episode_id"] for row, n in zip(rows, lengths)
                                    if n == first][:4]}


def main() -> None:
    manifest = json.loads((HERE / "route_manifest.json").read_text(encoding="utf8"))
    rows = manifest["rows"]
    actions = {}
    for row in rows:
        with gzip.open(row["route_path"], "rt", encoding="utf8") as handle:
            actions[row["episode_id"]] = json.load(handle)["actions"]
    by_first = defaultdict(list)
    by_pair = defaultdict(list)
    for row in rows:
        by_first[row["shops_day6"][0]].append(row)
        by_pair[tuple(row["shops_day6"])].append(row)
    first = [{"first_shop": shop, **group_summary(group, actions)}
             for shop, group in sorted(by_first.items())]
    pairs = [{"shops": list(pair), **group_summary(group, actions)}
             for pair, group in sorted(by_pair.items())]
    hist = Counter(row["common_prefix_actions"] for row in pairs
                   if row["distinct_action_hashes"] > 1)
    result = {"first_shop_groups": first, "shop_pair_groups": pairs,
              "same_pair_conflict_earliest_divergence_histogram": dict(sorted(hist.items()))}
    (HERE / "prefix_analysis.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf8")
    print("first shop groups")
    for row in first:
        print(row["first_shop"], row["episodes"], row["distinct_action_hashes"],
              "lcp", row["common_prefix_actions"])
    print("conflict histogram", dict(sorted(hist.items())))
    print("earliest same-pair conflicts")
    for row in sorted((row for row in pairs if row["distinct_action_hashes"] > 1),
                      key=lambda row: row["common_prefix_actions"])[:14]:
        print(row["shops"], row["episodes"], row["distinct_action_hashes"],
              row["common_prefix_actions"], row["divergence_examples"])


if __name__ == "__main__":
    main()
