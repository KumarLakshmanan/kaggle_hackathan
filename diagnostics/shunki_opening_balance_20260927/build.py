import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
screen = json.loads((HERE/"screen.json").read_text(encoding="utf8"))
selected = screen["selected"]
assert selected["eligible"] and selected["mean_liquid_delta"] > 0
quantity = selected["quantity"]
source = ROOT/"main_uploaded_shunki_schedule_20260927_3cc0f69f.py"
assert hashlib.sha256(source.read_bytes()).hexdigest() == screen["source_sha256"]
layer = f'''
# Gross opening trade selected on two-turn accounting, not terminal outcomes.
_DATA["opening"][0]["market"][0][2] = {quantity}
_DATA["opening"][0]["market"][1][2] = {quantity-4}

def kaggle_opening_balance_entrypoint(observation, configuration=None):
    return agent(observation, configuration)
'''
raw = source.read_bytes()+layer.encode("utf8")
target = ROOT/"exp_shunki_opening_balance_20260927.py"
compile(raw, str(target), "exec")
target.write_bytes(raw)
digest = hashlib.sha256(raw).hexdigest()
backup = ROOT/("main_candidate_opening_balance_20260927_"+digest[:8]+".py")
backup.write_bytes(raw)
manifest = {"candidate_sha256": digest, "backup": str(backup), "quantity": quantity,
            "source_sha256": screen["source_sha256"], "plan_sha256": screen["plan_sha256"],
            "screen_sha256": hashlib.sha256((HERE/"screen.json").read_bytes()).hexdigest()}
(HERE/"manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf8")
print(json.dumps(manifest))
