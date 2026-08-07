# V25 failed-replay regression report

## Architecture

- Primary worker plan: the stable A-family production route.
- Primary market plan: the Parv replay schedule, which improved the two newest
  market-heavy matchups while retaining the Mochogo win.
- Alternate plan: the cleaned MD industrial route, selected only when the
  opponent's public turn-one cash falls in the tested `$18..$32` fingerprint.
- Counter ordering: contested same-turn sells follow the public Parv threat
  ordering, but this layer is disabled for the independently tested alternate.
- Safety: public-state market validation, weed repair, bounded preemption,
  terminal liquidation, and exception recovery remain enabled.

The generated submission remains plain, readable Python. Strategy tables are
not compressed, encoded, encrypted, or dynamically evaluated.

## Exact failed replay seeds

Each replay was tested twice with seats swapped on Kaggle Environments 1.32.5.

| Episode | Opponent | Seat 0 margin | Seat 1 margin | Paired margin |
|---:|---|---:|---:|---:|
| 90638959 | mochogo | +139 | +139 | +278 |
| 90648579 | MD Concepcion | +787 | +787 | +1,574 |
| 90649380 | Arun Mallikarjuna | +1,444 | +1,444 | +2,888 |
| 90653307 | parv goyal2 | +1,310 | -858 | +452 |
| 90653343 | Cam-Luan Truong | -843 | +1,043 | +200 |
| 90655731 | Boiled-Sweet-Potato | +436 | +436 | +872 |

Result: 6/6 paired matchups won, 10/12 individual games won, and every agent
finished with `DONE` status. Parv and Cam remain seat-sensitive; their paired
scores are positive, but this is not a claim that every possible future game
or seed is guaranteed to win.

## Historical promotion gate

The existing 23-route panel was rerun at seed 314159 with both seats swapped:

- Opponent routes: 23/23 won.
- Individual games: 46/46 won.
- Mean margin: +8,485.48.
- Median margin: +7,242.
- Mean agent decision time: 565.81 microseconds.
- Maximum observed decision time: 176.52 milliseconds.
- Status: all games `DONE`.

Machine-readable evidence:

- `benchmark_results/v25_failed_routes_exact_seeds.json`
- `benchmark_results/v25_portfolio_current23_panel.json`

