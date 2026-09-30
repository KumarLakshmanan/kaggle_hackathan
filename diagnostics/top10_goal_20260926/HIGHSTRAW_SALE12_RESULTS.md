# Day-six high-strawberry sale-timing gate — 2026-09-26

The isolated candidate `exp_highstraw_sale12_20260926.py` (SHA-256
`1f604b1bb56e9d56996b07fb268430bb1cc921a825b9d37efb7c51cb0a5b2a50`)
uses the submitted `main.py` source and its unique Kaggle entrypoint. At
step 144 it records whether the rival has at least seven strawberry tiles
and at least three more than our farm. In those games it extends the
existing own-route sale lookahead from four to twelve turns; the ordinary
physical-mirror gate already uses twelve. All farm actions, route choices,
and other market layers are unchanged. The signal is visible in the current
observation; the candidate uses no episode or opponent identity.

`build_highstraw_sale12.py` reproduces the candidate. It was screened
against all 31 losses from the September 26 saved top-100 action panel,
both seats per route, native engine 1.32.7. All 62 games ended `DONE`.
Comparison used the tested 12-turn source `mirror12_100routes.json`; the
submitted source has the same policy lines, apart from the final
Kaggle-loader callable and line-ending normalization, so the direct `agent`
used in this panel is the same policy. The comparison joins
exact action hashes, seed and seat in `highstraw_sale12_comparison.json`.

The gate was expected on 17 routes, and exactly 17 route margins changed.
It rescued **zero of 31 losses**. Aggregate paired margin fell 4,414 coins;
our own cash fell 11,554 while fixed rival cash fell 7,140. The close
Joseph Adamski deficit widened from −738 to −3,536 paired coins. DSM improved
from −34,398 to −33,952 and Roman Svet from −7,876 to −5,738, but both
remained losses. Raw candidate results: `highstraw_sale12_losses31.json`.

**Reject before reactive promotion testing.** The simple market-timing gate
does not solve the early farm portfolio disadvantage. This reused fixed-action
panel is development evidence, not a live win-rate estimate. No `main.py`
edit or Kaggle upload.
