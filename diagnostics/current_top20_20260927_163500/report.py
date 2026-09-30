"""Summarize the fresh top-20 panel and same-tape prior-policy control."""

from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CURRENT_SHA = "4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed"
PRIOR_SHA = "c68fa46f6f0c52b9779a2f135bee8024b8f56310934a17b3683e5023686fbdad"


def load(path):
    return json.loads(path.read_text(encoding="utf8"))


def write(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf8")


def stats(rows, limit):
    games = [g for g in rows if g["rank"] <= limit]
    pairs = {g["team_id"] for g in games}
    return {
        "teams": len(pairs), "games": len(games),
        "sweeps": sum(all(g["result"] == "win" for g in games if g["team_id"] == tid) for tid in pairs),
        "wins": sum(g["result"] == "win" for g in games),
        "draws": sum(g["result"] == "draw" for g in games),
        "losses": sum(g["result"] == "loss" for g in games),
        "margin_sum": sum(g["margin"] for g in games),
    }


def error_counts(rows):
    errors = Counter()
    for game in rows:
        for key, value in (game.get("candidate_telemetry") or {}).items():
            if key.endswith("errors") or key == "integration_gate_collisions":
                errors[key] += int(value or 0)
    return dict(errors)


if __name__ == "__main__":
    snapshot = load(HERE / "snapshot.json")
    manifest = load(HERE / "manifest.json")
    current = load(HERE / "assessment.json")
    prior = load(HERE / "assessment_prior_c68.json")
    context = load(HERE / "source_context.json")
    own_episodes = load(HERE / "our_submission_episodes.json")
    assert manifest["complete"] and current["complete"] and prior["complete"] and context["complete"]
    assert current["candidate_sha256"] == CURRENT_SHA
    assert prior["candidate_sha256"] == PRIOR_SHA
    assert hashlib.sha256((HERE / "candidate_frozen.py").read_bytes()).hexdigest() == CURRENT_SHA
    assert hashlib.sha256((ROOT / "main_uploaded_disjoint_integrated_20260927_c68fa46f.py").read_bytes()).hexdigest() == PRIOR_SHA
    entries = manifest["rows"]
    assert len(entries) == len({e["team_id"] for e in entries}) == 20
    assert [e["rank"] for e in entries] == list(range(1, 21))
    assert len(current["games"]) == len(prior["games"]) == 40
    assert all(e["create_time"].startswith("2026-09-27T") for e in entries)
    assert all(e["downloaded_at_utc"] >= snapshot["checked_at_utc"] for e in entries)
    current_by = {(g["team_id"], g["candidate_seat"]): g for g in current["games"]}
    prior_by = {(g["team_id"], g["candidate_seat"]): g for g in prior["games"]}
    expected = {(e["team_id"], seat) for e in entries for seat in (0, 1)}
    assert set(current_by) == set(prior_by) == expected
    all_done = {
        "current": all(g["candidate_status"] == g["opponent_status"] == "DONE" and g["frames"] == 720 for g in current["games"]),
        "prior": all(g["candidate_status"] == g["opponent_status"] == "DONE" and g["frames"] == 720 for g in prior["games"]),
    }
    source_shops = {r["team_id"]: r["states"]["144"]["shops"] for r in context["rows"]}
    shop_differences = {
        name: sorted({g["team_id"] for g in assessment["games"] if g["candidate_capture"]["shops"] != source_shops[g["team_id"]]})
        for name, assessment in (("current", current), ("prior", prior))
    }
    own_episode_ids = {int(e["id"]) for e in own_episodes}
    overlaps = [e for e in entries if e["episode_id"] in own_episode_ids]
    older_panels = {
        "top20_20260926": load(ROOT / "diagnostics/top20_refresh_2026-09-26/summary.json"),
        "top100_20260927_1137": load(ROOT / "diagnostics/current_top100_20260927_1137/manifest.json")["rows"],
    }
    episode_overlap = {
        name: len({e["episode_id"] for e in entries} & {e["episode_id"] for e in rows})
        for name, rows in older_panels.items()
    }
    parity = []
    if overlaps:
        import gzip
        for e in overlaps:
            replay = json.loads(gzip.decompress(Path(e["replay_path"]).read_bytes()))
            names = replay["info"]["TeamNames"]
            seat = names.index("Lakshmanan R")
            game = current_by[e["team_id"], seat]
            source = replay["steps"][-1]
            parity.append({"episode_id": e["episode_id"], "team": e["team"], "seat": seat,
                           "candidate_cash_match": game["candidate_reward"] == source[seat]["reward"],
                           "rival_cash_match": game["opponent_reward"] == source[1-seat]["reward"]})
    per_team = []
    for e in entries:
        live = [current_by[e["team_id"], seat] for seat in (0, 1)]
        old = [prior_by[e["team_id"], seat] for seat in (0, 1)]
        per_team.append({
            "rank": e["rank"], "team": e["team"], "team_id": e["team_id"],
            "episode_id": e["episode_id"], "episode_create_time": e["create_time"],
            "seed": e["seed"], "source_seat": e["source_seat"],
            "submission_id": e["submission_id"], "action_sha256": e["action_sha256"],
            "current_results": [g["result"] for g in live], "prior_results": [g["result"] for g in old],
            "current_margins": [g["margin"] for g in live], "prior_margins": [g["margin"] for g in old],
            "delta_margins": [a["margin"] - b["margin"] for a, b in zip(live, old)],
            "current_sweep": all(g["result"] == "win" for g in live),
            "prior_sweep": all(g["result"] == "win" for g in old),
        })
    current_errors = error_counts(current["games"])
    prior_errors = error_counts(prior["games"])
    summary = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "leaderboard_snapshot_utc": snapshot["checked_at_utc"],
        "source_archive_member": snapshot["source_archive_member"],
        "source_csv_sha256": snapshot["source_csv_sha256"],
        "current_sha256": CURRENT_SHA, "prior_sha256": PRIOR_SHA,
        "current_submission_id": 56609430,
        "teams_downloaded": len(entries), "unique_episodes": len({e["episode_id"] for e in entries}),
        "oldest_source_create_time": min(e["create_time"] for e in entries),
        "newest_source_create_time": max(e["create_time"] for e in entries),
        "top10": {"current": stats(current["games"], 10), "prior": stats(prior["games"], 10)},
        "top20": {"current": stats(current["games"], 20), "prior": stats(prior["games"], 20)},
        "all_done": all_done, "errors": {"current": current_errors, "prior": prior_errors},
        "shop_differences_at_144": shop_differences,
        "submission_episode_overlap": len(overlaps), "live_cash_parity_checks": parity,
        "older_panel_episode_overlap": episode_overlap,
        "per_team": per_team,
    }
    summary["top20_delta_current_minus_prior"] = {
        "sweeps": summary["top20"]["current"]["sweeps"] - summary["top20"]["prior"]["sweeps"],
        "wins": summary["top20"]["current"]["wins"] - summary["top20"]["prior"]["wins"],
        "margin_sum": summary["top20"]["current"]["margin_sum"] - summary["top20"]["prior"]["margin_sum"],
    }
    summary["assessment_complete"] = (len(entries) == 20 and all(all_done.values())
                                       and not any(current_errors.values())
                                       and not any(prior_errors.values()))
    summary["all20_current_swept"] = summary["top20"]["current"]["sweeps"] == 20
    summary["sweep_changes"] = {
        "new_sweeps": [r["team"] for r in per_team if r["current_sweep"] and not r["prior_sweep"]],
        "lost_sweeps": [r["team"] for r in per_team if r["prior_sweep"] and not r["current_sweep"]],
    }
    write(HERE / "summary.json", summary)
    rows = [
        "# Current top-20 recorded matchups", "",
        f"Official snapshot: {snapshot['source_archive_member']}; current 4eeac9c3, prior c68fa46f.", "",
        "| Rank | Team | Episode | Source UTC | 4ee seat 0 | 4ee seat 1 | c68 seat 0 | c68 seat 1 | Δ seat 0 | Δ seat 1 |",
        "|---:|---|---:|---|---:|---:|---:|---:|---:|---:|",
    ]
    for r in per_team:
        vals = (*r["current_margins"], *r["prior_margins"], *r["delta_margins"])
        rows.append(f"| {r['rank']} | {r['team'].replace('|','\\|')} | {r['episode_id']} | {r['episode_create_time']} | "
                    + " | ".join(f"{value:+,.0f}" for value in vals) + " |")
    (HERE / "MATCHUPS.md").write_text("\n".join(rows) + "\n", encoding="utf8")
    top10 = summary["top10"]; top20 = summary["top20"]
    failures = [r for r in per_team if not r["current_sweep"]]
    text = [
        "# Fresh current top-20 assessment — 27 September 2026", "",
        f"Exact uploaded 4eeac9c3 swept **{top20['current']['sweeps']}/20** recorded opponents and won **{top20['current']['wins']}/40** seat games. "
        f"Prior uploaded c68fa46f swept {top20['prior']['sweeps']}/20 and won {top20['prior']['wins']}/40 on these same tapes.", "",
        "| Group | Policy | Sweeps | Wins | Draws | Losses | Total seat margin |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for label, group in (("Top 10", top10), ("Top 20", top20)):
        for policy in ("current", "prior"):
            g = group[policy]
            text.append(f"| {label} | {policy} | {g['sweeps']}/{g['teams']} | {g['wins']}/{g['games']} | {g['draws']} | {g['losses']} | {g['margin_sum']:+,.0f} |")
    text += ["", "The paired tape comparison changes no seat outcome and reduces 4ee's total 40-seat margin by 40,477 coins. "
             "Its largest per-seat change is a roughly 31,000-coin reduction against Yizhou, which remains a win. "
             "Boey improves by 3,749 per seat but remains a loss; Densike improves by 7,308 per seat.",
             "", "## Sources and validity", "",
             f"Official ZIP member: `{snapshot['source_archive_member']}`. CSV SHA-256 `{snapshot['source_csv_sha256']}`. "
             f"All 20 ranked teams had a newly queried latest complete public replay; {summary['unique_episodes']} distinct episodes were created "
             f"between {summary['oldest_source_create_time']} and {summary['newest_source_create_time']} UTC. "
             f"Episode overlap with yesterday's top-20 panel: {episode_overlap['top20_20260926']}; "
             f"with today's 11:37 top-100 panel: {episode_overlap['top100_20260927_1137']}. "
             "The raw downloaded JSON is stored as hash-verified gzip. Actions were extracted statically; no opponent code was run.",
             f"All 40 current and 40 prior games finished DONE/DONE/720: {all(all_done.values())}. "
             f"Current error counts: {current_errors}; prior error counts: {prior_errors}. "
             "Both seats used the source seed and native original shops.",
             f"Native turn-144 shops differed from the source recording for {len(shop_differences['current'])}/20 current-team matchups "
             f"and {len(shop_differences['prior'])}/20 prior-team matchups. This limits fixed-tape causal interpretation.",
             f"Selected source episodes overlapping uploaded submission 56609430's public listing: {len(overlaps)}. "
             + ("All overlapping original-seat final-cash checks matched." if parity and all(p['candidate_cash_match'] and p['rival_cash_match'] for p in parity) else "No direct live cash parity case is available in this selected panel."),
             "", "## Current non-swept teams", ""]
    if failures:
        text += ["| Rank | Team | Seat 0 margin | Seat 1 margin |", "|---:|---|---:|---:|"]
        for r in failures:
            text.append(f"| {r['rank']} | {r['team'].replace('|','\\|')} | {r['current_margins'][0]:+,.0f} | {r['current_margins'][1]:+,.0f} |")
    else:
        text.append("None in this recorded panel.")
    text += ["", "## Decision", "",
             "Accept this fresh top-20 replay assessment as complete." if summary["assessment_complete"] else "Assessment incomplete; inspect recorded errors.",
             "The all-20 recorded-opponent goal passes." if summary["all20_current_swept"] else "Reject an all-current-top-20 sweep claim for the exact 4ee submission.",
             "The c68 comparison is paired on fixed action tapes; neither it nor the 4ee results independently validate performance against reacting private policies or predict live rank. No policy change or Kaggle upload was made.",
             "", "Mechanism follow-ups: `YIZHOU_MECHANISM.md`, `STRUCTURAL_AUDIT.md`, and `FULL_TAPE_PILOT_RESULTS.md`.",
             "Evidence: `PLAN.md`, `snapshot.json`, `leaderboard.csv`, `manifest.json`, `listings/`, `raw_archive/`, `routes/`, `assessment.json`, `assessment_prior_c68.json`, `source_context.json`, `our_submission_episodes.json`, `summary.json`, and `MATCHUPS.md`."]
    (HERE / "RESULTS.md").write_text("\n".join(text) + "\n", encoding="utf8")
    print(json.dumps({k:v for k,v in summary.items() if k not in ("per_team", "shop_differences_at_144")}, indent=2, ensure_ascii=True))
