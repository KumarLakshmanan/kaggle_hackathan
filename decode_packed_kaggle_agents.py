"""Safely decode packed Kaggle notebook sources without executing them.

This tool parses notebook cells and evaluates only a tiny whitelist of literal
operations used by public submissions (base64/base85, gzip, zlib, and string
joins).  It never imports or executes downloaded candidate code.
"""

from __future__ import annotations

import argparse
import ast
import base64
import gzip
import hashlib
import json
import re
import zlib
from pathlib import Path
from typing import Any


def _source(cell: dict[str, Any]) -> str:
    return "".join(cell.get("source", []) or [])


def _literal(node: ast.AST, env: dict[str, Any]) -> Any:
    if isinstance(node, ast.Constant) and isinstance(node.value, (str, bytes, int)):
        return node.value
    if isinstance(node, ast.Name) and node.id in env:
        return env[node.id]
    if isinstance(node, (ast.Tuple, ast.List)):
        return type(node.elts)([_literal(item, env) for item in node.elts])
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left, right = _literal(node.left, env), _literal(node.right, env)
        if type(left) is type(right) and isinstance(left, (str, bytes)):
            return left + right
    if isinstance(node, ast.Call):
        fn = node.func
        args = [_literal(arg, env) for arg in node.args]
        if isinstance(fn, ast.Attribute) and isinstance(fn.value, ast.Constant) and fn.attr == "join":
            if isinstance(fn.value.value, str) and len(args) == 1:
                return fn.value.value.join(args[0])
        if isinstance(fn, ast.Attribute) and isinstance(fn.value, ast.Name):
            module, name = fn.value.id, fn.attr
            if len(args) != 1:
                raise ValueError("unsupported arity")
            value = args[0]
            if module == "base64" and name == "b85decode" and isinstance(value, str):
                return base64.b85decode(value)
            if module == "base64" and name == "b64decode" and isinstance(value, str):
                return base64.b64decode(value)
            if module == "gzip" and name == "decompress" and isinstance(value, bytes):
                return gzip.decompress(value)
            if module == "zlib" and name == "decompress" and isinstance(value, bytes):
                return zlib.decompress(value)
        if isinstance(fn, ast.Attribute) and isinstance(fn.value, ast.Name) and fn.attr == "decode":
            value = args[0] if args else None
            if isinstance(value, bytes):
                return value.decode("utf-8")
    raise ValueError("not a whitelisted literal expression")


def _decode_candidates(value: Any) -> list[bytes]:
    candidates: list[bytes] = []
    if isinstance(value, bytes):
        candidates.append(value)
    if isinstance(value, str) and len(value) >= 1000:
        for decoder in (base64.b85decode, base64.b64decode):
            try:
                raw = decoder(value)
            except Exception:
                continue
            candidates.append(raw)
            for decompressor in (gzip.decompress, zlib.decompress):
                try:
                    candidates.append(decompressor(raw))
                except Exception:
                    pass
    return candidates


def _find_payload(code: str) -> tuple[bytes, str] | None:
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return None
    env: dict[str, Any] = {}
    values: list[tuple[str, Any]] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        value_node = node.value
        try:
            value = _literal(value_node, env)
        except Exception:
            continue
        for target in targets:
            if isinstance(target, ast.Name):
                env[target.id] = value
                values.append((target.id, value))
    for name, value in values:
        for payload in _decode_candidates(value):
            if not isinstance(payload, bytes) or len(payload) < 10000:
                continue
            try:
                text = payload.decode("utf-8")
            except UnicodeDecodeError:
                continue
            if not re.search(r"(?m)^\s*def\s+(?:agent|kaggle_submission_agent)\s*\(", text):
                continue
            try:
                ast.parse(text)
            except SyntaxError:
                continue
            return payload, name
    return None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    for notebook in sorted(args.archive.rglob("*.ipynb")):
        row: dict[str, Any] = {"notebook": str(notebook)}
        try:
            data = json.loads(notebook.read_text(encoding="utf-8"))
            code = "\n".join(_source(cell) for cell in data.get("cells", []) if cell.get("cell_type") == "code")
            found = _find_payload(code)
            if found is None:
                row["status"] = "no_safe_packed_agent"
            else:
                payload, variable = found
                label = re.sub(r"[^A-Za-z0-9_.-]+", "_", notebook.parent.name)
                destination = args.output / f"{label}__packed.py"
                destination.write_bytes(payload)
                text = payload.decode("utf-8")
                row.update({
                    "status": "decoded",
                    "source": str(destination),
                    "variable": variable,
                    "bytes": len(payload),
                    "lines": text.count("\n") + 1,
                    "sha256": hashlib.sha256(payload).hexdigest(),
                })
        except Exception as exc:  # noqa: BLE001 - continue auditing all notebooks
            row.update({"status": "error", "error": repr(exc)})
        rows.append(row)
    manifest = {"archive": str(args.archive.resolve()), "rows": rows, "decoded": sum(r.get("status") == "decoded" for r in rows)}
    (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"notebooks": len(rows), "decoded": manifest["decoded"], "output": str(args.output.resolve())}))


if __name__ == "__main__":
    main()
