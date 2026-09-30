# Late mirror first-sale advance — rejected, 2026-09-26

The isolated `exp_late_first_sale_mirror_20260926.py` (SHA-256
`cf016e23898e17e89660801d1ec57c3e47b3acfff40720e06ed77fd8cc2f934f`)
was built from current submitted `main.py` SHA-256 `489fe8e4...` under the
frozen [plan](PLAN.md). It removed first-future-sale protection only from
step 480 onward and only while the publicly visible farms physically
matched. The current stock, buy, and market-order guards remained active.

The baseline was the existing exact current-source replay screen on all 29
live losses and ten closest wins, original seeds and both seats. It
reproduced all 39 original-seat Kaggle cash pairs. The candidate completed
78/78 games `DONE`/`DONE`, with zero reported errors and a 152 ms maximum
measured call. In the **39 original seats**, it rescued **one** loss
(𝕯𝖊𝖔𝖉𝖎𝖒𝖘 & 𝕮𝖔, −374→+64), reversed no control win, raised own cash 983,
lowered fixed-rival cash 406, and improved paired margin 1,389. Twenty-seven
original-seat margins changed. Across both seats, panel wins rose 22→24/78
and paired-route wins 12→13/39.

**Decision: reject at the predeclared development gate:** one rescue is below
the required five. The small fixed-action gain is descriptive and does not
establish strength against adapting opponents. No fresh reactive or top-100
promotion screen was run, and `main.py`/Kaggle remain unchanged. Raw
candidate games and original-seat deltas are in
`late_first_sale_dev_candidate39.json` and
`late_first_sale_dev_comparison.json`.
