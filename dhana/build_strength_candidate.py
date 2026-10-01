"""Build a standalone Dhana candidate, retaining upstream source and notices.

The source snapshot and this small builder make the generated policy auditable.
No replay file or seed is an input to this build.
"""
import ast
import argparse
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def build(promote=False, expected_hash=None):
    source = (ROOT / "main.py").read_text(encoding="utf-8-sig")
    lines = source.splitlines(keepends=True)
    changes = []
    for node in ast.parse(source).body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "_V53_RANK41_SOURCE" for t in node.targets):
            if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                changes.append((node.lineno-1, node.end_lineno, "# Disabled V53 policy source omitted; V52 policy retained.\n_V53_RANK41_SOURCE = None\n"))
        if not isinstance(node, ast.FunctionDef) or node.name != "agent":
            continue
        body = ast.get_source_segment(source, node)
        if "base_action = _V52_BASE_AGENT(" in body:
            replacement = '''def agent(observation, configuration=None):
    # Both controllers see the shared prefix; the step-72 selection is permanent.
    step = int(observation.get("step", 0))
    if step > 72:
        if _v52_use_rank41_for(observation):
            try:
                return _v52_copy.deepcopy(_V52_RANK41_AGENT(observation, configuration))
            except Exception:
                return _V52_BASE_AGENT(observation, configuration)
        return _V52_BASE_AGENT(observation, configuration)
    base_action = _V52_BASE_AGENT(observation, configuration)
    try:
        rank41_action = _V52_RANK41_AGENT(observation, configuration)
        if _v52_use_rank41_for(observation):
            return _v52_copy.deepcopy(rank41_action)
    except Exception:
        pass
    return base_action
'''
            changes.append((node.lineno-1, node.end_lineno, replacement))
        elif "main_action = _V51_MAIN_AGENT(" in body:
            replacement = '''def agent(observation, configuration=None):
    step = int(observation.get("step", 0))
    if step > 72:
        if _v51_use_main_for(observation):
            return _V51_MAIN_AGENT(observation, configuration)
        try:
            return _v51_copy.deepcopy(_V51_HAIDE_AGENT(observation, configuration))
        except Exception:
            return _V51_MAIN_AGENT(observation, configuration)
    main_action = _V51_MAIN_AGENT(observation, configuration)
    try:
        haide_action = _V51_HAIDE_AGENT(observation, configuration)
        return main_action if _v51_use_main_for(observation) else _v51_copy.deepcopy(haide_action)
    except Exception:
        return main_action
'''
            changes.append((node.lineno-1, node.end_lineno, replacement))
    assert len(changes) == 3
    for start, end, replacement in sorted(changes, reverse=True):
        lines[start:end] = [replacement]
    overlay = (ROOT / "dhana" / "market_overlay.py").read_text(encoding="utf-8")
    candidate = "# Dhana upgrade: selected-controller execution, efficient opening and idle recovery.\n" + "".join(lines) + "\n" + overlay
    compile(candidate, "dhana/candidate.py", "exec")
    target = ROOT / "dhana" / "candidate.py"
    target.write_text(candidate, encoding="utf-8")
    print(target, target.stat().st_size)
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    print("SHA256", digest)
    if promote:
        if not expected_hash or digest != expected_hash.lower():
            raise ValueError("Promotion requires the exact tested --expected-sha256")
        root_digest = hashlib.sha256((ROOT / "main.py").read_bytes()).hexdigest()
        if root_digest != "16da7a84cfdf4a659c42d2abf3eb41738e93da7e2b0fd4df7f8f241f6b845759":
            raise ValueError("Root control changed; revalidate before promotion")
        current = ROOT / "dhana" / "main.py"
        before = current.read_bytes()
        if hashlib.sha256(before).hexdigest() != "fc7a3bdc325ebfeecf4a54755dc0bf077f3aa871b7aaed5c1d0534e98b47b692":
            raise ValueError("Dhana main.py changed since baseline; refusing to overwrite")
        backup = ROOT / "dhana" / "backups" / "main_before_strength_20260922.py"
        backup.parent.mkdir(parents=True, exist_ok=True)
        if backup.exists() and backup.read_bytes() != before:
            raise ValueError("Backup path already contains different data")
        if not backup.exists():
            backup.write_bytes(before)
        current.write_bytes(target.read_bytes())
        print("PROMOTED", current, "BACKUP", backup)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--promote", action="store_true")
    parser.add_argument("--expected-sha256")
    args = parser.parse_args()
    build(args.promote, args.expected_sha256)
