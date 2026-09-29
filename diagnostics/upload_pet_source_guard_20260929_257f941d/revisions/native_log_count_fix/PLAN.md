# Pet source-guard loader package

## Scope and status

This is an isolated operational package for guarded candidate
`257f941d06fcd6dd9185ca58bc98d1af83dc4c3fafc24e275a1bf057b61bad55`.
`main.py` and the requested root backup are exact copies of
`diagnostics/pet_source_guard_20260929/candidate.py`. The loader checker has no
upload logic and does not edit root `main.py` or any prior diagnostic package.
Root separately staged `upload_once.py`; it is excluded from this loader
manifest, is never called here, and requires its own review and upload receipt.

The 102-game fixed-tape preservation check is a prerequisite to producing the
package manifest. `build_manifest.py` refuses a missing, incomplete, failed,
wrong-candidate, or wrong-manifest `preservation_receipt.json`. It takes the
six selected fixture-seat rows' expected rewards and full telemetry from that
receipt, while taking unchanged seed/replay/tape/trace inputs from the frozen
EBF panel. It never substitutes the older EBF outcome receipt as the guarded
candidate's expected result.

The six seats are both seats of `live-114260122`, both seats of
`live-114274897`, and both seats of inactive control
`top20-20-Densike-114270616`. After the passing preservation receipt is
available, the operational checker is planned to run each fixed opponent tape
through both direct import and Kaggle Environments' local file loader:
12 native games total, sequentially.

## Frozen checks

The builder and checker bind the guarded candidate, requested root backup,
research `main.py`, preservation runner/manifest/receipt/outcomes, original EBF
panel, fixture replay/tapes/traces, benchmark and lock helpers, Kaggle
Environments engine and Kaggriculture sources, and the local Python runtime.
The checker verifies the exact final callable, source/preservation bindings,
source-branch telemetry (`a44_pet_market_gate_branch72` equals the actual
`bridge_selected` value), the guarded Pet predicate and route/call counters,
receipt rewards and complete telemetry, DONE/DONE with 720 frames and 719
action calls, no ERROR/INVALID/TIMEOUT statuses or stderr, nonnegative remaining
budgets, direct/file reward parity, and equality of all 719 two-player actions.

The Pet predicate is checked from its recorded public fields:
`branch == "source"`, key `PET_CAFE|M8+|C>S|G0`, 12 rival melons, and public
WHEAT 9975. The computed predicate must equal `a44_pet_market_gate_active72`;
active rows must report route `113517834` and 647 calls, while inactive rows
must report a blank Pet route and zero calls. The target and pasture rows also
retain their preservation-receipt telemetry, including the Brunch route where
present. The inactive top20 control must remain inactive.

## Separate evidence meanings

The preservation receipt answers whether the derivative preserved its
predeclared 102 fixed-tape outcomes and instrumentation checks. The later
loader receipt answers whether the package's direct and file-loaded execution
matches the guarded candidate's preservation rows. Neither result establishes
reactive research promotion or a Kaggle rating improvement. Research promotion
remains false in this package; root owns the separate reactive decision and any
future upload decision. The parent EBF reactive screen is bound separately in
the manifest: its receipt is complete but `passed: false` and `promotion:
false`; the guarded derivative has no separate reactive qualification. The
preservation and loader checks do not change that research status.

## Commands after the preservation receipt passes

Build the package manifest and static freeze receipt without running games:

```powershell
python -X utf8 diagnostics/upload_pet_source_guard_20260929_257f941d/build_manifest.py
python -X utf8 diagnostics/upload_pet_source_guard_20260929_257f941d/verify_loader.py --static
```

Only after root reviews that freeze and separately releases the loader slot,
the 12-game operational check is explicitly requested with:

```powershell
python -X utf8 diagnostics/upload_pet_source_guard_20260929_257f941d/verify_loader.py --run
```

The operational command takes both `diagnostics/.shared_game_run.lock` and a
package-local lock, refuses existing output or hash drift, and never contacts
Kaggle. The loader command contains no upload action. Root owns any later
upload decision and the separately staged one-shot uploader.
