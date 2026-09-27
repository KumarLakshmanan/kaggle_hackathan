"""Freeze the prospectively specified selector after all development games."""
import base64
import gzip
import hashlib
import json
from pathlib import Path
import sys
import zlib

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from paired_benchmark import _load_module


def metrics(margins):
    return {"wins": sum(m > 0 for m in margins), "minimum_margin": min(margins),
            "total_margin": sum(margins)}


def main():
    manifest = json.loads((HERE / "search_manifest.json").read_text(encoding="utf8"))
    data = json.loads((HERE / "search_results.json").read_text(encoding="utf8"))
    assert data["candidate_sha256"] == manifest["candidate_sha256"]
    rows = data["rows"]
    assert len(rows) == manifest["jobs"]
    assert all(row["statuses"] == ["DONE", "DONE"] for row in rows)
    selected, groups = {}, []
    for target in manifest["targets"]:
        pair = target["shops"]
        baselines = [case["baseline_seat0_margin"] for case in target["cases"]]
        baseline = metrics(baselines)
        options = []
        for episode in target["eligible"]:
            results = [r for r in rows if r["shops"] == pair and r["episode"] == episode]
            assert len(results) == len(target["cases"])
            assert {r["team"] for r in results} == {r["team"] for r in target["cases"]}
            options.append({"episode": episode, **metrics([r["margin"] for r in results]), "cases": results})
        options.sort(key=lambda r: (r["wins"], r["minimum_margin"], r["total_margin"], r["episode"]), reverse=True)
        best = options[0]
        use = best["wins"] > baseline["wins"]
        if use:
            selected["|".join(pair)] = best["episode"]
        groups.append({"shops": pair, "baseline": baseline, "selected": use, "best": best, "ranked_options": options})
        print(pair, "wins", baseline["wins"], "->", best["wins"], "use", use, "source", best["episode"], flush=True)
    (HERE / "selection.json").write_text(json.dumps({"selected": selected, "groups": groups}, indent=2, ensure_ascii=False), encoding="utf8")
    if not selected:
        print("No selector change earned full-panel testing.", flush=True)
        return
    source = ROOT / "main_uploaded_shunki_schedule_20260927_3cc0f69f.py"
    assert hashlib.sha256(source.read_bytes()).hexdigest() == manifest["source_sha256"]
    module = _load_module(source, "optimized_compile")
    catalogue = json.loads((ROOT / "diagnostics/shunki_portfolio_20260927/route_manifest.json").read_text(encoding="utf8"))
    extra = {}
    for record in catalogue["rows"]:
        episode = record["episode_id"]
        if episode in selected.values() and str(episode) not in module._DATA["routes"]:
            with gzip.open(record["route_path"], "rt", encoding="utf8") as handle:
                extra[str(episode)] = json.load(handle)["actions"]
    packed = base64.b85encode(zlib.compress(json.dumps(extra, separators=(",", ":")).encode(), 9)).decode()
    layer = f'''

# Shop-only schedule selection learned on the frozen replay development panel.
_DATA["routes"].update(json.loads(zlib.decompress(base64.b85decode({packed!r})).decode("utf8")))
_OPT_TABLE = {selected!r}
_OPT_PARENT = agent
_OPT_STATS = {{"optimized_turns": 0, "selected_route": None}}

def agent(observation, configuration=None):
    step = int(observation["step"])
    if step == 0:
        _OPT_STATS.update(optimized_turns=0, selected_route=None)
    shops = observation["town"]["unlocked_shops"]
    selected = _OPT_TABLE.get("|".join(shops[:2])) if step >= 144 else None
    if selected is not None:
        _OPT_STATS["optimized_turns"] += 1
        _OPT_STATS["selected_route"] = selected
        return copy.deepcopy(_DATA["routes"][str(selected)][min(step, 718)])
    return _OPT_PARENT(observation, configuration)

agent.telemetry = _OPT_STATS

def kaggle_shop_optimized_entrypoint(observation, configuration=None):
    return agent(observation, configuration)
'''
    candidate = ROOT / "exp_shunki_shop_optimized_20260927.py"
    raw = source.read_bytes() + layer.encode("utf8")
    compile(raw, str(candidate), "exec")
    candidate.write_bytes(raw)
    result = {"candidate": str(candidate), "candidate_sha256": hashlib.sha256(raw).hexdigest(),
              "source_sha256": manifest["source_sha256"], "selected": selected,
              "search_results_sha256": hashlib.sha256((HERE / "search_results.json").read_bytes()).hexdigest(),
              "selection_sha256": hashlib.sha256((HERE / "selection.json").read_bytes()).hexdigest(),
              "bytes": len(raw)}
    (HERE / "candidate_manifest.json").write_text(json.dumps(result, indent=2), encoding="utf8")
    print("Frozen candidate", result["candidate_sha256"], flush=True)


if __name__ == "__main__":
    main()
