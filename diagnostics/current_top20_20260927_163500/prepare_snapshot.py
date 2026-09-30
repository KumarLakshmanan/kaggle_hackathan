"""Parse the freshly downloaded official leaderboard ZIP without executing it."""

from datetime import datetime, timezone
import csv
import hashlib
import io
import json
from pathlib import Path
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
EXPECTED = "4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed"


def sha256(data):
    return hashlib.sha256(data).hexdigest()


if __name__ == "__main__":
    assert not (HERE / "snapshot.json").exists()
    candidate = (ROOT / "main.py").read_bytes()
    assert sha256(candidate) == EXPECTED
    (HERE / "candidate_frozen.py").write_bytes(candidate)
    archive_bytes = (HERE / "kaggriculture.zip").read_bytes()
    with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
        names = [n for n in archive.namelist() if n.lower().endswith(".csv")]
        assert len(names) == 1, names
        csv_bytes = archive.read(names[0])
    (HERE / "leaderboard.csv").write_bytes(csv_bytes)
    rows = list(csv.DictReader(io.StringIO(csv_bytes.decode("utf-8-sig"))))
    selected = [
        {"rank": int(row["Rank"]), "teamId": int(row["TeamId"]),
         "teamName": row["TeamName"], "score": float(row["Score"]),
         "self_control": int(row["TeamId"]) == 16674353}
        for row in rows if 1 <= int(row["Rank"]) <= 20
    ]
    assert len(selected) == len({row["teamId"] for row in selected}) == 20
    assert [row["rank"] for row in selected] == list(range(1, 21))
    (HERE / "top20_teams.json").write_text(
        json.dumps(selected, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    snapshot = {
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": "Official Kaggle competitions leaderboard kaggriculture -d",
        "source_archive_member": names[0],
        "source_zip_sha256": sha256(archive_bytes),
        "source_csv_sha256": sha256(csv_bytes),
        "candidate_sha256": EXPECTED,
        "submission_id": 56609430,
        "rows_in_csv": len(rows),
        "top20_team_ids": [row["teamId"] for row in selected],
    }
    (HERE / "snapshot.json").write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
    print(json.dumps({"snapshot": snapshot, "teams": selected}, indent=2, ensure_ascii=False))
