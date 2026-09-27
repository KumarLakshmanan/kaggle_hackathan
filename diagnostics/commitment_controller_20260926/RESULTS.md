# Day-11 sheep commitment controller — rejected, 2026-09-26

## Provenance and intervention

The unchanged local incumbent and submitted Kaggle source is `main.py`
SHA-256 `489fe8e4e80b03e7e6485b5969f3bec1861fa8389473f361969f064e484f6c7b`.
The isolated wrapper `exp_sheep_commitment_20260926.py` loaded those exact
bytes and called the incumbent once per observation. It intercepted only the
existing six-sheep eligibility predicate. At the first funded day-11
one-Yarn opportunity, A retained the incumbent, B compared a time-indexed
land/animal/feed/worker/market forecast with the incumbent and could enable
the inherited complete sheep executor, and C always enabled that executor.
No seed, opponent identity, private rival stock or future shop was a policy
input. See the [predeclared plan](PLAN.md) for trigger, cases, and gates.

The OFF wrapper matched direct `main.py` exactly on seeds 2612000 and
2612001 in both seats: four `DONE` games and zero cash/action outcome
difference. `off_parity_2seeds.json` is the record. The installed simulator
is `kaggle-environments==1.32.7`, standard 720-step native configuration.

The initial `601062e5...` wrapper revision had a forecast parser defect:
an empty recorded market-order placeholder made `_native_hires` attempt to
sum a list. The exception fallback retained the incumbent, so its 16-seed
zero-change run was **not a treatment test** (`model_dev16.json`,
`force_dev16.json`). I corrected the parser to count a hire only when the
order is nonempty, froze the resulting source, verified an activated pilot,
and repeated the exact predeclared block. No threshold or case was changed.

## Native reactive development result

Development seeds 2612000–2612015 were played in both seats against the
trusted reacting `main.py`. Shops and shared market evolved naturally. The
seed, not the seat, is the independent shop draw. All 96 A/B/C games ended
`DONE`. `abc_fixed_dev16_comparison.json` joins A/B/C by full seed and seat;
the exact source, opponent, simulator, and configuration are recorded here
and in the raw runner outputs.

| Arm | Positive paired margins / 16 | Seat wins / 32 | Own cash | Rival cash | Total paired margin | Worst paired delta | Errors |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| A incumbent | 0, 16 ties | 0, 32 ties | 2,978,818 | 2,978,818 | 0 | 0 | 0 |
| B controller | 0, 3 losses / 13 ties | 0, 6 losses / 26 ties | 2,844,934 | 2,905,620 | −60,686 | −23,750 | 0 |
| C always expand | 0, 3 losses / 13 ties | 0, 6 losses / 26 ties | 2,844,934 | 2,905,620 | −60,686 | −23,750 | 0 |

B and C activated on the same three seeds and produced identical terminal
cash. Relative to A, `Δown = −133,884`, `Δrival = −73,198`, and therefore
`Δmargin = −60,686` across the 32 seats. The model predicted minimum gains
of +14,927, +9,788, and +15,041 coins at those three decisions, respectively;
actual paired margins were −19,700, −23,750, and −17,236. There were zero
loss-to-win rescues and zero winning-control reversals because A self-play
was a draw in all cases. The worst seat loss was −12,267. This tests
competitive margin against the reacting incumbent, not leaderboard win rate.

The market-price submodel reproduced installed engine wool prices at six
inventory points around equilibrium. A separate engine transition check
showed WOOL and FERTILIZER sales commute when independent, while selling
before a seed buy can fund that buy; see `market_transition_check.py`.
Neither check validates the long-horizon forecast. The known 1-second action
budget remains relevant: the same-process timed-agent maximum in the final
development runs was 583 ms for B and 565 ms for C, while the failed initial
parallel runs reported >1 second under contention. These timings exclude
Kaggle file-loader/startup serialization and cannot qualify a deployable
artifact. The candidate is rejected on strength before deployment timing.

## Decision and limitations

**Reject this mechanism.** The complete sheep executor was feasible enough
to confirm the project, but the observation-only forecast failed to predict
its competitive continuation in every activated development seed. No
threshold tuning, full saved-action panel, untouched block, or additional
Kaggle upload follows from this failed gate. `main.py` remains unchanged.
The exact transaction and matched-shop diagnosis for one activated seed is
`ledger_2612002_s0.json`, generated from three full event traces. With native
shops, B changed the unlocks after day 15; final cash moved from
116,139/116,139 to 81,220/91,070 (own/rival). The own-cash delta of
−34,919 consists of lower wool receipts (−27,375), higher sheep/land/wage
costs (−11,092), higher wheat costs (+4,719), and smaller offsets in other
items. The exact ledger reconciles every coin; terminal `other_cash_delta` is
zero. Rival cash also fell 25,069, so paired margin fell 9,850.

Forcing B to face A's *same future shop sequence*, while keeping the rival
reactive and the market endogenous, produced 114,368/105,709: own cash
−1,771, rival cash −10,430, and paired margin **+8,659** relative to A.
The extra sheep monetized 132 more wool units and 55 more fertilizer units;
own wool receipts increased 12,212, but buying three sheep, extra land,
wages and wheat consumed most of that. The competitive gain came from a
larger rival-cash reduction, including 11,530 fewer rival wool receipts.
This matched-shop intervention is a causal diagnostic on one seed, not a
deployable policy result or independent validation. Native unlock changes
are a real consequence in this simulator and dominate this example.

The result does not prove that every
counterfactual controller fails: the current model omits important native
route opportunity costs and cannot know future shops. The next distinct
mechanism must choose a **whole route** at the earlier day-6 commitment,
since the one-Yarn incumbent route already schedules its own sheep and land.

Reproduction:

```powershell
python -B -X utf8 paired_benchmark.py --candidate exp_sheep_commitment_20260926.py --opponent main.py --seeds 2612000 2612001 2612002 2612003 2612004 2612005 2612006 2612007 2612008 2612009 2612010 2612011 2612012 2612013 2612014 2612015 --candidate-override _BUNDLE_MODE=model --capture-step 265 --json-out diagnostics/commitment_controller_20260926/model_fixed_dev16.json
python -B -X utf8 paired_benchmark.py --candidate exp_sheep_commitment_20260926.py --opponent main.py --seeds 2612000 2612001 2612002 2612003 2612004 2612005 2612006 2612007 2612008 2612009 2612010 2612011 2612012 2612013 2612014 2612015 --candidate-override _BUNDLE_MODE=force --capture-step 265 --json-out diagnostics/commitment_controller_20260926/force_fixed_dev16.json
python -B -X utf8 diagnostics/commitment_controller_20260926/analyze_dev.py
```
