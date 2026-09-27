"""Fresh-terminal confirmation, reusing only outcome-blind prefix scans."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
PRIOR = ROOT / "diagnostics/shunki_route_search_20260927/native"
sys.path.insert(0, str(ROOT))
from diagnostics.shunki_route_search_20260927 import confirm_native as runner

# Every worker imports this wrapper before receiving a job, applying the same
# frozen configuration while retaining fresh per-game policy module loading.
runner.HERE = HERE
runner.OUT = HERE / "native"
runner.NEW = ROOT / "exp_shunki_shop_pruned_20260927.py"
runner.RIVALS = {key: value for key, value in runner.RIVALS.items() if key != "old08aa"}
runner.BRANCHES = [key for key in runner.BRANCHES if key != "BAKERY|PET_CAFE"]
runner.MAX_SCAN = 4096
runner.__file__ = __file__

terminal = json.loads((PRIOR / "early_rejection.json").read_text(encoding="utf8"))["rows"]
EXCLUDED = {rival: {row["seed"] for row in terminal if row["rival"] == rival} for rival in runner.RIVALS}


def selected_rows(scanned):
    return {branch: [row for row in scanned if "|".join(row["shops"]) == branch
                     and row["seed"] not in EXCLUDED[row["rival"]]][:runner.NEEDED]
            for branch in runner.BRANCHES}


original_summary = runner.summarize


def summarize(rows, panels):
    result = original_summary(rows, panels)
    checks = result["checks"]
    del checks["all_448_games"]
    del checks["no_external_rival_loses_over_two_points"]
    del checks["head_to_head_at_least_20_of_32"]
    checks["all_240_games"] = len(rows) == 240
    checks["no_external_rival_loses_over_one_point"] = all(result["summary"][key]["new"]["paired_points"] >=
                                                         result["summary"][key]["old"]["paired_points"] - 1
                                                         for key in ("old489", "public_c95"))
    checks["head_to_head_at_least_16_of_24"] = result["summary"]["submitted3cc"]["new"]["paired_points"] >= 16
    checks["all_terminal_seeds_fresh"] = all(row["seed"] not in EXCLUDED[row["rival"]] for row in rows)
    result["gate_pass"] = all(checks.values())
    return result


runner.selected_rows = selected_rows
runner.summarize = summarize


if __name__ == "__main__":
    runner.OUT.mkdir(exist_ok=True)
    provenance = {"excluded_terminal_seeds": {k: sorted(v) for k, v in EXCLUDED.items()},
                  "prior_rejection_sha256": hashlib.sha256((PRIOR / "early_rejection.json").read_bytes()).hexdigest(),
                  "reused_harness_sha256": hashlib.sha256((ROOT / "diagnostics/shunki_route_search_20260927/confirm_native.py").read_bytes()).hexdigest(),
                  "prefix_sources": {}}
    for rival in runner.RIVALS:
        source = PRIOR / (rival + "_selection.json")
        prior = json.loads(source.read_text(encoding="utf8"))
        provenance["prefix_sources"][rival] = {"path": str(source), "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                                                "prefixes": len(prior["scanned"])}
        target = runner.OUT / (rival + "_selection.json")
        if not target.exists():
            target.write_text(json.dumps({"scanned": prior["scanned"], "selected": selected_rows(prior["scanned"])}, indent=2), encoding="utf8")
    provenance_path = runner.OUT / "prefix_provenance.json"
    if provenance_path.exists():
        assert json.loads(provenance_path.read_text(encoding="utf8")) == provenance
    else:
        provenance_path.write_text(json.dumps(provenance, indent=2), encoding="utf8")
    runner.main()
