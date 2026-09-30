# Fresh reactive mirror24 retention check — frozen 2026-09-26 17:24 UTC

The latest Kaggle submission 56572390 (current `main.py`, SHA-256
`489fe8e4...`) displays 2165.0, below the previous working submission
56569042 (snapshot `main_before_mirror_straw24_20260926_08aa268a.py`,
SHA-256 `08aa268a...`) at 2221.0. Those live scores use different opponent
samples, so the difference is not a controlled policy comparison. Earlier
native 16-seed blocks favored mirror24, but a fresh check is warranted.

Freeze native engine seeds **2612600–2612623**, both seats, with the current
main as candidate and the exact previous source as reacting opponent. Use
the engine's native shop draws, no forced route/shop, and require every game
`DONE`. Summarize each seed as one paired result, plus own/rival cash and
candidate call time. A positive paired-seed majority and positive total
margin would support retaining mirror24 locally; a negative majority or
negative total margin would trigger a larger audit before a rollback decision.
This self-play A/B cannot establish a top-10 rating or generalize to every
opponent. The current file remains unchanged throughout the check. No Kaggle
upload is authorized.
