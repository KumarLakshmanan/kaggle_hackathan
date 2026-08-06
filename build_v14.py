"""Build the standalone V14 agent from a compact public action tape."""

from __future__ import annotations

import argparse
import ast
import base64
import gzip
import hashlib
import importlib.util
import json
import zlib
from pathlib import Path


def _assignment(tree: ast.Module, name: str) -> ast.Assign:
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == name for target in node.targets
        ):
            return node
    raise RuntimeError(f"Assignment {name!r} not found")


def _load_module(path: Path):
    spec = importlib.util.spec_from_file_location(f"verify_{path.stem}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def build(base_path: Path, route_path: Path, output_path: Path) -> dict[str, str | int]:
    with gzip.open(route_path, "rt", encoding="utf-8") as handle:
        route_payload = json.load(handle)
    actions = route_payload.get("actions", [])
    if len(actions) != 719:
        raise RuntimeError(f"Expected 719 route actions, found {len(actions)}")

    action_bytes = json.dumps(
        actions, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")
    action_sha256 = hashlib.sha256(action_bytes).hexdigest()
    encoded = base64.b85encode(zlib.compress(action_bytes, level=9)).decode("ascii")
    chunks = [encoded[index : index + 104] for index in range(0, len(encoded), 104)]
    encoded_lines = "\n".join(f"                {chunk!r}" for chunk in chunks)
    replacement = (
        "_ACTIONS = json.loads(\n"
        "    zlib.decompress(\n"
        "        base64.b85decode(\n"
        "            (\n"
        f"{encoded_lines}\n"
        "            ).encode(\"ascii\")\n"
        "        )\n"
        "    ).decode(\"utf-8\")\n"
        ")\n"
        f"_ROUTE_ACTION_SHA256 = {action_sha256!r}\n"
        "_ARCHITECTURE = \"V14 complete route + order-safe shift-and-repay\"\n"
    )

    source = base_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    action_node = _assignment(tree, "_ACTIONS")
    doc_node = tree.body[0]
    if not (
        isinstance(doc_node, ast.Expr)
        and isinstance(doc_node.value, ast.Constant)
        and isinstance(doc_node.value.value, str)
        and doc_node.end_lineno is not None
    ):
        raise RuntimeError("Expected a module docstring in the base agent")
    if action_node.end_lineno is None:
        raise RuntimeError("Python parser did not provide assignment end line")
    lines = source.splitlines(keepends=True)
    source = (
        "\"\"\"V14 Kaggriculture complete-route agent.\n\n"
        "The 719-turn route is transcribed from public replay actions. Runtime\n"
        "uses only the current legal observation. Safety layers provide hand\n"
        "alignment, bounded weed repair, SELL clamping, order-safe one-turn\n"
        "premium shifts with exact next-turn repayment, and final liquidation.\n"
        "\"\"\"\n"
        + "".join(lines[doc_node.end_lineno : action_node.lineno - 1])
        + replacement
        + "".join(lines[action_node.end_lineno :])
    )
    artifact = source.encode("utf-8")
    compile(artifact, str(output_path), "exec")
    output_path.write_bytes(artifact)

    module = _load_module(output_path)
    if module._ACTIONS != actions:
        raise RuntimeError("Generated action tape does not match compact route")
    if module._ROUTE_ACTION_SHA256 != action_sha256:
        raise RuntimeError("Generated route hash mismatch")
    if not module._PREEMPT_ENABLED or module._PREEMPT_FRACTION != 2.0:
        raise RuntimeError("Expected validated R3 tactical settings")

    return {
        "output": str(output_path.resolve()),
        "bytes": len(artifact),
        "sha256": hashlib.sha256(artifact).hexdigest(),
        "route_action_sha256": action_sha256,
        "actions": len(actions),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--route", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.base, args.route, args.output), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
