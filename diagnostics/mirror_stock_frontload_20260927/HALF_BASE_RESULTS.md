# Half-base stock sale — development pass, reactive gate fail, 2026-09-26

The isolated `exp_mirror_stock_frontload_halfbase_20260927.py` (SHA-256
`e9517daebe5523879c5096839570af04619135fc7f5a7fb7e6446ab1c367ca68`)
differs from the rejected latched candidate only by requiring the visible
strawberry quote to be at least 60, half the native engine's 120-coin base.
The two-seat native mechanism smoke retained the documented 20-unit sale,
changing the fixed-rival episode 113642505 margin from −900 to +231.

On the frozen 29 current live losses plus ten close wins, original seeds in
both seats with endogenous shops and fixed rival actions, all 78 candidate
games ended `DONE`/`DONE`, zero wrapper errors, maximum measured call 152 ms.
The exact incumbent baseline reproduced all 39 original-seat Kaggle cash
pairs. In original seats, this variant rescued **five losses**, reversed
**zero** wins, raised own cash **1,874**, lowered fixed-rival cash **3,885**
and improved paired margin **5,759**. It passed the predeclared saved-route
development gate. Raw results: `halfbase_dev_candidate39.json` and
`halfbase_dev_comparison.json`.

The predeclared fresh reactive check used native seeds 2614300–2614315,
both seats, versus reacting current `main.py`. All 32 games ended `DONE`
with zero candidate errors and a 167 ms maximum call. It fired in only
**four games** (two seeds): one paired seed was positive (+604), one was
negative (−58), and 14 paired seeds tied. Aggregate margin was **+546**.
Most same-policy games stayed physically aligned and never exposed the
post-divergence rule. This fails the predeclared **positive paired-seed
majority** gate. Raw result: `reactive_halfbase.json`.

**Decision: reject promotion under the frozen gate.** The reactive check
has too little exposure to support a general claim. Fixed public action
tapes cannot substitute for independent adaptive opponents. No top-100
promotion screen, `main.py` edit, or Kaggle upload occurred. A separate
matched test against a genuinely diverging reacting near clone would be a
new diagnostic experiment, not a retroactive pass of this gate.
