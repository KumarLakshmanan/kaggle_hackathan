# Public complete-route native screen — 2026-09-26

The first 512 outcome-blind seed scans found only five double-Yarn openings,
so the search budget was extended to 1,024 **before any treatment game**.
The first eight qualifying seeds occurred by the 704th scanned seed;
their exact shops and order are in `seed_selection.json`. Three frozen
public 719-action schedules from the saved top-100 double-Yarn losses
then faced reacting unchanged `main.py` on all eight, both seats, with
main-vs-main controls and native original shop draws. All 64 games were
DONE/DONE.

| Recorded route | Positive paired seeds | Positive seats | Own-cash change | Rival-cash change | Paired-margin change | Gate |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| AI是我的豆包 | 3/8 | 7/16 | −4,346 | +44,210 | −48,556 | Fail |
| ShunkiKyoya | **8/8** | **16/16** | **+282,072** | **−87,869** | **+369,941** | Pass |
| mhw | 1/8 | 3/16 | −452,107 | +50,398 | −502,505 | Fail |

The ShunkiKyoya route preserved `YARN_STORE,YARN_STORE` in both seats on
all eight selected seeds; its worst paired-seed margin gain was +37,348.
This is a valid new-seed result against a reacting local opponent, though
only for double-Yarn openings and one rival policy. The source action
SHA-256 is `a72f6711bd28087a242021ec858bbbf9f43fd5f4d4eb9e03d8f872729f742aae`.
It was packaged unchanged as single-file candidate
`exp_shunki_public_route_20260927.py` (SHA-256
`39d39bfdcb40b782785b8be50e03b925c19b1510bb1610e7704ebb8bfbef8744`).
Its raw-route terminal cash and Kaggle file-loader/direct cash matched in
both seats; the loader selected the unique final callable.

The predeclared **untouched arbitrary-shop confirmation** used sequential
seeds 2629000–2629015 without shop preselection, both seats against
reacting unchanged `main.py` plus controls. All 64 games were DONE/DONE;
all 32 seat comparisons preserved the same first two shops between control
and candidate. The packaged route improved only **5/16 paired seeds** and
**10/32 seats**. Aggregate own cash fell **294,178**, rival cash rose
**381,348**, and paired margin fell **675,526**; the worst paired seed
regressed **105,092**. This fails every predeclared general-replacement
strength gate except execution.

**Decision: reject the fixed ShunkiKyoya route as a general replacement;
no `main.py` edit or Kaggle upload.** Its double-Yarn specialist effect is
promising but has no untouched double-Yarn confirmation, and a day-six
selector cannot retroactively change its different opening. Investigate
whether additional public episodes from the same opponent provide
compatible opening prefixes and complete schedules for other shops.
Do not infer that its historical public rating or the eight selected games
guarantee top-10 strength.

Evidence: `PLAN.md`, `seed_selection.json`, `reactive_screen.json`,
`candidate_parity.json`, `reactive_confirm16.json`; exact source route is
named in the frozen four-route manifest. Reproduce with:

```powershell
python -X utf8 diagnostics\public_route_native_screen_20260927\select_seeds.py
python -X utf8 diagnostics\public_route_native_screen_20260927\reactive_screen.py
python -X utf8 diagnostics\public_route_native_screen_20260927\build_candidate.py
python -X utf8 diagnostics\public_route_native_screen_20260927\verify_candidate.py
python -X utf8 diagnostics\public_route_native_screen_20260927\reactive_confirm16.py
```
