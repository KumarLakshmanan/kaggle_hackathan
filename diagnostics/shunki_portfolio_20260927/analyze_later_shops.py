"""Build outcome-blind, exact-prefix-compatible later-shop route choices."""

from __future__ import annotations

from collections import Counter, defaultdict
import gzip
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main() -> None:
    manifest = json.loads((HERE / "route_manifest.json").read_text(encoding="utf8"))
    sequences = json.loads((HERE / "shop_sequences.json").read_text(encoding="utf8"))
    assert len(manifest["rows"]) == len(sequences["rows"]) == 203
    by_episode = {row["episode_id"]: row for row in sequences["rows"]}
    actions = {}
    for row in manifest["rows"]:
        with gzip.open(row["route_path"], "rt", encoding="utf8") as handle:
            actions[row["episode_id"]] = json.load(handle)["actions"]
    by_prefix = defaultdict(list)
    for row in manifest["rows"]:
        episode = row["episode_id"]
        for n in range(1, 9):
            shops = by_episode[episode]["reveals"][str(72 * n)]
            if len(shops) < n:
                continue
            by_prefix[tuple(shops[:n])].append(episode)
    selected = {}
    compatible = Counter()
    switched = Counter()
    missing = Counter()
    examples = []
    for n in range(1, 9):
        for key, episodes in sorted(by_prefix.items()):
            if len(key) != n:
                continue
            if n <= 2:
                selected[key] = episodes[0]
                continue
            parent = selected[key[:-1]]
            turn = 72 * n
            matches = [episode for episode in episodes
                       if actions[episode][:turn] == actions[parent][:turn]]
            if matches:
                selected[key] = matches[0]
                compatible[n] += 1
                if selected[key] != parent:
                    switched[n] += 1
            else:
                selected[key] = parent
                missing[n] += 1
                if len(examples) < 20:
                    examples.append({"shops": list(key), "parent_episode": parent,
                                     "source_episodes": episodes})
    target = ("ICE_CREAM_SHOP", "BRUNCH_SPOT", "YARN_STORE")
    assert selected[target[:2]] == 113445495
    assert selected[target] == 113347600
    result = {"source_routes": 203, "prefix_coverage":
              {str(n): sum(len(key) == n for key in by_prefix) for n in range(1, 9)},
              "exact_compatible_prefixes": dict(sorted(compatible.items())),
              "route_switches": dict(sorted(switched.items())),
              "no_exact_match": dict(sorted(missing.items())),
              "no_exact_match_examples": examples,
              "ice_brunch_yarn": {"parent": selected[target[:2]],
                                   "selected": selected[target]},
              "route_map": {"|".join(key): episode for key, episode in selected.items()}}
    (HERE / "later_shop_analysis.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf8")
    print({key: result[key] for key in ("prefix_coverage", "exact_compatible_prefixes",
                                       "route_switches", "no_exact_match",
                                       "ice_brunch_yarn")})


if __name__ == "__main__":
    main()
