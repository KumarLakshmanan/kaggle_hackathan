"""Write an audit report from completed, hash-matched evaluation artifacts."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "benchmark_results"


def read(name):
    return json.loads((RESULTS / name).read_text(encoding="utf-8"))


def key(row):
    return row["opponent"], row["seed"], row["seat"]


def main():
    candidate = ROOT / "dhana" / "candidate.py"
    digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
    assert candidate.read_bytes() == (ROOT / "dhana/main.py").read_bytes(), "Promoted source differs"
    manifest = json.loads((ROOT / "analysis_artifacts/dhana_strength/manifest.json").read_text(encoding="utf-8"))
    archive_file = "dhana_v3_archive_200.json"
    archive_checkpoint = read(archive_file)
    if archive_checkpoint["complete"] and archive_checkpoint["summary"]["games"] == manifest["route_count"] * 2:
        archive_label = f"Full local replay archive: {manifest['route_count']:,} routes, both seats"
    else:
        archive_label = "Archive sample: 100 routes, both seats"
    suites = [("Root development/validation: 40 seeds, both seats", "dhana_v3_root_80.json"),
              ("Root final holdout: 20 fresh seeds, both seats", "dhana_v3_holdout_40.json"),
              ("Standalone replay panel: 58 routes, both seats", "dhana_v3_json_116.json"),
              (archive_label, archive_file)]
    lines = ["# Dhana strength audit — 2026-09-23", "",
             "This is a measured upgrade, not an unbeatable-agent claim. Root `main.py` is unchanged.", "",
             "## Implementation", "",
             "The old Dhana nearest-replay policy is replaced by the root's stronger V52/V51 multi-policy base, "
             "with upstream notices retained. A permanent step-72 selection now stops running unused controllers. "
             "Both controllers still receive the entire prefix, alternate actions remain detached copies, "
             "and selected-controller failures have a fallback. Unused, disabled V53 source is omitted.", "",
             "The recognized opening changes BUY 20 / SELL 15 wheat to BUY 15 / SELL 10. "
             "Net wheat remains five and the subsequent seed purchase is preserved. While trailing on cash, "
             "idle/redundant worker commands can collect already-available renewable output or fertilizer; "
             "stock pressure and the final liquidation phase disable this recovery. Useful care, movement and planting are not replaced.", "",
             "The new overlay uses current public farms and the player's own private inventory, not test seeds, "
             "episode identifiers, opponent private inventory or future observations. The inherited base still contains its precomputed policy tapes.", "",
             "## Completed evaluations", "",
             "All scores below use kaggle-environments 1.32.7, standard 720-step games and PYTHONHASHSEED=0. "
             "The runner uses the installed, unmodified official game interpreter. A win means strictly higher terminal reward; ties are separate.", "",
             "| Suite | Wins | Draws | Losses | Win rate | Mean margin | Worst margin |",
             "|---|---:|---:|---:|---:|---:|---:|"]
    loaded = {}
    for label, filename in suites:
        result = read(filename)
        assert result["complete"] and result["candidate_sha256"] == digest, filename
        assert result["summary"]["all_done"], filename
        assert all(not r["exceptions"] and not r["telemetry"].get("overlay_errors", 0) for r in result["rows"]), filename
        loaded[filename] = result
        s = result["summary"]
        lines.append(f"| {label} | {s['wins']}/{s['games']} | {s['draws']} | {s['losses']} | {100*s['wins']/s['games']:.2f}% | {s['mean_margin']:+.2f} | {s['min_margin']:+.0f} |")
    root_rows = loaded["dhana_v3_root_80.json"]["rows"] + loaded["dhana_v3_holdout_40.json"]["rows"]
    paired = {}
    for row in root_rows:
        paired.setdefault(row["seed"], []).append(row["margin"])
    assert all(len(v) == 2 for v in paired.values())
    paired_scores = [sum(v) for v in paired.values()]
    lines += ["", f"Across all root games: {sum(r['margin'] > 0 for r in root_rows)}/{len(root_rows)} individual wins. "
              f"Summing both seat margins per seed gives {sum(v > 0 for v in paired_scores)}/{len(paired_scores)} "
              f"positive paired score totals ({sum(v == 0 for v in paired_scores)} ties, {sum(v < 0 for v in paired_scores)} negative totals). "
              "A positive two-seat total is NOT the same as winning every individual game.", "",
              "The first 80 games were used for development/validation, including retuning after failures; "
              "they are not independent held-out evidence. The final 40 games use System.Random(20260923) seeds "
              "generated after fixing the final source and parameters, without subsequent retuning. "
              "Repeated development runs are not included again in the displayed totals.", ""]
    before = read("dhana_before_replay_panel.json")
    lines += [f"Old Dhana on the same standalone replay panel: {before['summary']['wins']}/"
              f"{before['summary']['games']} wins, {before['summary']['losses']} losses.", ""]
    old_archive = read("dhana_before_archive_200.json")
    assert old_archive["complete"]
    assert old_archive["candidate_sha256"] == "fc7a3bdc325ebfeecf4a54755dc0bf077f3aa871b7aaed5c1d0534e98b47b692"
    s = old_archive["summary"]
    lines += [f"Old Dhana on the identical 200-game archive sample: {s['wins']}/{s['games']} wins, "
              f"{s['draws']} draws, {s['losses']} losses, mean margin {s['mean_margin']:+.2f}.", ""]
    control = read("root_archive_control_200.json")
    assert control["complete"]
    index = {key(r): r for r in control["rows"]}
    sample = [r for r in loaded["dhana_v3_archive_200.json"]["rows"] if key(r) in index]
    assert set(index) == {key(r) for r in sample}
    gains = [r["margin"] - index[key(r)]["margin"] for r in sample]
    changed_wins = sum(r["margin"] > 0 >= index[key(r)]["margin"] for r in sample)
    changed_losses = sum(r["margin"] <= 0 < index[key(r)]["margin"] for r in sample)
    s = control["summary"]
    lines += [f"Unchanged root on the identical first 100 archive routes: {s['wins']}/{s['games']} wins, "
              f"{s['draws']} draws, {s['losses']} losses, mean margin {s['mean_margin']:+.2f}. "
              f"Dhana's matched mean margin change: {sum(gains)/len(gains):+.2f}; "
              f"{changed_wins} root non-wins became wins, {changed_losses} root wins became non-wins. "
              "This is a comparison against recorded opponents, distinct from live head-to-head against root.", ""]
    parity = read("dhana_v3_official_verify.json")
    assert parity["complete"] and parity["candidate_sha256"] == digest
    assert all(r["fast"]["rewards"] == r["official"]["rewards"] for r in parity["parity_checks"])
    lines += ["Fast-runner rewards/statuses exactly matched the full official Kaggle runner in both seats "
              "on seed 2147483646. Sixteen unit tests cover overlay safeguards, no input/action mutation, "
              "controller warm-up/selection, detached action copies and exception fallback. "
              "Timing numbers in JSON reports are diagnostic only: suites ran concurrently, so they are not a controlled speed benchmark.", "",
              "## Coverage and limitations", ""]
    full_archive = (loaded["dhana_v3_archive_200.json"]["complete"] and
                    loaded["dhana_v3_archive_200.json"]["summary"]["games"] == manifest["route_count"] * 2)
    if full_archive:
        lines += [f"Full archive match evaluation finished: {loaded['dhana_v3_archive_200.json']['summary']['games']:,} games "
                  "across every extracted route in both seats.", ""]
    if full_archive:
        archive_scope = (f"**All {manifest['route_count']:,} extracted routes were match-tested in both seats "
                        f"({loaded['dhana_v3_archive_200.json']['summary']['games']:,} games).** This covers every replay body found locally, "
                        "after collapsing exact action-and-seed duplicates.")
    else:
        archive_scope = ("**The entire archive has NOT been match-tested.** The current evaluation uses 100 evenly spaced routes "
                        "from the hash-sorted manifest (200 games).")
    lines += [f"All four local archive Parquet shards were read, plus best_replay, failed_replay, dhana/fail and live_routes. "
              f"Extraction found {manifest['episodes']:,} replay episodes and {manifest['route_count']:,} distinct action/seed routes, "
              f"with {len(manifest['skipped'])} skipped extraction records. Both recorded players were extracted. "
              "Exact action-and-seed duplicates were collapsed; metadata-only episode listings are not replay bodies.", "",
              archive_scope, "The archive sample was selected from a hash-sorted local manifest, not a random leaderboard sample. "
              "It overlaps development data. Replaying fixed action tapes does not reproduce an opponent's live adaptation. "
              "The 1.32.6 replay actions were re-executed under 1.32.7 rather than retaining their historical scores. "
              "Observed losses disprove a universal 100% win-rate claim. Unseen agents, seeds, engine/configuration changes "
              "and hosted resource limits remain risks.", "",
              "Rejected experiments include larger opening reductions (which changed later market interactions), "
              "unconditional idle recovery and early/late sale changes that regressed validation cases.", "",
              "## Reproduce", "", "```powershell",
              "$env:PYTHONHASHSEED='0'",
              "$py = 'C:\\Users\\GIGABYTE\\.cache\\codex-runtimes\\codex-primary-runtime\\dependencies\\python\\python.exe'",
              "& $py -B dhana/build_strength_candidate.py",
              "& $py -B -m unittest dhana/test_strength.py -v",
              "& $py -B dhana/strength_lab.py --candidate dhana/main.py --seeds 42 2147483646 --workers 4 --output benchmark_results/recheck_root.json",
              "& $py -B dhana/strength_lab.py --candidate dhana/main.py --manifest analysis_artifacts/dhana_strength/json_manifest.json --workers 4 --output benchmark_results/recheck_json.json",
              "# Full archive run: potentially several hours. --resume skips every completed game in the output file.",
              "& $py -B dhana/strength_lab.py --candidate dhana/main.py --manifest analysis_artifacts/dhana_strength/manifest.json --workers 6 --resume --output benchmark_results/dhana_v3_archive_200.json",
              "```", "",
              "Evaluation-only dependencies live in ignored .bench_deps (kaggle-environments 1.32.7, jsonschema, pyarrow, "
              "requests, structlog, pysimdjson). The submitted main.py uses its inherited standard-library implementation; "
              "do not submit the development tools or .bench_deps.", "",
              "## Provenance", "",
              f"Final candidate SHA-256: `{digest}`.", "",
              "Root control SHA-256: `16da7a84cfdf4a659c42d2abf3eb41738e93da7e2b0fd4df7f8f241f6b845759`.", "",
              "Old Dhana SHA-256: `fc7a3bdc325ebfeecf4a54755dc0bf077f3aa871b7aaed5c1d0534e98b47b692`. "
              "Promotion keeps this exact source at dhana/backups/main_before_strength_20260922.py.", "",
              "Detailed result files (with every seed, seat, score and source hash):"]
    for _, filename in suites:
        lines.append(f"- [{filename}](../benchmark_results/{filename})")
    for filename in ("root_archive_control_200.json", "dhana_before_replay_panel.json", "dhana_before_archive_200.json", "dhana_v3_official_verify.json"):
        lines.append(f"- [{filename}](../benchmark_results/{filename})")
    target = ROOT / "dhana" / "STRENGTH_REPORT.md"
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(target)


if __name__ == "__main__":
    main()
