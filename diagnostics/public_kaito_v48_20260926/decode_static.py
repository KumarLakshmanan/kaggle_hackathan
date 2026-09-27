"""Extract embedded public source as data; never execute the downloaded code."""

import ast
import base64
import json
from pathlib import Path
import zlib


ROOT = Path(__file__).resolve().parent
TREE = ast.parse((ROOT / "decoded_untrusted.py.txt").read_text(encoding="utf-8"))


def compressed_strings(variable):
    assignment = next(
        node
        for node in TREE.body
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == variable for target in node.targets)
    )
    decoder = next(
        node
        for node in ast.walk(assignment.value)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "b85decode"
    )
    pieces = [node.value for node in ast.walk(decoder.args[0]) if isinstance(node, ast.Constant) and isinstance(node.value, str)]
    return zlib.decompress(base64.b85decode("".join(pieces))).decode("utf-8")


modules = json.loads(compressed_strings("_V48_MODULES"))
for name, source in modules.items():
    target = ROOT / "modules" / (name.replace(".", "/") + ".py.txt")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(source, encoding="utf-8")
    print(name, len(source), source.count("\n"))

routes = json.loads(compressed_strings("_V48_ROUTES"))
(ROOT / "routes_untrusted.json").write_text(json.dumps(routes, indent=2), encoding="utf-8")
print("routes", type(routes).__name__, len(routes))
