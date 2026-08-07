# V26 Dhana integration report

## Direct comparison

`main.py` V25 was tested against `dhana/main.py` on eight seeds with seats
swapped for every seed:

- 16/16 games won by V25.
- Mean margin: +10,413.06.
- Both agents finished every game with `DONE` status.

This established that Dhana's fixed action route should not replace the V25
portfolio.

## Logic retained from Dhana

Two strategy-independent ideas were rewritten as plain, readable Python:

1. Actor-local weed recovery now replays up to eight route turns after a
   blocked BUILD or PLANT transaction, instead of two.
2. Final liquidation scores each product using current price, held quantity,
   product glut sensitivity, and the opponent's visible crop/animal exposure.
   Products most likely to suffer an opponent dump are sold first.

The second change fixes the two seat-sensitive exact replay losses present in
V25. No Dhana action table or encoded payload was copied.

## Logic rejected

- Dhana's fixed production route lost all 16 direct games.
- Its 30-route prototype memory expands to approximately 3.69 MB of JSON and
  is stored in compressed/encoded form. It was not copied because the current
  lightweight portfolio already won the direct matchup and the project requires
  an unencrypted, inspectable submission.
- Turn-700 forced liquidation was not copied; V26 retains final-turn
  liquidation to avoid abandoning profitable late production prematurely.
- Broad exception-to-PASS behavior was not copied; the existing legal-action
  recovery path remains in place.

## Verification

### V26 versus Dhana

- Seeds: 42, 314159, 2109971721, 595288444, 201223054, 785864056,
  1716462233, and 1002553721.
- Results: 16 wins, 0 draws, 0 losses.
- Mean margin: +10,591.19.

### Exact failed replay seeds

| Episode | Seat 0 margin | Seat 1 margin | Paired margin |
|---:|---:|---:|---:|
| 90638959 | +139 | +139 | +278 |
| 90648579 | +489 | +489 | +978 |
| 90649380 | +1,444 | +1,444 | +2,888 |
| 90653307 | +1,310 | +229 | +1,539 |
| 90653343 | +103 | +1,043 | +1,146 |
| 90655731 | +436 | +436 | +872 |

Result: 12/12 individual games and 6/6 paired matchups won.

### Historical promotion panel

- Opponent routes: 23/23 won.
- Individual games: 46/46 won.
- All games completed with `DONE` status.

Machine-readable evidence:

- `benchmark_results/v26_vs_dhana_8seeds.json`
- `benchmark_results/v26_failed_routes_exact_seeds.json`
- `benchmark_results/v26_current23_panel.json`

