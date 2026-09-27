"""Check whether optimized schedules can safely respond to later shops."""
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent


if __name__ == "__main__":
    catalogue = json.loads((ROOT / "diagnostics/shunki_portfolio_20260927/route_manifest.json").read_text(encoding="utf8"))["rows"]
    histories = {r["episode_id"]: r["reveals"] for r in json.loads((ROOT / "diagnostics/shunki_portfolio_20260927/shop_sequences.json").read_text(encoding="utf8"))["rows"]}
    selected = json.loads((HERE / "candidate_manifest.json").read_text(encoding="utf8"))["selected"]
    actions, hashes = {}, {}
    wanted = {tuple(histories[e]["144"]) for e in selected.values()}
    for rec in catalogue:
        ep = rec["episode_id"]
        if ep == 113445495 or tuple(histories[ep]["144"]) not in wanted:
            continue
        with gzip.open(rec["route_path"], "rt", encoding="utf8") as f:
            actions[ep] = json.load(f)["actions"]
        hashes[ep] = {str(step): hashlib.sha256(json.dumps(actions[ep][144:step], sort_keys=True, separators=(",", ":")).encode()).hexdigest()
                      for step in range(216, 577, 72)}
    rows = []
    for branch, start in selected.items():
        family = [e for e in actions if histories[e]["144"] == histories[start]["144"]]
        options = {}
        for step in range(216, 577, 72):
            options[str(step)] = [{"episode": ep, "source_shops": histories[ep][str(step)]}
                                  for ep in family if ep != start and hashes[ep][str(step)] == hashes[start][str(step)]]
        rows.append({"actual_branch": branch, "selected_episode": start, "source_branch": histories[start]["144"],
                     "family_size": len(family), "compatible_after_144": options})
        print(branch, "source family", len(family), "compatible alternatives", {k: len(v) for k, v in options.items()}, flush=True)
    (HERE / "late_compatibility_audit.json").write_text(json.dumps({"rows": rows}, indent=2), encoding="utf8")
