# Ghost wheat derivative: corrected 12-game outcome run

Status: new frozen runner package; no outcome games have run from this directory. The earlier `outcome_run_20260929` attempt is preserved separately and excluded because its telemetry gate read the panel row instead of the actual candidate result. This V2 checker receives both the actual game result and the frozen panel row; its static preflight includes positive and negative synthetic checks of that data path.

This remains fixed-tape diagnostic evidence only. Candidate SHA-256 is `228ca9da123ef388b5430d4451020820d7e3854a8dc7ec5fd7ae54e9da1d2767`, derived from the exact 6d parent `6d3d1c0df1b06566417d8ba204e05e0caad9a115bb84b73513bef68575a70bf9`. The experiment is unchanged: at source bridge step 72, `ICE_CREAM_SHOP|M8+|C>S|G0` with public WHEAT inventory <= 9975 selects route `113360743`; exactly both seats of `live-114288168` should activate.

Run all six frozen fixtures in order, both seats. Require 12 clean 720-frame games with both agents DONE and no candidate errors; the two Ghost seats must both win; all ten non-trigger controls must exactly match the 6d result, candidate reward, opponent reward, and margin. Verify telemetry from each actual game result against the frozen public step-72 state, including branch, key, WHEAT inventory, trigger, selected route, Goose4 calls and errors, and bridge errors.

The partial `candidate.jsonl` under the prior outcome directory is retained as a harness-failure record, not a result. This V2 directory has new output paths, performs no resume, and will write a complete receipt only after all 12 rows finish. Shared lock: `diagnostics/.shared_game_run.lock`.

Command, only after root reviews the static freeze and confirms the shared lock is clear:

```powershell
python -X utf8 diagnostics/a44_goose4_smoothie_ghost_wheat_gate_20260929/outcome_run_v2_20260929/run.py
```
