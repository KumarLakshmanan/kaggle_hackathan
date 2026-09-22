"""Statically recover compressed agent payloads from pulled notebooks.

This parser never executes notebook/source code.  It evaluates only literal
string concatenations and standard compression/base-encoding wrappers, then
checks recovered bytes for an agent function before writing them.
"""

from __future__ import annotations

import argparse
import ast
import base64
import gzip
import hashlib
import io
import json
import re
import tarfile
import zlib
from pathlib import Path
from typing import Any


def _literal(node: ast.AST) -> Any:
    if isinstance(node, ast.Constant) and isinstance(node.value, (str, bytes)):
        return node.value
    if isinstance(node, (ast.Tuple, ast.List)):
        return type(node.elts)([_literal(item) for item in node.elts])
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        return _literal(node.left) + _literal(node.right)
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
        if node.func.attr == "join" and len(node.args) == 1:
            values = _literal(node.args[0])
            if isinstance(values, (tuple, list)):
                if all(isinstance(item, bytes) for item in values):
                    return b"".join(values)
                if all(isinstance(item, str) for item in values):
                    return "".join(values)
        if len(node.args) == 1:
            value = _literal(node.args[0])
            if isinstance(value, str):
                value = value.encode("ascii")
            if isinstance(value, bytes):
                if node.func.attr == "b64decode":
                    return base64.b64decode(value)
                if node.func.attr == "b85decode":
                    return base64.b85decode(value)
                if node.func.attr == "a85decode":
                    return base64.a85decode(value)
                if node.func.attr == "decompress" and isinstance(node.func.value, ast.Name):
                    if node.func.value.id == "gzip":
                        return gzip.decompress(value)
                    if node.func.value.id == "zlib":
                        return zlib.decompress(value)
    raise ValueError("not a static literal")


def _candidate_values(tree: ast.AST) -> list[tuple[str, bytes]]:
    values: list[tuple[str, bytes]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        names = [target.id for target in node.targets if isinstance(target, ast.Name)]
        if not names:
            continue
        name = names[0]
        if not re.search(r"(?:BLOB|B64|GZ|ARCHIVE|PAYLOAD|SOURCE)", name, re.I):
            continue
        try:
            value = _literal(node.value)
        except ValueError:
            continue
        if isinstance(value, str):
            value = value.encode("ascii")
        if isinstance(value, bytes) and len(value) >= 64:
            values.append((name, value))
    return values


def _decoded_variants(value: bytes) -> list[bytes]:
    variants = [value]
    for decoder in (base64.b64decode, base64.b85decode, base64.a85decode):
        try:
            decoded = decoder(value)
        except Exception:  # noqa: BLE001 - try the other static wrappers
            continue
        variants.append(decoded)
    expanded = list(variants)
    for item in variants:
        for decoder in (gzip.decompress, zlib.decompress):
            try:
                expanded.append(decoder(item))
            except Exception:  # noqa: BLE001 - format probe
                pass
    return expanded


def _payloads(value: bytes) -> list[tuple[str, bytes]]:
    result: list[tuple[str, bytes]] = []
    seen: set[str] = set()
    queue = [("literal", value)]
    for label, item in list(queue):
        for suffix, decoded in (("", item),):
            digest = hashlib.sha256(decoded).hexdigest()
            if digest in seen:
                continue
            seen.add(digest)
            result.append((label + suffix, decoded))
        for index, decoded in enumerate(_decoded_variants(item)):
            digest = hashlib.sha256(decoded).hexdigest()
            if digest not in seen:
                queue.append((f"{label}/decoded{index}", decoded))
    # Probe one more layer for nested base64/compression wrappers.
    for label, item in list(queue):
        for index, decoded in enumerate(_decoded_variants(item)):
            digest = hashlib.sha256(decoded).hexdigest()
            if digest not in seen:
                seen.add(digest)
                result.append((f"{label}/nested{index}", decoded))
    return result


def _agent_bytes(payload: bytes) -> list[tuple[str, bytes]]:
    found: list[tuple[str, bytes]] = []
    if re.search(rb"(?m)^\s*def\s+(?:agent|kaggle_submission_agent)\s*\(", payload):
        found.append(("payload.py", payload))
    try:
        with tarfile.open(fileobj=io.BytesIO(payload), mode="r:*") as archive:
            for member in archive.getmembers():
                if not member.isfile() or not member.name.lower().endswith((".py", ".txt")):
                    continue
                handle = archive.extractfile(member)
                if handle is None:
                    continue
                data = handle.read()
                if re.search(rb"(?m)^\s*def\s+(?:agent|kaggle_submission_agent)\s*\(", data):
                    found.append((member.name, data))
    except (tarfile.TarError, OSError):
        pass
    return found


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sources", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    rows = []
    for source in sorted(args.sources.rglob("*.py")):
        rank_match = re.search(r"(?:^|[\\/])([0-9]{3})-", str(source))
        if not rank_match:
            continue
        rank = int(rank_match.group(1))
        try:
            tree = ast.parse(source.read_text(encoding="utf-8"))
            recovered = []
            for variable, literal in _candidate_values(tree):
                for label, payload in _payloads(literal):
                    for member, data in _agent_bytes(payload):
                        digest = hashlib.sha256(data).hexdigest()
                        if digest in {item["sha256"] for item in recovered}:
                            continue
                        recovered.append({"member": member, "sha256": digest, "bytes": len(data), "data": data})
            if not recovered:
                rows.append({"rank": rank, "source": str(source), "status": "not_recovered"})
                continue
            # Prefer a payload literally named main.py, then the largest source.
            chosen = sorted(recovered, key=lambda item: (item["member"].lower() != "main.py", -item["bytes"]))[0]
            destination = args.output / f"{rank:03d}-embedded-{chosen['sha256'][:12]}.py"
            destination.write_bytes(chosen["data"])
            rows.append({
                "rank": rank,
                "source": str(source),
                "status": "extracted",
                "member": chosen["member"],
                "sha256": chosen["sha256"],
                "bytes": chosen["bytes"],
                "path": str(destination.resolve()),
            })
        except Exception as error:  # noqa: BLE001 - preserve corpus progress
            rows.append({"rank": rank, "source": str(source), "status": "error", "error": repr(error)})
    manifest = {"sources": str(args.sources.resolve()), "agents": rows}
    manifest["extracted"] = sum(row.get("status") == "extracted" for row in rows)
    (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps({"sources": len(rows), "extracted": manifest["extracted"]}))


if __name__ == "__main__":
    main()
