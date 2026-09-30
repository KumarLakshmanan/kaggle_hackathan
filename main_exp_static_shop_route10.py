"""Validation-only static-table variant of the V54 shop route fix.

The production file currently installs a transparent router wrapper.  This
candidate restores each wrapped router to its original callable and changes
only the relevant route tables, so score and timing can be compared fairly.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("static_shop_route10_base", ROOT / "main.py")
if spec is None or spec.loader is None:
    raise RuntimeError("could not load main.py")
base = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = base
spec.loader.exec_module(base)


PAIR = ("YARN_STORE", "ICE_CREAM_SHOP")
NAMESPACES = [base.__dict__]
for name in ("_V49_EMBEDDED_NAMESPACE", "_V51_HAIDE_NAMESPACE", "_V52_RANK41_NAMESPACE"):
    namespace = getattr(base, name, None)
    if isinstance(namespace, dict):
        NAMESPACES.append(namespace)

seen = set()
for namespace in NAMESPACES:
    impl = namespace.get("_IMPL")
    if impl is None or id(impl) in seen:
        continue
    seen.add(id(impl))
    router = impl.chassis.router
    previous = getattr(router, "__kwdefaults__", {}).get("_previous")
    if callable(previous):
        impl.chassis.router = previous
    for name in ("_R108_SHOP_ROUTES", "_R110_OLD_SHOPS", "_V92_TABLE"):
        mapping = namespace.get(name)
        if isinstance(mapping, dict) and PAIR in mapping:
            mapping[PAIR] = 10


agent = base.agent
