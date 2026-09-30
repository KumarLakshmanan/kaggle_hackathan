import base64
import hashlib
import json
from pathlib import Path
import zlib

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
ITEMS = {"CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL"}


def signature(farm):
    return ",".join(str(int(x)+10*int(y)) for x, y in [farm["farmer"], *farm["hands"]])


if __name__ == "__main__":
    source = ROOT / "exp_shunki_shop_optimized_20260927.py"
    assert hashlib.sha256(source.read_bytes()).hexdigest() == "94f0602f0a6a2d4c1af84f8caf93ee802335582485dd2f796a8c7e5a09846604"
    rows = json.loads((ROOT / "diagnostics/top50_refresh_20260927_2303/routes/summary.json").read_text(encoding="utf8"))
    model, provenance = {}, []
    for row in rows:
        raw = Path(row["replay_path"]).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == row["replay_sha256"]
        replay = json.loads(raw)
        seat = row["source_seat"]
        positions = [signature(frame[seat]["observation"]["farms"][seat]) for frame in replay["steps"][:719]]
        actions = [frame[seat]["action"] for frame in replay["steps"][1:]]
        for step in range(144, 719):
            hist = positions[step-7:step+1]
            if len(set(hist)) < 3:
                continue
            key = hashlib.sha256((str(step)+":"+"|".join(hist)).encode()).hexdigest()[:24]
            sales = {}
            for order in actions[step].get("market", []):
                if len(order) >= 3 and order[0] == "SELL" and order[1] in ITEMS:
                    sales[order[1]] = sales.get(order[1], 0) + int(order[2])
            if key not in model:
                model[key] = sales
            else:
                model[key] = {item: min(qty, sales[item]) for item, qty in model[key].items()
                              if item in sales and min(qty, sales[item]) > 0}
        provenance.append({"replay": row["replay_path"], "sha256": row["replay_sha256"]})
    model = {key: value for key, value in model.items() if value}
    packed = base64.b85encode(zlib.compress(json.dumps(model, separators=(",", ":")).encode(), 9)).decode()
    prefix = "\n_SALE_MODEL = json.loads(zlib.decompress(base64.b85decode(" + repr(packed) + ")).decode())\n"
    raw = source.read_bytes() + prefix.encode() + (HERE / "layer.py").read_bytes()
    target = ROOT / "exp_shunki_sale_model_20260927.py"
    compile(raw, str(target), "exec")
    target.write_bytes(raw)
    manifest = {"candidate": str(target), "candidate_sha256": hashlib.sha256(raw).hexdigest(),
                "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                "model_keys": len(model), "bytes": len(raw), "provenance": provenance}
    (HERE / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf8")
    print("Sale model", len(model), "keys", manifest["candidate_sha256"], flush=True)
