"""Targeted diagnostic on an already tested seed; not independent strength validation."""
import copy
import gzip
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from paired_benchmark import _load_module, make


def differences(expected, actual, prefix=""):
    rows = []
    if isinstance(expected, dict) and isinstance(actual, dict):
        for key in sorted(set(expected) | set(actual)):
            if key not in expected or key not in actual:
                rows.append({"path": prefix + "/" + key, "expected": expected.get(key), "actual": actual.get(key)})
            else:
                rows.extend(differences(expected[key], actual[key], prefix + "/" + key))
    elif isinstance(expected, list) and isinstance(actual, list) and len(expected) == len(actual):
        for i, (left, right) in enumerate(zip(expected, actual)):
            rows.extend(differences(left, right, prefix + "/" + str(i)))
    elif expected != actual:
        rows.append({"path": prefix, "expected": expected, "actual": actual})
    return rows


if __name__ == "__main__":
    manifest = json.loads((HERE / "build_manifest.json").read_text())
    source = manifest["sources"][0]
    raw = Path(source["replay_path"]).read_bytes()
    replay = json.loads(gzip.decompress(raw))
    candidate = _load_module(Path(manifest["candidate"]), "prefix_diagnostic")
    rival = _load_module(ROOT / "main_uploaded_disjoint_integrated_20260927_c68fa46f.py", "prefix_diagnostic_rival")
    captured = {}

    def observe(observation, configuration):
        step = int(observation["step"])
        if step <= 73:
            captured[step] = copy.deepcopy(observation)
        return candidate.agent(observation, configuration)

    try:
        env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 2693000}, debug=False)
        env.run([observe, rival.agent])
        rows = []
        seat = source["source_seat"]
        for step, actual in captured.items():
            expected = replay["steps"][step][seat]["observation"]
            delta = differences({"farm": expected["farms"][seat], "private": expected["private"]},
                                {"farm": actual["farms"][0], "private": actual["private"]})
            rows.append({"step": step, "differences": delta,
                         "actual_wheat_price": actual["market"]["prices"]["WHEAT"],
                         "recorded_action": replay["steps"][step+1][seat]["action"]})
        result = {"seed": 2693000, "seat": 0, "independent_validation": False,
                  "source_episode": source["episode_id"], "candidate_sha256": manifest["candidate_sha256"],
                  "rows": rows, "captured_72": captured[72], "source_72": replay["steps"][72][seat]["observation"]}
        (HERE / "prefix_diagnostic.json").write_text(json.dumps(result, indent=2), encoding="utf8")
        for row in rows:
            if row["step"] >= 67 or any(d["path"].startswith("/private") for d in row["differences"]) and row["step"] <= 12:
                print(json.dumps(row), flush=True)
    finally:
        sys.modules.pop(candidate.__name__, None)
        sys.modules.pop(rival.__name__, None)
