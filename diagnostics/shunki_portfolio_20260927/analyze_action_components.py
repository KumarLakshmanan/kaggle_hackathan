"""Audit whether public route differences permit shop-time branching."""

from __future__ import annotations

from collections import Counter, defaultdict
import gzip
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def prefix_length(routes: list[list], component: str | None = None) -> int:
    anchor = routes[0]
    for step in range(min(len(route) for route in routes)):
        expected = anchor[step] if component is None else anchor[step].get(component)
        if any((route[step] if component is None else route[step].get(component))
               != expected for route in routes[1:]):
            return step
    return len(anchor)


def summarize(rows: list[dict], actions: dict[int, list]) -> dict:
    routes = [actions[row["episode_id"]] for row in rows]
    full = prefix_length(routes)
    components = {key: prefix_length(routes, key)
                  for key in ("farmer", "hands", "market")}
    divergent = (None if full == len(routes[0]) else
                 next((row for row in rows[1:]
                       if actions[row["episode_id"]][full] != routes[0][full]), None))
    fields = [] if divergent is None else [key for key in components
              if routes[0][full].get(key) != actions[divergent["episode_id"]][full].get(key)]
    return {"episodes": len(rows), "full_prefix": full,
            "component_prefixes": components,
            "first_difference_fields": fields,
            "example_episodes": None if divergent is None else
            [rows[0]["episode_id"], divergent["episode_id"]]}


def main() -> None:
    manifest = json.loads((HERE / "route_manifest.json").read_text(encoding="utf8"))
    rows = manifest["rows"]
    actions = {}
    for row in rows:
        with gzip.open(row["route_path"], "rt", encoding="utf8") as handle:
            actions[row["episode_id"]] = json.load(handle)["actions"]
    groups = {}
    for name, key in (("first_shop", lambda row: (row["shops_day6"][0],)),
                      ("shop_pair", lambda row: tuple(row["shops_day6"]))):
        by_group = defaultdict(list)
        for row in rows:
            by_group[key(row)].append(row)
        groups[name] = [{"shops": list(shops), **summarize(members, actions)}
                        for shops, members in sorted(by_group.items())]
    same_pair = [row for row in groups["shop_pair"] if row["full_prefix"] < 719]
    fields = Counter(tuple(row["first_difference_fields"]) for row in same_pair)
    result = {"total_routes": len(rows), "all_routes": summarize(rows, actions),
              **groups, "same_pair_first_difference_fields":
              {"+".join(key): count for key, count in sorted(fields.items())}}
    (HERE / "component_analysis.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf8")
    for row in groups["first_shop"]:
        print(row["shops"], "full", row["full_prefix"],
              "fields", row["first_difference_fields"],
              "components", row["component_prefixes"],
              "episodes", row["example_episodes"])
    print("same_pair_fields", result["same_pair_first_difference_fields"])
    print("early_same_pair", [(row["shops"], row["full_prefix"],
                               row["first_difference_fields"], row["example_episodes"])
                              for row in sorted(same_pair, key=lambda row: row["full_prefix"])[:15]])


if __name__ == "__main__":
    main()
