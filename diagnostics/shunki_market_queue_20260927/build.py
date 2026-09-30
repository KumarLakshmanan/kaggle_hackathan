"""Embed just the installed engine's market functions and their dependencies."""
import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
source = ROOT/"main_uploaded_shunki_schedule_20260927_3cc0f69f.py"
assert hashlib.sha256(source.read_bytes()).hexdigest() == "3cc0f69fcb9f6a8bee17bf6789f0f321a17f0d47324c462def1e783d6921a603"
engine = Path(r"C:/Users/Veeramani Selvaraj/AppData/Local/Programs/Python/Python314/Lib/site-packages/kaggle_environments/envs/kaggriculture/kaggriculture.py")
engine_text = engine.read_text(encoding="utf8")
tree = ast.parse(engine_text)
constants = {"CROPS", "ANIMALS", "PRODUCTS", "MARKET_I0", "PRICE_FLOOR", "MARKET_PARAMS",
             "HINGE_GAIN", "LAND_ORDER", "LAND_PRICES", "FARM_HAND_COST_MULT"}
functions = {"get", "_shape", "market_price", "_refresh_prices", "_shed_access_tiles",
             "_quadrant_of", "_spawn_hand", "_process_market", "_parse_order", "_commit_unit",
             "_fib", "_hire_cost", "_do_hire", "_do_buy_land"}
segments = ["# Market semantics from Kaggle/kaggle-environments, Apache-2.0, installed version 1.32.7.", "import math"]
found = set()
for node in tree.body:
    name = node.name if isinstance(node, ast.FunctionDef) else node.targets[0].id if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name) else None
    if name in constants | functions:
        segments.append(ast.get_source_segment(engine_text, node))
        found.add(name)
assert found == constants | functions, (constants | functions)-found
model = "\n\n".join(segments)+"\n"
compile(model, "market_model", "exec")
(HERE/"engine_market_model.py.txt").write_text(model, encoding="utf8")
funding_source = (ROOT/"diagnostics/shunki_land_prefund_20260927/layer.py").read_text(encoding="utf8")
stock_fn = next(n for n in ast.parse(funding_source).body if isinstance(n, ast.FunctionDef) and n.name == "_fund_stock")
stock_source = ast.get_source_segment(funding_source, stock_fn).replace("_fund_stock", "_queue_stock").replace("_FUND_ANIMAL", "_QUEUE_ANIMALS")
layer = "\n\n_QUEUE_ENGINE = {}\nexec("+repr(model)+", _QUEUE_ENGINE)\n_QUEUE_ANIMALS = _QUEUE_ENGINE['ANIMALS']\n\n"+stock_source+"\n\n"+(HERE/"layer.py").read_text(encoding="utf8")
raw = source.read_bytes()+layer.encode("utf8")
target = ROOT/"exp_shunki_market_queue_20260927.py"
compile(raw, str(target), "exec")
target.write_bytes(raw)
digest = hashlib.sha256(raw).hexdigest()
backup = ROOT/("main_candidate_market_queue_20260927_"+digest[:8]+".py")
backup.write_bytes(raw)
manifest = {"candidate_sha256": digest, "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "plan_sha256": hashlib.sha256((HERE/"PLAN.md").read_bytes()).hexdigest(), "backup": str(backup),
            "engine_file_sha256": hashlib.sha256(engine.read_bytes()).hexdigest(), "embedded_functions": sorted(found)}
(HERE/"manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf8")
print(json.dumps(manifest))
