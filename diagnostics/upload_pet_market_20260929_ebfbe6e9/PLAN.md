# ebf Pet Market local file-loader verification

## Scope

This package contains an exact copy of ebf as `main.py` and a one-shot local
direct/file-loader parity checker. It has no uploader. Root owns any future
submission, and must wait for the separately coordinated fresh qualification
to pass before running this checker or considering an upload.

The current saved ebf outcome receipt is complete but `passed: false`: its
historical static WHEAT expectation is stale for both `live-114274897` seats.
The live candidate telemetry in that receipt records public WHEAT as `9980`
on those seats (the saved panel expected `9975`). This package uses the live
receipt telemetry as the expected value and asserts `9980`; it does not rewrite
the panel, receipt, or prior result. A future qualification must independently
resolve the receipt gate before this candidate is described as qualified.

## Frozen six-seat coverage

The checker selects these rows from the hash-bound panel and joins them to the
candidate's completed outcome receipt:

| Fixture | Seats | Expected behavior |
| --- | --- | --- |
| `live-114260122` | 0, 1 | Pet gate active at step 72; key `PET_CAFE|M8+|C>S|G0`, rival MELON 12, WHEAT 9975, route `113517834`, 647 active calls. |
| `live-114274897` | 0, 1 | Pet gate inactive; observed WHEAT 9980 from the live receipt; source Brunch pasture leaf route `113332529`, 647 calls. |
| `top20-20-Densike-114270616` | 0, 1 | Inactive top20 control; Pet gate inactive, WHEAT 9976, no Pet or pasture leaf route. |

For each seat, the checker runs the same fixed opponent action tape once with
the candidate imported directly and once through Kaggle Environments' local
file loader: **12 native games total**, sequentially. It requires all runs to
finish DONE/DONE at 720 frames, match the saved candidate and opponent rewards,
match the candidate telemetry from the outcome receipt in direct mode, report
no native policy or telemetry errors, record 719 native action calls, reject
any ERROR/INVALID/TIMEOUT state or agent stderr on either side, stay within the
runtime budget, and produce identical 719 actions for both players in direct
and file modes.

This is an operational packaging check on saved tapes. It is not fresh
reactive qualification and does not predict a Kaggle score.

## Bindings and execution

`package_manifest.json` binds this copy and verifier, the existing root backup,
the current research `main.py`, the ebf manifest/preflight/panel/receipts,
the exact six replay/tape/trace inputs, local benchmark/error/lock helpers,
and the Kaggle Environments engine and Kaggriculture sources. The expected
file-loader callable is `kaggle_a44_pet_market_gate_entrypoint` and the
engine version is `1.32.7`.

After the root confirms that fresh qualification passed and the shared game
lock is free, run only:

```powershell
python -X utf8 diagnostics/upload_pet_market_20260929_ebfbe6e9/verify_loader.py
```

The checker takes `diagnostics/.shared_game_run.lock` and a package-local lock.
It refuses pre-existing output, hash drift, a different root `main.py`, or a
missing shared lock slot. Review `loader_parity.json` and its hash afterward.
This package intentionally has no upload command or upload receipt; root must
stage and execute the one-time upload separately only after all qualification
and loader gates pass.

The checker reads candidate, parent, panel, receipt, callable and engine hashes
from `package_manifest.json`, then verifies the linked files and six exact
fixture-seat bindings. A different candidate can use this runner only with a
separately reviewed manifest and matching candidate-specific panel/receipt;
the existing EBF receipt does not qualify a derivative. No native loader games
have been run while preparing this package.
