"""Load the unchanged official farming interpreter without unrelated game SDKs.

PyPy cannot load CPython's compiled jsonschema/Parquet dependencies. The two
utility definitions needed by this interpreter are compiled verbatim from the
installed official package. This module contains no reimplementation of rules.
"""
import ast
import importlib.util
import random
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / ".bench_deps" / "kaggle_environments"
source = (PACKAGE / "utils.py").read_text(encoding="utf-8")
utils = types.ModuleType("kaggle_environments.utils")
utils.random = random
selected = [ast.get_source_segment(source, n) for n in ast.parse(source).body
            if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.name in ("Struct", "resolve_episode_seed")]
assert len(selected) == 2
exec("from __future__ import annotations\n" + "\n\n".join(selected), utils.__dict__)
package = types.ModuleType("kaggle_environments")
package.__path__ = [str(PACKAGE)]
sys.modules["kaggle_environments"] = package
sys.modules[utils.__name__] = utils
spec = importlib.util.spec_from_file_location("official_farming", PACKAGE / "envs" / "kaggriculture" / "kaggriculture.py")
engine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(engine)
Struct = utils.Struct
__version__ = "1.32.7"


def make(*args, **kwargs):
    raise RuntimeError("Full-framework verification must run under CPython")
