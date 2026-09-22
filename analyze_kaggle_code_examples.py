"""Extract comparable strategy signals from downloaded Kaggle notebooks.

This is intentionally an analysis-only helper.  It never executes notebook
cells; it reads code cells and kernel metadata so candidate policies can be
reviewed before any logic is copied into an agent.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent
ARCHIVES = [ROOT / "kaggle_top_code_2026-09-21", ROOT / "kaggle_public_code"]
OUT_JSON = ROOT / "kaggle_code_feature_analysis_2026-09-21.json"
OUT_MD = ROOT / "kaggle_code_feature_analysis_2026-09-21.md"


FEATURES = {
    "public_state_router": r"(?i)public.?state|route.?portfolio|shop.?router|router",
    "market_timing": r"(?i)sell.?tim|demand|price.?shock|market.?rhythm|sale.?window",
    "market_orders": r"(?i)BUY_SEED|BUY_ANIMAL|BUY_LAND|SELL|BUY_WHEAT",
    "worker_pacing": r"(?i)idle.?worker|farm.?hand|hire|worker|hands",
    "premium_control": r"(?i)premium|queue|PREMIUM",
    "opening_book": r"(?i)opening|first.?turn|first.?48|turn.?88|signature",
    "terminal_policy": r"(?i)terminal|liquidat|last.?day|day.?29|final.?turn",
    "preemption_counter": r"(?i)preempt|counter|opponent|mirror|hysteresis",
    "search_or_optimization": r"(?i)MCTS|Monte.?Carlo|lookahead|beam.?search|genetic|optimizer|linear.?program",
    "replay_or_clone": r"(?i)replay|clone|seed|stream|trajectory",
    "crop_economics": r"(?i)ROI|profit|yield|margin|economics|score",
    "animal_care": r"(?i)feed|care|water|escape|animal",
    "risk_guards": r"(?i)guard|fallback|safe|reserve|cash|recovery",
}


def iter_notebooks() -> list[Path]:
    found: set[Path] = set()
    for archive in ARCHIVES:
        if archive.exists():
            found.update(archive.rglob("*.ipynb"))
    return sorted(found)


def load_notebook(path: Path) -> tuple[dict, str]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}, ""
    cells = payload.get("cells") or []
    source = "\n\n".join(
        "".join(cell.get("source") or [])
        for cell in cells
        if cell.get("cell_type") == "code"
    )
    return payload, source


def metadata_for(path: Path) -> dict:
    meta_path = path.parent / "kernel-metadata.json"
    if not meta_path.exists():
        return {}
    try:
        return json.loads(meta_path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def main() -> None:
    records = []
    for path in iter_notebooks():
        notebook, source = load_notebook(path)
        if not source:
            continue
        meta = metadata_for(path)
        matched = {
            name: bool(re.search(pattern, source))
            for name, pattern in FEATURES.items()
        }
        records.append(
            {
                "path": str(path),
                "relative_path": str(path.relative_to(ROOT)),
                "id": meta.get("id"),
                "title": meta.get("title") or path.stem,
                "author": (meta.get("id") or "").split("/", 1)[0] or None,
                "code_chars": len(source),
                "code_lines": source.count("\n") + 1,
                "features": [name for name, present in matched.items() if present],
                "feature_flags": matched,
                "cell_count": len(notebook.get("cells") or []),
            }
        )

    records.sort(key=lambda row: (len(row["features"]), row["code_chars"]), reverse=True)
    feature_counts = Counter(
        feature for row in records for feature in row["features"]
    )
    author_counts = Counter(row["author"] for row in records if row["author"])
    report = {
        "generated_from": [str(p.relative_to(ROOT)) for p in ARCHIVES if p.exists()],
        "notebook_count": len(records),
        "feature_counts": dict(feature_counts.most_common()),
        "author_counts": dict(author_counts.most_common()),
        "records": records,
    }
    OUT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    lines = [
        "# Kaggle code-example feature analysis",
        "",
        f"Notebooks with readable code cells: **{len(records)}**",
        "",
        "## Feature frequency",
        "",
        "| Feature | Notebooks |",
        "|---|---:|",
    ]
    lines.extend(
        f"| `{feature}` | {count} |" for feature, count in feature_counts.most_common()
    )
    lines.extend(["", "## Highest-coverage examples", ""])
    lines.append("| Author | Title | Features | Code lines |")
    lines.append("|---|---|---:|---:|")
    for row in records[:80]:
        title = row["title"].replace("|", "\\|")
        lines.append(
            f"| {row['author'] or ''} | {title} | {len(row['features'])} | {row['code_lines']} |"
        )
    lines.extend(["", "## Archive paths", ""])
    lines.extend(f"- `{row['relative_path']}`" for row in records[:200])
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"notebooks": len(records), "feature_counts": feature_counts.most_common()}, ensure_ascii=False))


if __name__ == "__main__":
    main()
