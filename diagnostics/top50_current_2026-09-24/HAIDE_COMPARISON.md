# Independent public-agent architecture screen

The previously extracted, self-contained `kaggle_extracted_agents_2026-09-21/haideptry_master_2965.py` was run against the **same** 100 fresh top-50 fixed-action routes, both candidate seats, under `kaggle-environments` 1.32.7. Outputs: `haide_25routes_screen.json`, `haide_100routes.json`; control: `main_100routes.json`.

| Agent | Route wins / 100 | Seat wins / 200 | Mean seat margin | Completed games |
| --- | ---: | ---: | ---: | ---: |
| Current `main.py` | 67 | 133 | +22,160.29 | 200 |
| Public Haide master | 67 | 134 | +21,794.16 | 200 |

The 25-route screen suggested 18 Haide wins versus 17 for main, but the full panel gave **three loss-to-win conversions and three win-to-loss reversals**, for no net route-win improvement. The large URAD route flip (paired margin −20,026 → +57,158) was **not** caused by higher candidate cash: candidate cash fell by 13,410 across seats while fixed-tape opponent cash fell by 90,594. Conversely, one prior main win against arutyunoff (+181,644) became a Haide loss (−49,880), driven by both lower candidate cash (−36,162) and much higher fixed-tape opponent cash (+195,362). These are static-replay market interactions, not proof that either agent would dominate an adapting opponent.

Decision: do not substitute the independent agent or merge it into `main.py`. Its gross rescue/reversal table and own-versus-opponent cash decomposition show why a small screening sample and net win count alone are insufficient.

A separate **reactive** check ran current main directly against this older public Haide code on eight predeclared fresh seeds (`300001`–`300008`), both seats. Main won 16/16 and all runs completed (`main_vs_haide_reactive_8seeds.json`). This is a useful compatibility/regression control, but its saturated win rate cannot validate a proposed improvement against today's private top-50 policies.
