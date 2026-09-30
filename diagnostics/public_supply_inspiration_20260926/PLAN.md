# Published-code inspiration: coherent wheat reserve — 2026-09-26

Public sources reviewed statically: Evelyn3976's Apache-2.0
`Kaggriculture Adaptive Market Scheduler v1` keeps worker feed tasks tied to
physical wheat carriers and shed pickups; Ahmed Berat Özer's Apache-2.0
`Kaggriculture V43: Recovering Lost Harvests` uses an exact post-action shed
model and guards market requests against physical stock. The current
`main.py` already implements related seed-funding, overflow, and terminal
repairs. This experiment applies only the coherent feed-reserve principle
to our separate search agent. No public source is executed or copied into
the candidate.

Mechanism B differs from the retained search v2 in one decision: it uses
the same `2*animal_count+3` wheat target for both SELL protection and the
later BUY_PRODUCT top-up. The original sells down to `animal_count` and
then buys toward the larger target, sometimes alternating wheat sells and
buys. Worker routing, portfolio search, all other market orders, and
`main.py` are unchanged.

Predeclared development seeds: 2615000–2615003, both seats, default
endogenous shops, reacting `main.py`. Run A (original search v2) and B
against `main.py` on each seed. Promotion within the research branch
requires all `DONE`, fewer wheat buy/sell cycles, higher aggregate paired
margin than A, and at least two positive seed-level B-minus-A margins.
If this passes, confirm on untouched native seeds 2615004–2615007 in both
seats, requiring positive aggregate paired-margin change and no new
time-limit failures. The independent search agent still must beat `main.py`
on a separate fresh panel before any `main.py` promotion. This experiment
authorizes no Kaggle upload.
