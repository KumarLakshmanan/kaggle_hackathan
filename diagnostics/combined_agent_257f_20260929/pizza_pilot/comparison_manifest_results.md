# pilot paired comparison

Status: **complete**. Candidate SHA-256: `ae349d83276976906626f7b59bc6bd3c41d286bc51854c26a6a8b25caf999abb`. Baseline: `257f941d06fcd6dd9185ca58bc98d1af83dc4c3fafc24e275a1bf057b61bad55`.
Evaluation: fixed saved-replay action tapes; preservation evidence only.

| Case | Group / opponent | Baseline source | Seed / seat | Baseline WDL | Baseline own / rival | Baseline margin | Candidate WDL | Candidate own / rival | Candidate margin | Margin Δ | Native status / frames: baseline → candidate | Errors: baseline / candidate | Max calls: baseline / candidate |
|---|---|---|---:|:---:|---:|---:|:---:|---:|---:|---:|---|---|---|
| live-114218866-seat0 | target / saved tape | native_rerun | 1310278052 / 0 | loss | 120144 / 174100 | -53956 | loss | 107828 / 116493 | -8665 | +45291 | DONE/DONE/720 → DONE/DONE/720 | none / none | candidate 213.75 ms / candidate 154.74 ms |
| live-114218866-seat1 | target / saved tape | native_rerun | 1310278052 / 1 | loss | 120144 / 174100 | -53956 | loss | 107828 / 116493 | -8665 | +45291 | DONE/DONE/720 → DONE/DONE/720 | none / none | candidate 197.46 ms / candidate 147.77 ms |
| live-114249897-seat0 | control / saved tape | native_rerun | 2104832039 / 0 | win | 124604 / 96750 | 27854 | win | 124604 / 96750 | 27854 | +0 | DONE/DONE/720 → DONE/DONE/720 | none / none | candidate 281.07 ms / candidate 238.54 ms |
| live-114249897-seat1 | control / saved tape | native_rerun | 2104832039 / 1 | win | 124604 / 96750 | 27854 | win | 124604 / 96750 | 27854 | +0 | DONE/DONE/720 → DONE/DONE/720 | none / none | candidate 249.73 ms / candidate 201.77 ms |

Rows: 4. Baseline W-D-L: 2-0-2 (2 points); candidate W-D-L: 2-0-2 (2 points); mean paired margin Δ: +22645.50.
