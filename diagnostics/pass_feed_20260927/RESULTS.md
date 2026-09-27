# Carried-wheat `PASS` feed candidate — 2026-09-26 19:44 UTC

Separate candidate `exp_pass_feed_20260927.py` SHA-256 `067f28545b20a20178a615715fb6313759a876f2468b367afc72db438335d3f1`
was built byte-for-byte from current `main.py` SHA-256 `489fe8e4...` plus
one wrapper. It fed an unfed cow/sheep only when the parent would `PASS`,
on days 12–28, with at least two wheat carried by that worker. All other
actions and market orders came from the incumbent. Its source and exact
builder are preserved. `main.py` and its uploaded backup were unchanged.

The predeclared smoke used the two consumed diagnostic losses, their original
seeds, both seats and native shops. All four games ended `DONE`/`DONE`.
Telemetry recorded 198 triggers and zero wrapper errors. The raw rows and
timings are in `smoke_two_losses.json`.

| Route / seat | Own cash change | Rival cash change | Paired-margin change |
| --- | ---: | ---: | ---: |
| Boey / 0 | −2,228 | −720 | −1,508 |
| Boey / 1 | −2,228 | −720 | −1,508 |
| mhw / 0 | −1,442 | −548 | −894 |
| mhw / 1 | −1,277 | +114 | −1,391 |
| **Total** | **−7,175** | **−1,874** | **−5,301** |

Feeding every visible idle animal spends carried wheat and interacts with
later feed/production and the shared market. These terminal results do not
isolate which downstream mechanism caused the loss, but they decisively fail
the predeclared positive aggregate own-cash smoke gate.

**Decision: reject this candidate now.** Do not run the conditional 34-loss
plus control panel or fresh reactive screens, promote to `main.py`, or upload
to Kaggle. Fixed-rival smoke is only a development filter, not independent
proof that a more selective feed rule could never help.
