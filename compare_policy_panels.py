"""Compare two paired benchmark reports route-by-route."""

from __future__ import annotations

import argparse
import collections
import json
import os
from pathlib import Path


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def key(row):
    path = os.path.normcase(os.path.normpath(str(row.get("opponent_path", ""))))
    return path, int(row.get("seed", 0))


def pair_margins(path: Path):
    payload = load(path)
    grouped = collections.defaultdict(list)
    for row in payload.get("rows", []):
        if "margin" in row:
            grouped[key(row)].append(float(row["margin"]))
    return {item: sum(values) for item, values in grouped.items()}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--left", type=Path, required=True)
    parser.add_argument("--right", type=Path, required=True)
    parser.add_argument("--capture", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    left = pair_margins(args.left)
    right = pair_margins(args.right)
    features = {}
    if args.capture:
        for row in load(args.capture):
            if row.get("capture_step") != 72:
                continue
            features.setdefault(key({"opponent_path": row["path"], "seed": row["seed"]}), row)

    rows = []
    for route in sorted(set(left) & set(right)):
        feature = features.get(route)
        rows.append({
            "path": route[0],
            "seed": route[1],
            "shops": feature.get("shops") if feature else None,
            "opponent_counts": feature.get("opponent_counts") if feature else None,
            "opponent_money": feature.get("opponent_money") if feature else None,
            "left_pair_margin": left[route],
            "right_pair_margin": right[route],
            "left_win": left[route] > 0,
            "right_win": right[route] > 0,
            "delta_left_minus_right": left[route] - right[route],
        })

    def summary(values):
        margins = [row[values] for row in rows]
        return {
            "routes": len(margins),
            "wins": sum(value > 0 for value in margins),
            "losses": sum(value < 0 for value in margins),
            "mean_pair_margin": sum(margins) / len(margins) if margins else None,
        }

    cross = collections.Counter((row["left_win"], row["right_win"]) for row in rows)
    by_shop = collections.defaultdict(list)
    for row in rows:
        shop = (row.get("shops") or ["?"])[0]
        by_shop[shop].append(row)

    result = {
        "left": str(args.left),
        "right": str(args.right),
        "left_summary": summary("left_pair_margin"),
        "right_summary": summary("right_pair_margin"),
        "cross": {f"left_{a}_right_{b}": count for (a, b), count in sorted(cross.items())},
        "shop_summary": {
            shop: {
                "routes": len(items),
                "left_wins": sum(item["left_win"] for item in items),
                "right_wins": sum(item["right_win"] for item in items),
                "left_mean": sum(item["left_pair_margin"] for item in items) / len(items),
                "right_mean": sum(item["right_pair_margin"] for item in items) / len(items),
            }
            for shop, items in sorted(by_shop.items())
        },
        "routes": rows,
    }
    if args.output:
        args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print("LEFT", json.dumps(result["left_summary"], sort_keys=True))
    print("RIGHT", json.dumps(result["right_summary"], sort_keys=True))
    print("CROSS", json.dumps(result["cross"], sort_keys=True))
    print("SHOP", json.dumps(result["shop_summary"], sort_keys=True))
    print("LEFT_ONLY_WINS")
    for row in rows:
        if row["left_win"] and not row["right_win"]:
            print(row["shops"], row["seed"], round(row["left_pair_margin"]), round(row["right_pair_margin"]))
    print("RIGHT_ONLY_WINS")
    for row in rows:
        if row["right_win"] and not row["left_win"]:
            print(row["shops"], row["seed"], round(row["left_pair_margin"]), round(row["right_pair_margin"]))


if __name__ == "__main__":
    main()
