import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
source = ROOT / "exp_shunki_trade_quantity_20260927.py"
assert hashlib.sha256(source.read_bytes()).hexdigest() == "6e09adf8a2760ad3983c6308fdb83ffa40677a179746eab0c34bb164e3388540"
raw = source.read_bytes() + b"\n\n" + (HERE / "layer.py").read_bytes()
target = ROOT / "exp_shunki_mirror_quantity_20260927.py"
compile(raw, str(target), "exec")
assert not target.exists(); target.write_bytes(raw)
digest = hashlib.sha256(raw).hexdigest()
backup = ROOT / ("main_candidate_mirror_quantity_20260927_" + digest[:8] + ".py")
assert not backup.exists(); backup.write_bytes(raw)
manifest = {"candidate": str(target), "candidate_sha256": digest, "backup": str(backup),
            "construction_source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "baseline": "a2d2869c", "plan_sha256": hashlib.sha256((HERE / "PLAN.md").read_bytes()).hexdigest()}
(HERE / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf8")
prior_path = ROOT / "diagnostics/shunki_market_queue_20260927/top50.json"
prior = json.loads(prior_path.read_text(encoding="utf8"))
excluded = []
for row in prior["rows"]:
    for game in row["games"]:
        farms = game["candidate_capture"]["farms"]
        assert farms[0]["occupied"] != farms[1]["occupied"]
        excluded.append({"team": row["team"], "seat": game["candidate_seat"], "margin": game["margin"]})
assert len(excluded) == 100
(HERE / "top50_exclusion_proof.json").write_text(json.dumps({"candidate_sha256": digest,
    "prior_results_sha256": hashlib.sha256(prior_path.read_bytes()).hexdigest(), "new_games": 0,
    "reused_games": 100, "sweeps": 43, "seat_wins": 86, "excluded": excluded,
    "proof": "Exact a2 through143; every saved step144 occupied-tile comparison differs, so the quantity branch never enables."}, indent=2, ensure_ascii=False), encoding="utf8")
pilot_source = (ROOT / "diagnostics/shunki_trade_quantity_20260927/development.py").read_text(encoding="utf8")
pilot = pilot_source.replace("exp_shunki_trade_quantity_20260927.py", "exp_shunki_mirror_quantity_20260927.py")
pilot = pilot.replace("2674000", "2686000").replace("2674008", "2686008").replace("max_workers=4", "max_workers=2")
pilot = pilot.replace('("quantity_errors", "queue_errors")', '("quantity_errors", "queue_errors", "mirror_quantity_errors")')
(HERE / "development.py").write_text(pilot, encoding="utf8")
print(json.dumps(manifest))
