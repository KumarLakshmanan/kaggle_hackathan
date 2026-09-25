# Imports & System Configuration
import base64
import csv
import hashlib
import io
import json
import math
import os
import re
import shutil
import sys
import time
import zipfile
from pathlib import Path
from typing import Any, Iterable, Mapping

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import requests

print("PyArrow version:", pa.__version__)
print("Pandas version:", pd.__version__)


_TEAM_NAMES_KEY_RE = re.compile(rb'"TeamNames"\s*:\s*')

def extract_team_names_from_prefix(prefix: bytes | str) -> tuple[str, ...]:
    """Extract replay info.TeamNames from a small JSON prefix (first 64 KiB).
    
    Allows scanning thousands of replay headers without decompressing step arrays.
    """
    raw = prefix.encode("utf-8") if isinstance(prefix, str) else bytes(prefix)
    match = _TEAM_NAMES_KEY_RE.search(raw)
    if match is None:
        raise RuntimeError("Replay prefix does not contain TeamNames header")
    try:
        # JSONDecoder.raw_decode parses the array and determines where it ends
        tail = raw[match.end():].decode("utf-8", errors="ignore")
        names, _ = json.JSONDecoder().raw_decode(tail)
    except Exception as exc:
        raise RuntimeError(f"Invalid TeamNames header: {exc}") from exc
        
    if not isinstance(names, list) or len(names) < 2 or any(not isinstance(x, str) or not x for x in names):
        raise RuntimeError(f"Invalid TeamNames payload: {names!r}")
    return tuple(names)

def scan_team_names_from_zip(
    zf: zipfile.ZipFile,
    manifest_rows: Iterable[Mapping[str, Any]],
    header_scan_bytes: int = 64 * 1024,
) -> tuple[dict[int, Any], dict[int, tuple[str, ...]], list[dict[str, Any]]]:
    """Scan replay headers across a daily ZIP archive in seconds."""
    entries = {}
    for info in zf.infolist():
        name = Path(info.filename).name
        if name.endswith(".json") and name[:-5].isdigit():
            entries.setdefault(int(name[:-5]), info)
            
    names_by_episode = {}
    skipped = []
    
    for row in manifest_rows:
        try:
            ep_id = int(row["episode_id"])
        except Exception:
            continue
            
        info = entries.get(ep_id)
        if info is None:
            skipped.append({"episode_id": ep_id, "reason": "missing_member"})
            continue
            
        try:
            with zf.open(info) as f:
                prefix = f.read(header_scan_bytes)
            names_by_episode[ep_id] = extract_team_names_from_prefix(prefix)
        except Exception:
            skipped.append({"episode_id": ep_id, "reason": "invalid_header"})
            
    return entries, names_by_episode, skipped


def rank_daily_teams(
    manifest_rows: Iterable[Mapping[str, Any]],
    team_names_by_episode: Mapping[int, Iterable[str]],
    top_n: int = 10,
) -> list[dict[str, Any]]:
    """Rank teams from official daily replay score evidence.
    
    Filters out noisy/low-tier games and isolates top-10 champion replays.
    """
    stats = {}
    seen_episodes = set()
    
    for raw in manifest_rows:
        ep_id = int(raw["episode_id"])
        if ep_id in seen_episodes:
            continue
        seen_episodes.add(ep_id)
        
        if ep_id not in team_names_by_episode:
            continue
            
        try:
            avg_score = float(raw["avg_score"])
            min_score = float(raw["min_score"])
        except (KeyError, TypeError, ValueError):
            continue
            
        if not (math.isfinite(avg_score) and math.isfinite(min_score)):
            continue
            
        upper_score = 2.0 * avg_score - min_score
        names = tuple(dict.fromkeys(str(x) for x in team_names_by_episode[ep_id] if str(x)))
        
        for name in names:
            row = stats.setdefault(
                name,
                {
                    "team_name": name,
                    "appearances": 0,
                    "score_proxy": float("-inf"),
                    "max_min_score": float("-inf"),
                    "max_agent_score_upper": float("-inf"),
                    "evidence_episode_id": None,
                },
            )
            row["appearances"] += 1
            candidate = (avg_score, min_score, upper_score, -ep_id)
            incumbent = (
                float(row["score_proxy"]),
                float(row["max_min_score"]),
                float(row["max_agent_score_upper"]),
                -int(row["evidence_episode_id"]) if row["evidence_episode_id"] is not None else float("-inf"),
            )
            if candidate > incumbent:
                row["score_proxy"] = avg_score
                row["max_min_score"] = min_score
                row["max_agent_score_upper"] = upper_score
                row["evidence_episode_id"] = ep_id
                
    ranked = sorted(
        stats.values(),
        key=lambda r: (
            -float(r["score_proxy"]),
            -float(r["max_min_score"]),
            -float(r["max_agent_score_upper"]),
            str(r["team_name"]),
        ),
    )
    
    out = []
    for rank, row in enumerate(ranked[:top_n], 1):
        item = dict(row)
        item["rank"] = rank
        out.append(item)
    return out


