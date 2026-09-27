"""Read Kaggle's zip in memory because its CSV name contains a Windows colon."""

import csv
import io
import json
from pathlib import Path
import zipfile


ARCHIVE = Path(__file__).with_name("kaggriculture.zip")


def main():
    with zipfile.ZipFile(ARCHIVE) as zipped:
        csv_name = next(name for name in zipped.namelist() if name.endswith(".csv"))
        with zipped.open(csv_name) as handle:
            rows = list(csv.DictReader(io.TextIOWrapper(handle, encoding="utf-8-sig")))
    print("csv", csv_name, "rows", len(rows))
    print("fields", list(rows[0]))
    for number, row in enumerate(rows, 1):
        if number <= 10 or any("Lakshmanan" in str(value) for value in row.values()):
            print(number, json.dumps(row, ensure_ascii=False))
    for score in (2200.6, 2166.7):
        better = sum(float(row["Score"]) > score for row in rows if row.get("Score"))
        print("score", score, "indicative_rank", better + 1)


if __name__ == "__main__":
    main()
