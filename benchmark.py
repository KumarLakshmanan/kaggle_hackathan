"""Deterministic local benchmark for Kaggriculture candidate agents."""

import argparse
import statistics

from kaggle_environments import make

from approaches import CANDIDATES


def run_one(candidate_name, opponent, seed):
    env = make(
        "kaggriculture",
        configuration={"episodeSteps": 720, "seed": int(seed)},
        debug=False,
    )
    env.run([CANDIDATES[candidate_name], opponent])
    final = env.steps[-1]
    rewards = [float(state.reward or 0.0) for state in final]
    statuses = [state.status for state in final]
    return rewards, statuses


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", nargs="+", type=int, default=[1, 2, 3, 42, 100])
    parser.add_argument("--opponent", default="pass")
    parser.add_argument("--candidates", nargs="+", default=list(CANDIDATES))
    args = parser.parse_args()

    rows = []
    for name in args.candidates:
        scores = []
        for seed in args.seeds:
            rewards, statuses = run_one(name, args.opponent, seed)
            scores.append(rewards[0])
            print(
                f"{name:28s} seed={seed:5d} "
                f"score={rewards[0]:10.1f} opp={rewards[1]:10.1f} "
                f"status={statuses}",
                flush=True,
            )
        rows.append((name, statistics.mean(scores), min(scores), max(scores)))

    print("\nSUMMARY")
    for name, mean, low, high in sorted(rows, key=lambda row: row[1], reverse=True):
        print(f"{name:28s} mean={mean:10.1f} min={low:10.1f} max={high:10.1f}")


if __name__ == "__main__":
    main()
