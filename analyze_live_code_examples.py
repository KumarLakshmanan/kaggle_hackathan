"""Create a static comparison report for downloaded Kaggriculture code.

This utility only reads the local Kaggle download/extraction artifacts.  It
does not execute notebook code, contact Kaggle, or change the production
agent.  The executable benchmark results are recorded separately because
static markers alone cannot establish a stronger policy.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


MARKERS = (
    "fertilizer",
    "seed",
    "market",
    "sell",
    "buy",
    "harvest",
    "pickup",
    "weed",
    "route",
    "shock",
    "pasture",
    "milk",
    "wool",
    "timing",
    "telemetry",
)


def _rank_from_source(source: str) -> int | None:
    match = re.search(r"(?:^|[\\/])0*(\d+)-", source)
    return int(match.group(1)) if match else None


def _title_by_rank(path: Path) -> dict[int, str]:
    rows = json.loads(path.read_text(encoding="utf-8"))
    return {index + 1: str(row.get("title", row.get("ref", ""))) for index, row in enumerate(rows)}


def _ast_metrics(text: str) -> dict[str, Any]:
    try:
        tree = ast.parse(text)
    except SyntaxError as error:
        return {"parseable": False, "syntax_error": str(error)}
    imports: list[str] = []
    classes: list[str] = []
    functions: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module or "")
        elif isinstance(node, ast.ClassDef):
            classes.append(node.name)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(node.name)
    return {
        "parseable": True,
        "imports": sorted(set(imports)),
        "classes": classes,
        "functions": functions,
        "agent_definitions": sum(name == "agent" for name in functions),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--listing", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--production", type=Path, required=True)
    parser.add_argument("--markdown-out", type=Path, required=True)
    parser.add_argument("--json-out", type=Path, required=True)
    args = parser.parse_args()

    titles = _title_by_rank(args.listing)
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    extracted = [row for row in manifest.get("agents", []) if row.get("status") == "extracted"]
    records: list[dict[str, Any]] = []
    by_hash: defaultdict[str, list[int]] = defaultdict(list)
    for row in extracted:
        source_value = row.get("path") or row.get("source")
        if not source_value:
            continue
        source_path = Path(source_value)
        text = source_path.read_text(encoding="utf-8", errors="replace")
        lower = text.lower()
        rank = int(
            row.get("rank")
            or _rank_from_source(str(row.get("notebook", "")))
            or _rank_from_source(str(row.get("source", "")))
            or 0
        )
        metrics = _ast_metrics(text)
        record = {
            "rank": rank,
            "title": titles.get(rank, ""),
            "path": str(source_path.resolve()),
            "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            "bytes": len(text.encode("utf-8")),
            "lines": text.count("\n") + 1,
            "markers": {marker: lower.count(marker) for marker in MARKERS if marker in lower},
            **metrics,
        }
        records.append(record)
        by_hash[record["sha256"]].append(rank)

    production_text = args.production.read_text(encoding="utf-8", errors="replace")
    production_lower = production_text.lower()
    production = {
        "path": str(args.production.resolve()),
        "bytes": len(production_text.encode("utf-8")),
        "lines": production_text.count("\n") + 1,
        "markers": {marker: production_lower.count(marker) for marker in MARKERS if marker in production_lower},
        "sha256": hashlib.sha256(production_text.encode("utf-8")).hexdigest(),
    }
    duplicate_groups = sorted(
        (sorted(ranks) for ranks in by_hash.values() if len(ranks) > 1),
        key=lambda ranks: ranks[0],
    )
    records.sort(key=lambda row: row["rank"])
    payload = {
        "listing": str(args.listing.resolve()),
        "manifest": str(args.manifest.resolve()),
        "extracted_count": len(records),
        "unique_source_hashes": len(by_hash),
        "duplicate_rank_groups": duplicate_groups,
        "production": production,
        "records": records,
    }
    args.json_out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    lines = [
        "# Kaggriculture live code-example static comparison",
        "",
        "This report is static: it reads downloaded notebook sources and decoded literal agent payloads. It never executes notebook cells or submits to Kaggle.",
        "",
        f"- Extracted payloads: **{len(records)}**",
        f"- Unique source hashes: **{len(by_hash)}**",
        f"- Duplicate rank groups: **{', '.join(map(str, duplicate_groups)) if duplicate_groups else 'none'}**",
        f"- Production file: `{args.production.resolve()}` ({production['bytes']:,} bytes; {production['lines']:,} lines)",
        "",
        "## Extracted sources",
        "",
        "| Rank | Title | Bytes | Lines | Agent defs | Main markers | Hash |",
        "|---:|---|---:|---:|---:|---|---|",
    ]
    for record in records:
        marker_text = ", ".join(
            f"{name}={count}" for name, count in sorted(record["markers"].items(), key=lambda item: (-item[1], item[0]))[:6]
        )
        lines.append(
            f"| {record['rank']} | {record['title'].replace('|', '/')} | {record['bytes']:,} | {record['lines']:,} | {record.get('agent_definitions', 0)} | {marker_text} | `{record['sha256'][:12]}` |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "These are static source observations, not strength results. Keyword counts and parseable function structure do not establish that an agent is valid, fast, or competitive; any source selected for head-to-head testing must first be reviewed and run in a controlled benchmark.",
            "",
            "The production agent remains unchanged by this report. Experimental router files and replay benchmarks are kept separately so a future promotion can be audited against the same panel.",
            "",
        ]
    )
    args.markdown_out.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"extracted": len(records), "unique_hashes": len(by_hash), "markdown": str(args.markdown_out.resolve()), "json": str(args.json_out.resolve())}, ensure_ascii=False))


if __name__ == "__main__":
    main()
