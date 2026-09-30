# Unused coop goose pilots — 2026-09-26

The submitted `main.py` (SHA-256 `08aa268a...`) builds an unused coop on the
saved DSM / Brunch Spot route. Three isolated candidates tested whether adding
one goose there improves the result. Each result below is a native
`kaggle-environments` 1.32.7 game on seed 1681313608, candidate seat 0,
against the same saved DSM action route. Both players ended `DONE`. This is a
development-route pilot, not independent validation of a reacting policy.

| Policy | Our cash | Rival cash | Margin | Change from baseline |
| --- | ---: | ---: | ---: | ---: |
| Current `main.py` | 114,699 | 131,898 | -17,199 | — |
| Buy one goose, keep the original labor plan | 114,399 | 131,888 | -17,489 | -290 |
| Buy a goose and hire a dedicated hand daily | 112,737 | 132,339 | -19,602 | -2,403 |
| Assign the least-burden existing hand | 98,484 | 150,195 | -51,711 | -34,512 |

The first candidate bought the goose but never placed it; it stayed in the
shed. The dedicated-hand candidate placed and serviced it, but incremental egg
sales of 1,729 coins did not cover the added work and feed. Requested HIRE
spend rose from 5,083 to 7,654 coins and requested wheat purchases from 5,433
to 6,884, plus the 300-coin goose. Reusing a planned hand displaced farm work:
by day 12, 11 tiles were weeds and only 20 strawberry tiles remained, versus
33 strawberries in the baseline trace. The large loss is consistent with a
tightly scheduled route whose existing hands have little spare capacity.

The three candidate source hashes are `89062956...`, `60bd818c...`, and
`546718d4...` respectively. Reproduction builders are
`build_empty_coop_goose_probe.py`, `build_empty_coop_goose_worker.py`, and
`build_empty_coop_idle_worker.py`. Raw native traces are the corresponding
`empty_coop_goose_DSM_s0_trace.json.gz`,
`empty_coop_worker_DSM_s0_trace.json.gz`, and
`empty_coop_idle_DSM_s0_trace.json.gz`; baseline paired result is
`route_probe_control_dsm.json`.

**Decision: reject all three pilots.** No `main.py` edit or Kaggle upload.
Other seats, original-shop variations, and reactive opponents were not run
because the first screen failed.
