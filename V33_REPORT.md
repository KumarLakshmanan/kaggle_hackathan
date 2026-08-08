# V33 observable counter portfolio

## Outcome

V33 replaces the old `main.py` and is mirrored byte-for-byte in `submission.py`.
It keeps the readable 719-turn action-book architecture, legality checks, weed
recovery, bounded market preemption, and final liquidation from V32, then adds
public-state routing for the newly observed failed replays.

## New routing

- Opponent money from 150 through 175 after turn zero selects the alternate
  industrial opening. This covers the OlivierS and jatan openings.
- The public shop pairs `YARN_STORE/BRUNCH_SPOT`,
  `YARN_STORE/FARMERS_MARKET`, and `BRUNCH_SPOT/ICE_CREAM_SHOP` select the
  THUNDER counter book.
- `SMOOTHIE_SHOP/ICE_CREAM_SHOP` selects the Aastik counter book.

The selector uses only observations available to the agent. It does not use
episode IDs, hidden seeds, team names, encoded payloads, or dynamic evaluation.

## Reproducible gates

- Failed-replay panel: `12/12` games won, `6/6` unique routes won, both seats,
  all agents `DONE`. Smallest paired route margin: `+3,978`.
- Best-replay panel: `102/104` games won, `51/52` unique routes won, both seats,
  all agents `DONE`. Smallest winning game margin: `+39`.
- The one unresolved route is `episode-90635995-seat0` (Seb), at `-2,410` per
  seat in the strict route proxy.

Full machine-readable results are in:

- `benchmark_results/v33_final_failed_gate.json`
- `benchmark_results/v33_final_best_all_gate.json`

## Seb limitation

The Seb tape requires a seven-hire turn-zero opening to beat directly. Every
compatible five-hire book in the local corpus loses that proxy. The tested
seven-hire counter beats Seb, but regresses to only `38/52` best routes and
loses 14 of them. Because the turn-zero observation is identical, a
deterministic policy cannot wait for later shop observations before choosing
between those incompatible openings. V33 therefore keeps the five-hire minimax
opening that wins 51 best routes and every current failed route.

These replay proxies are regression evidence, not a guarantee of leaderboard
placement against unseen agents or engine changes.
