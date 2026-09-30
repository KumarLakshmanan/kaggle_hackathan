"""Regenerate policy files with only rank, visible-shop history, and actions."""

from __future__ import annotations

from datetime import datetime, timezone
import base64
import gzip
import hashlib
import json
from pathlib import Path
import sys
import zlib

HERE = Path(__file__).resolve().parent
SOURCE_DIR = HERE.parents[0] / "fresh90_refresh_20260929"
SUMMARY_PATH = SOURCE_DIR / "routes" / "development_latest" / "summary.json"
EXPECTED_SUMMARY_SHA = "9dc48578eb5e828d8038ff39821c8e27ddb12b1a7a4812a87622003c2db63e9c"


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")


def main() -> None:
    sys.path.insert(0, str(HERE))
    import build_candidates

    plan_sha = sha((HERE / "PLAN.md").read_bytes())
    expected_plan_sha = (HERE / "PLAN_SHA256.txt").read_text(encoding="utf-8").splitlines()[0].split()[0].lower()
    if plan_sha != expected_plan_sha:
        raise RuntimeError("frozen plan hash mismatch")
    summary_raw = SUMMARY_PATH.read_bytes()
    summary_sha = sha(summary_raw)
    if summary_sha != EXPECTED_SUMMARY_SHA:
        raise RuntimeError("frozen development summary hash mismatch")
    source_rows = json.loads(summary_raw.decode("utf-8"))
    source_by_rank = {int(row["rank"]): row for row in source_rows}
    analysis_path = HERE / "family_analysis.json"
    analysis = json.loads(analysis_path.read_text(encoding="utf-8"))
    for declared in analysis["selected_candidates"]:
        tapes = []
        for source in declared["embedded_tapes"]:
            row = source_by_rank[int(source["rank"])]
            if int(row["episode_id"]) != int(source["episode_id"]):
                raise RuntimeError(f"rank/episode changed for rank {source['rank']}")
            route_path = Path(row["path"])
            payload = json.loads(gzip.decompress(route_path.read_bytes()))
            actions = payload["actions"]
            action_hash = sha(canonical(actions))
            if action_hash != row["action_sha256"] or action_hash != source["action_sha256"]:
                raise RuntimeError(f"source action hash mismatch for rank {source['rank']}")
            shop_history = declared["family"]["shop_histories"][str(source["rank"])]
            tapes.append({"rank": int(source["rank"]), "shop_history": shop_history, "actions": actions})
        if len(tapes) != int(declared["embedded_tape_count"]):
            raise RuntimeError(f"tape count mismatch for candidate {declared['candidate_id']}")
        packed = base64.b85encode(zlib.compress(canonical(tapes), level=9)).decode("ascii")
        base_rank = int(declared["base_rank"])
        source_text = build_candidates.ROUTER_TEMPLATE.replace("__PACKED__", packed).replace("__BASE_RANK__", str(base_rank))
        candidate_path = Path(declared["candidate_path"])
        candidate_path.write_text(source_text, encoding="utf-8")
        raw = candidate_path.read_bytes()
        declared["candidate_sha256"] = sha(raw)
        declared["candidate_bytes"] = len(raw)
        declared["policy_payload_fields"] = ["rank", "shop_history", "actions"]
        declared["policy_uses_seed_or_opponent_identity"] = False
        declared["embedded_tapes"] = [{**source, "route_path": str(Path(source["route_path"]).resolve())}
                                       for source in declared["embedded_tapes"]]

    analysis["candidates_regenerated_at_utc"] = datetime.now(timezone.utc).isoformat()
    analysis["candidate_policy_payload_fields"] = ["rank", "shop_history", "actions"]
    analysis["candidate_policy_selection_keys"] = ["physical_prefix_match", "visible_shop_history", "frozen_rank"]
    analysis["candidate_policy_seed_or_opponent_identity_used"] = False
    analysis_path.write_text(json.dumps(analysis, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"analysis": str(analysis_path.resolve()),
                      "candidates": [{"path": c["candidate_path"], "sha256": c["candidate_sha256"],
                                      "bytes": c["candidate_bytes"], "base_rank": c["base_rank"],
                                      "family_ranks": c["family"]["member_ranks"],
                                      "policy_fields": c["policy_payload_fields"]}
                                     for c in analysis["selected_candidates"]]}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
