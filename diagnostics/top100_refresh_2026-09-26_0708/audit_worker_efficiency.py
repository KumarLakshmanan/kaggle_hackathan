"""Exact native worker-action census on lost routes and deterministic controls."""

from __future__ import annotations

from collections import Counter
from concurrent.futures import ProcessPoolExecutor
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "diagnostics" / "live_refresh_56530281_20260926"))

from trace_paired_game_events import run  # noqa: E402

SOURCE = ROOT / "main.py"
EXPECTED_SHA = "489fe8e4e80b03e7e6485b5969f3bec1861fa8389473f361969f064e484f6c7b"
PANEL = HERE / "main_100routes.json"
LOSSES = HERE / "main_loss_manifest.json"
OUTPUT = HERE / "worker_efficiency_44.json"


def key(row: dict) -> tuple[str, int, int]:
    return (row["action_sha256"], int(row["seed"]), int(row["source_seat"]))


def select_controls(rows: list[dict], loss_keys: set[tuple[str, int, int]]) -> list[dict]:
    wins = sorted((row for row in rows if key(row) not in loss_keys and
                   row["pair_margin"] > 0), key=lambda r: (r["pair_margin"], key(r)))
    close = wins[:5]
    rest = wins[5:]
    spread = [rest[round(i * (len(rest) - 1) / 4)] for i in range(5)]
    return close + spread


def play(job: tuple[dict, bool]) -> dict:
    row, is_loss = job
    data = run(candidate=str(SOURCE), opponent=f"rawroute:{row['opponent_path']}",
               seed=int(row["seed"]), candidate_seat=0)
    expected = next(game for game in row["games"] if game["candidate_seat"] == 0)
    assert data["candidate_status"] == data["opponent_status"] == "DONE", row["team"]
    assert (data["candidate_reward"], data["opponent_reward"]) == (
        expected["candidate_reward"], expected["opponent_reward"]), row["team"]
    result = {"team": row["team"], "seed": row["seed"],
              "episode_id": row["episode_id"], "action_sha256": row["action_sha256"],
              "loss": is_loss, "pair_margin": row["pair_margin"],
              "candidate_reward": data["candidate_reward"],
              "opponent_reward": data["opponent_reward"], "players": []}
    for player in (0, 1):
        attempted = Counter()
        failed = Counter()
        windows: dict[str, Counter] = {}
        for event in data["events"]:
            if event.get("phase") != "unit_action" or event.get("player") != player:
                continue
            op = event["action"][0] if event.get("action") else "EMPTY"
            attempted[op] += 1
            bucket = f"{(int(event['step']) // 144) * 6:02d}-{(int(event['step']) // 144) * 6 + 5:02d}"
            window = windows.setdefault(bucket, Counter())
            window["total"] += 1
            if op == "PASS":
                window["pass"] += 1
            elif not event["changed"]:
                failed[op] += 1
                window["failed_nonpass"] += 1
        nonpass = sum(attempted.values()) - attempted["PASS"]
        result["players"].append({
            "player": player, "unit_actions": sum(attempted.values()),
            "passes": attempted["PASS"], "nonpass": nonpass,
            "failed_nonpass": sum(failed.values()),
            "failed_nonpass_rate": sum(failed.values()) / nonpass if nonpass else None,
            "attempted_by_op": dict(attempted), "failed_by_op": dict(failed),
            "windows": {name: dict(counts) for name, counts in sorted(windows.items())},
        })
    return result


def main() -> None:
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == EXPECTED_SHA
    panel = json.loads(PANEL.read_text(encoding="utf8"))
    losses = json.loads(LOSSES.read_text(encoding="utf8"))
    row_by_key = {key(row): row for row in panel["rows"]}
    assert len(losses) == 34
    loss_keys = {key(row) for row in losses}
    assert len(loss_keys) == 34
    selected = [row_by_key[k] for k in loss_keys]
    selected.sort(key=lambda r: (r["pair_margin"], key(r)))
    controls = select_controls(panel["rows"], loss_keys)
    assert len(controls) == 10 and len({key(row) for row in controls}) == 10
    jobs = [(row, True) for row in selected] + [(row, False) for row in controls]
    with ProcessPoolExecutor(max_workers=3) as pool:
        rows = list(pool.map(play, jobs))
    summary = {}
    for label, is_loss in (("losses", True), ("controls", False)):
        subset = [row for row in rows if row["loss"] == is_loss]
        summary[label] = {}
        for player in (0, 1):
            players = [row["players"][player] for row in subset]
            nonpass = sum(p["nonpass"] for p in players)
            failures = sum(p["failed_nonpass"] for p in players)
            actions = sum(p["unit_actions"] for p in players)
            passes = sum(p["passes"] for p in players)
            summary[label][f"player_{player}"] = {
                "routes": len(players), "unit_actions": actions, "passes": passes,
                "pass_rate": passes / actions, "nonpass": nonpass,
                "failed_nonpass": failures, "failed_nonpass_rate": failures / nonpass,
                "routes_with_100_failures": sum(p["failed_nonpass"] >= 100 for p in players),
                "max_failed_route": max(p["failed_nonpass"] for p in players),
            }
    output = {"main_sha256": EXPECTED_SHA, "summary": summary, "rows": rows}
    OUTPUT.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(OUTPUT)


if __name__ == "__main__":
    main()