def write_replay_shard_from_zip(
    date: str,
    zf: zipfile.ZipFile,
    entries: Mapping[int, Any],
    selected_ids: list[int],
    out_dir: Path,
) -> Path:
    """Write selected episode replay bodies into a compressed Parquet shard."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    final_path = out_dir / f"replays_{date}.parquet"
    tmp_path = out_dir / f"replays_{date}.parquet.tmp"
    
    # Parquet schema: Episode ID as Int64, Replay JSON as LargeString
    schema = pa.schema([
        ("episode_id", pa.int64()),
        ("replay_json", pa.large_string()),
    ])
    
    writer = pq.ParquetWriter(tmp_path, schema, compression="zstd", compression_level=10)
    archived_ids = []
    
    try:
        for ep_id in sorted(set(selected_ids)):
            info = entries.get(ep_id)
            if info is None:
                continue
            raw = zf.read(info)
            text = raw.decode("utf-8")
            
            table = pa.Table.from_arrays([
                pa.array([ep_id], type=pa.int64()),
                pa.array([text], type=pa.large_string()),
            ], schema=schema)
            
            writer.write_table(table)
            archived_ids.append(ep_id)
    finally:
        writer.close()
        
    os.replace(tmp_path, final_path)
    print(f"✅ Saved compressed shard: {final_path.name} ({final_path.stat().st_size / 1e6:.2f} MB, {len(archived_ids)} replays)")
    return final_path


import zlib

def encode_action_tape(action_list: list) -> str:
    """Compress a list of turn-by-turn actions into a Base85 + Zlib string."""
    json_bytes = json.dumps(action_list, separators=(",", ":")).encode("utf-8")
    compressed = zlib.compress(json_bytes, level=9)
    encoded = base85_str = base64.b85decode  # placeholder check
    b85 = base64.b85encode(compressed).decode("ascii")
    return b85

def decode_action_tape(b85_str: str) -> list:
    """Decompress a Base85 + Zlib string back into a Python action list."""
    compressed = base64.b85decode(b85_str.encode("ascii"))
    json_bytes = zlib.decompress(compressed)
    return json.loads(json_bytes.decode("utf-8"))

# Quick Demonstration of Compression Efficiency
sample_actions = [{"farmer": ["MOVE", "NORTH"], "hands": [["PLANT", "WHEAT"]]} for _ in range(720)]
raw_json = json.dumps(sample_actions)
encoded_tape = encode_action_tape(sample_actions)
decoded_actions = decode_action_tape(encoded_tape)

print(f"Raw JSON Size:      {len(raw_json):,} bytes")
print(f"Compressed Base85: {len(encoded_tape):,} bytes")
print(f"Compression Ratio:  {len(raw_json) / len(encoded_tape):.2f}x smaller!")
assert sample_actions == decoded_actions, "Decoded tape matches original!"
