# Resume — guarded route pool, 28 September 2026

The goal remains all 30 saved public losses and all 20 saved top teams won
in both seats. Main is 4ee. No Kaggle access or additional upload is authorized.

## Completed

- Source coverage: 208 prefixes, accepted after correcting actual shops.
- Development: 22 variants, 144 games; selected A113373693 + C113453388.
- Candidate `candidate_selected.py` and root backup
  `main_candidate_guarded_routes_20260928_2dd39764.py` have SHA-256
  `2dd397645df739ee41e73a0d91f9e749863068b18bf31319ab338c980094ba34`.
- Native affected-case parity: all 12 games exact, 04:30:31 UTC.
- Full native target panel: all 100 clean, completed 04:44:50 UTC;
  **19/20 top teams + 1/30 public losses = 20/50 sweeps**. All previous
  winning seats retained. Sessions 46566 and 74172 are terminal.
- Source 06803086's separate scan ended at 04:42:39 UTC with insufficient
  market other-guard coverage. Session 40895 is terminal. Do not advance
  that failed coverage gate or silently expand its frozen range.

## Active changed-branch qualification

Unified session **15096**, command:

```powershell
python -X utf8 diagnostics\guarded_route_pool_20260928\native.py pilot-scan --workers 4
```

At block 2928487: 4ee A/C quotas are 4/4 and 4/4; market A is 2/4, C
is 4/4. No terminal strength outcomes yet. Poll the existing session;
do not start another scan. `native.py` is hash-bound and its synthetic
gates passed. Follow NATIVE_PLAN.md and PREFIX_CONVENTION.md: only a passing
scan allows pilot-verify, then pilot. Confirmation requires a pilot pass.

This qualifies changed A/C branches only. QUALIFICATION_SCOPE.md preserves
the inherited source's missing evidence. It cannot authorize an overall
promotion by itself. Do not repeat exclusive prepare/select phases.

## Separate next experiment

`../public_loss_route_pool_20260928/` freezes a pool for all 21 remaining
public-loss branches and a new whole-policy qualification. This does not
rewrite the earlier plans. DECEM remains in the full goal and regression
panel; its first-144-compatible pool is exhausted without a win.

### Superseding checkpoint at 05:08 UTC

Scan 15096 completed/pass at 05:02:03 UTC (784 prefix games). All quotas
filled. Original-engine `pilot-verify --workers 2` is active in session
**19905**, 32 selected prefix games. Do not repeat the completed scan.
The broad remaining-loss control stage is session **73859**; see its state.

### Superseding checkpoint: native pilot

Prefix verification session 19905 is terminal/pass (32/32 exact).
Native terminal pilot is active as session **63515** with two workers:
`python -X utf8 diagnostics\guarded_route_pool_20260928\native.py pilot --workers 2`.
Do not repeat earlier phases; inspect native_pilot.json before confirmation.

## Terminal qualification result — 05:39 UTC

Session **63515** is terminal: 96/96 native games, all clean, passed=false.
All three arms score 24/32 win points. Exact 2dd failed strict improvement;
reject promotion and do not run confirmation. Earlier scan/verification/
full-panel sessions are also terminal. See RESULTS.md and native_pilot.json.

Only the distinct broader public-loss pool continues in session **23766**.
Its new whole-policy gates were frozen before this result. Main remains
4ee and Kaggle remains untouched. The first-BRUNCH 91-route experiment is
also terminal/rejected: no DECEM wins in 182 games.
