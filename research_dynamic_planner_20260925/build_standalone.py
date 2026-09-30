"""Mechanically bundle the readable policy; no compression or encoded data."""

from __future__ import annotations

import argparse
import ast
import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def top_names(source):
    result = set()
    for node in ast.parse(source).body:
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            result.add(node.name)
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                if isinstance(target, ast.Name):
                    result.add(target.id)
    return result


def build(output):
    economic = (ROOT / "economics.py").read_text(encoding="utf-8")
    policy = (ROOT / "candidate.py").read_text(encoding="utf-8")
    begin = policy.index("_ECON_SPEC =")
    end = policy.index("_ECON_SPEC.loader.exec_module(_ECON)", begin)
    end += len("_ECON_SPEC.loader.exec_module(_ECON)")
    policy = policy[:begin]+policy[end:]
    policy = policy.replace("_ECON.", "")
    collisions = top_names(economic) & top_names(policy)
    if collisions:
        raise ValueError("Resolve shared top-level names before bundling: "+str(sorted(collisions)))
    economic = economic.replace("from __future__ import annotations", "")
    policy = policy.replace("from __future__ import annotations", "")
    source = ('"""Standalone daily farm planner. Experimental; not submitted.\n'
              'Generated from readable economics.py and candidate.py.\n"""\n\n'
              'from __future__ import annotations\n\n'
              '# ECONOMIC MODEL\n\n'+economic+'\n\n# WORKER AND FARM PLANNER\n\n'+policy)
    ast.parse(source)
    output.write_text(source, encoding="utf-8")
    print(str(output.resolve()))
    print(hashlib.sha256(output.read_bytes()).hexdigest())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "standalone.py")
    build(parser.parse_args().output)
