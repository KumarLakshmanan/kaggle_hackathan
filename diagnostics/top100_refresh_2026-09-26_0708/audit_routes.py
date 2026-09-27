"""Check that the refreshed route panel covers the leaderboard's top 100."""

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CURRENT = HERE / "routes" / "summary.json"
PRIOR = ROOT / "diagnostics" / "top100_refresh_2026-09-26" / "summary.json"
OLDER = ROOT / "diagnostics" / "top100_current_2026-09-25" / "summary.json"
OUTPUT = HERE / "route_audit.json"


def main():
    raw = (HERE / "leaderboard_snapshot.json").read_text(encoding="utf-8-sig")
    start = min(i for i in (raw.find("["), raw.find("{")) if i >= 0)
    leaderboard = json.loads(raw[start:])[:100]
    rows = json.loads(CURRENT.read_text(encoding="utf8"))
    ids = {int(x["teamId"]) for x in leaderboard}
    captured = {int(x["team_id"]) for x in rows}
    assert len(ids) == 100
    assert ids == captured, {"missing": sorted(ids - captured),
                             "extra": sorted(captured - ids)}
    assert len(rows) == 100, len(rows)
    assert all(x["num_actions"] == 719 for x in rows)
    assert all(Path(x["path"]).is_file() for x in rows)
    hashes = {x["action_sha256"] for x in rows}
    old_rows = json.loads(PRIOR.read_text(encoding="utf8"))
    older_rows = json.loads(OLDER.read_text(encoding="utf8"))
    out = {
        "leaderboard_teams": len(ids),
        "captured_routes": len(rows),
        "unique_action_hashes": len(hashes),
        "unique_source_episodes": len({x["episode_id"] for x in rows}),
        "action_hash_overlap_previous_sep26": len(hashes & {x["action_sha256"] for x in old_rows}),
        "action_hash_overlap_sep25": len(hashes & {x["action_sha256"] for x in older_rows}),
        "source_episode_overlap_previous_sep26": len({x["episode_id"] for x in rows}
                                                       & {x["episode_id"] for x in old_rows}),
    }
    OUTPUT.write_text(json.dumps(out, indent=2) + "\n", encoding="utf8")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
