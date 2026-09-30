"""Describe frozen standalone-policy outcomes without changing their gates."""
from collections import Counter
from hashlib import sha256
from pathlib import Path
import json

HERE = Path(__file__).resolve().parent


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def render():
    pilot = json.loads((HERE / "pilot.json").read_text())
    full = json.loads((HERE / "full.json").read_text())
    pool = json.loads((HERE / "pool.json").read_text())
    assert full["complete"] and pilot["complete"]
    assert full["pool_sha256"] == pilot["pool_sha256"] == digest(HERE / "pool.json")
    assert full["helper_sha256"] == digest(HERE / "screen.py")
    assert len(full["games"]) == 200 and len(pilot["games"]) == 60
    assert len({(g["version"], g["fixture_id"], g["candidate_seat"]) for g in full["games"]}) == 200
    lines = [
        "# Complete whole-opening donor study — 28 September 2026", "",
        "The three exact standalone policies began their own donor schedules at turn 0. "
        "After the 60-game pilot, shared150 failed the frozen top-control gate. "
        "The unchanged shared151 and shared166 candidates completed all 50 saved targets in both seats. "
        "Their 40 exact pilot games were reused and 160 additional games were run, for 220 unique games across this study. "
        "These are saved-tape development results, not independent validation against reacting opponents.", "",
        "Source 367d2e76 sweeps 19/20 top fixtures and 13/30 public-loss fixtures. "
        "The frozen full-stage gate requires at least 18/20 and 14/30, respectively, plus clean execution.", "",
        "| Candidate | Top sweeps | Public-loss sweeps | Clean | Frozen decision |",
        "| --- | ---: | ---: | --- | --- |",
    ]
    for s in full["summaries"]:
        lines.append(f"| {s['version']} | {s['both_seat_wins']['top20']}/20 | "
                     f"{s['both_seat_wins']['loss30']}/30 | {s['clean']} | "
                     f"{'Advances research only' if s['passed'] else 'Reject replacement'} |")
    lines += ["| shared150 | 0/3 pilot controls | 4/7 pilot donors | True | Reject at pilot; no full panel |", ""]
    for s in full["summaries"]:
        version = s["version"]
        games = [g for g in full["games"] if g["version"] == version]
        pairs = {fid: sorted([g for g in games if g["fixture_id"] == fid], key=lambda g: g["candidate_seat"])
                 for fid in sorted({g["fixture_id"] for g in games})}
        assert all(len(pair) == 2 for pair in pairs.values())
        lost = [fid for fid, pair in pairs.items()
                if all(g["parent_result"] == "win" for g in pair) and any(g["result"] != "win" for g in pair)]
        branches = Counter((g["candidate_telemetry"]["donor_pair144"],
                            g["candidate_telemetry"]["donor_selected"],
                            g["candidate_telemetry"]["donor_default_branch"]) for g in games)
        default_seats = sum(g["candidate_telemetry"]["donor_default_branch"] for g in games)
        lines += ["## " + version, "", "Candidate SHA-256: `" + pool["arms"][version]["candidate_sha256"] + "`.", "",
                  "New both-seat public rescues: " + (", ".join(s["new_public_rescues"]) or "none") + ".", "",
                  f"Lost source both-seat wins: {len(lost)} fixtures; {len(s['lost_source_winning_seats'])} previously winning seats.", "",
                  "Lost source sweep fixtures: " + (", ".join(lost) or "none") + ".", "",
                  f"Unmapped observed shop pairs use the predeclared default in {default_seats}/100 seats. "
                  "Archived donor shop labels did not guarantee the same realized shops in these counterfactual games.", "",
                  "### Every fixture and paired cash effect", "",
                  "Margins and changes list seat 0 / seat 1. Own and rival changes are relative to exact source 367d2e76.", "",
                  "| Fixture | Source margins | Candidate margins | Own cash change | Rival cash change | Both seats win |",
                  "| --- | ---: | ---: | ---: | ---: | --- |"]
        for fid, pair in pairs.items():
            fmt = lambda key: " / ".join(f"{g[key]:.0f}" for g in pair)
            lines.append(f"| {fid} | {fmt('parent_margin')} | {fmt('margin')} | {fmt('delta_own')} | "
                         f"{fmt('delta_rival')} | {all(g['result'] == 'win' for g in pair)} |")
        lines += ["", "### Observed selection coverage", "",
                  "| Observed first / second shop | Route | Default fallback | Seats |", "| --- | --- | --- | ---: |"]
        for (shops, route, fallback), count in sorted(branches.items()):
            lines.append(f"| {shops.replace('|', ' / ')} | {route} | {fallback} | {count} |")
        lines += [""]
    lines += ["## Evidence and limits", "",
              "No source/main edits, promotion, Kaggle access or native/reacting outcome games were performed. "
              "All three standalone candidates remain preserved as possible diverse reacting references. "
              "Original-framework native schema/timeout checks and actual file-loader compatibility remain pending. "
              "Fast games verify full native transitions and recorded telemetry only; they exclude the framework wrapper. "
              "The common initial-procurement feasibility audit is a separate static artifact in INITIAL_OBLIGATIONS.md; "
              "it does not change these candidates or their decisions.", "",
              "The two pre-game memory interruptions and exact checkpoint resumes are recorded in RUN_STATE.md. "
              "No completed outcome was repeated or counted twice.", "",
              "Full receipt SHA-256: `" + digest(HERE / "full.json") + "`.",
              "Pilot receipt SHA-256: `" + digest(HERE / "pilot.json") + "`.",
              "Pool SHA-256: `" + digest(HERE / "pool.json") + "`.",
              "Screen helper SHA-256: `" + digest(HERE / "screen.py") + "`.",
              "Completed UTC: " + full["completed_at_utc"] + ".", ""]
    (HERE / "RESULTS.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"full_sha256": digest(HERE / "full.json"),
                      "summaries": [dict(version=s["version"], passed=s["passed"], clean=s["clean"],
                                         both_seat_wins=s["both_seat_wins"],
                                         new_public_rescues=s["new_public_rescues"],
                                         lost_source_winning_seats=len(s["lost_source_winning_seats"]))
                                    for s in full["summaries"]]}, indent=2))


if __name__ == "__main__":
    render()
