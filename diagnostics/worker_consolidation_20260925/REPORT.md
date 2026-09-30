# Bounded offline worker-consolidation feasibility — 2026-09-25

**Decision: no task-preserving treatment established; no policy change or submission.**
The experiment is offline-only and uses frozen traces as schedule evidence. It does not propose a route/replay-aware agent rule.

The local insertion neighborhood requires each donor bundle to be inserted as a contiguous shortest-path route into a surviving unit's slots that had no non-position economic effect, then return that unit to its trace position by the donor bundle's delivery deadline. The two bundles must fit on distinct surviving units. The pair search is capped at the recorded limit. This is a bounded feasibility screen, not a proof against all possible rescheduling.

| Case | Frozen baseline own / rival | Baseline replay exact | Eligible crop insertions | Eligible fertilizer insertions | Pairings | Exact task treatments |
| --- | ---: | --- | ---: | ---: | ---: | ---: |
| `neartie_marwar22_trace_20260925.json.gz` | 57,331 / 57,415 (-84) | True | 0 | 0 | 0 | 0 |
| `demand_gleb_control_trace_20260925.json.gz` | 77,957 / 77,114 (+843) | True | 0 | 0 | 0 | 0 |

The target trace identifies the final 89-coin hire on step 697. Its trailing hand completes the following observed bundles:

- `water_harvest_deliver`: CARROT ×2; task at `[9, 4]`, delivery at step 711 / `[5, 4]`.
- `collect_fertilizer_deliver`: FERTILIZER ×1; task at `[7, 4]`, delivery at step 717 / `[5, 4]`.

Exact replay details

### `neartie_marwar22_trace_20260925.json.gz`

Baseline tape replay: own 57,331, rival 57,415, margin -84; status `['DONE', 'DONE']`; 720 frames. Exact-match to frozen rewards/status: `True`.

- `invalid_remove_only_comparator_not_a_treatment`: own 57,369, rival 57,419, margin -50; own cash delta +38 (not the nominal +89 hire saving), rival cash delta +4; valid treatment `False`; tile state differs, sales exact `False`, rival cash equal `False`. Candidate-call max 774.215 ms, episode frames 720.

### `demand_gleb_control_trace_20260925.json.gz`

Baseline tape replay: own 77,957, rival 77,114, margin +843; status `['DONE', 'DONE']`; 720 frames. Exact-match to frozen rewards/status: `True`.

- `invalid_remove_only_comparator_not_a_treatment`: own 77,953, rival 77,123, margin +830; own cash delta -4, rival cash delta +9; valid treatment `False`; tile state differs, sales exact `False`, rival cash equal `False`. Candidate-call max 767.843 ms, episode frames 720.

Search elapsed 105.290 s across both cases (includes exact replays).
The per-call maximum includes the oracle tape's one-time gzip load and is not an online-policy latency estimate.
The remove-only comparator, when present, is explicitly invalid: it is not a consolidation treatment and cannot establish feasibility. A successful treatment would additionally require both donor bundles to be executed, exact same-day sell commits, equivalent own physical state (excluding the intentionally removed worker), rival cash unchanged, and +89 own cash from the omitted hire. No such treatment is claimed unless a trial is marked valid.

Run command:

```powershell
python diagnostics\worker_consolidation_20260925\experiment.py
```

The existing parent 24-route audit was not read, edited, or run by this experiment.
