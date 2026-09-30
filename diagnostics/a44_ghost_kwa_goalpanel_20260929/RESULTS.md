# Full Ghost + Kwa saved-corpus goal run

Date: 2026-09-29. Candidate SHA-256:
`7b354498ef2f7213e24ecb332d92d291d9515b94b2a7a845058e829572c0fca2`.
The candidate is the frozen Ghost + Kwa composition built on exact 6d parent
`6d3d1c0df1b06566417d8ba204e05e0caad9a115bb84b73513bef68575a70bf9`.

## Coverage and result

The earlier hash-bound run tested the candidate against all 20 saved top-team
fixtures and recorded **19/20 both-seat sweeps (95%)**. This follow-up ran both
seats for every fixture in the full frozen 30-loss set. The two panels are
disjoint, so together they cover all 50 target fixtures.

The 60 loss games completed cleanly at DONE/DONE/720. All telemetry passed,
all four route-target seats won, and all 56 inactive controls exactly matched
the 6d baseline. The candidate earned **24/30 both-seat loss sweeps (80%)**,
up from **22/30** for the exact 6d baseline. It missed the required 27/30
loss goal by three sweeps. The top-20 goal remained satisfied at 19/20.

The two new sweeps came from the route interventions:

| Fixture | 6d result and margin | Composite result and margin |
|---|---|---|
| Kwa `live-114227779` | loss, -3,858 in both seats | win, +4,118 in both seats |
| Ghost Rule `live-114288168` | seat 0 loss -2,253; seat 1 win +1,425 | win, +1,298 in both seats |

Six fixtures remain losses in both seats under the composite:

| Fixture | Opponent | Margin in both seats |
|---|---|---:|
| `live-114218866` | pensukesan | -53,956 |
| `live-114223292` | 吃白饭的大肥鱼 | -33,224 |
| `live-114238112` | Civitasmass | -8,178 |
| `live-114260122` | Ghost Rule | -32,028 |
| `live-114270587` | Roman Svet | -18,815 |
| `live-114274897` | THIRD FARM CLUB | -17,760 / -17,099 |

The goal needs at least three additional both-seat rescues. The best isolated
lead is Civitasmass `live-114238112`: a source-branch step-72 Pizza/Ice Cream
pair selector has a frozen target/control plan at
`diagnostics/a44_pizza_icecream_pair_20260929/PLAN.md`. Route `113339524` won
both seats in an older screen, but that screen used a different turn-79 wheat
quantity; treat it only as a hypothesis and rerun the plan’s fresh eight-game
target/control gate before counting it.

## Evidence and decision

Loss panel SHA-256:
`dd11014aa8b9423a43a5f8fd6bf1af592881b940845d032c406a8d86cc1e6ea7`.
Frozen manifest SHA-256:
`ecf9c0545bf8b1e3dd4f655f8b2ed68e8f2c1d852e22e5d9ca422a2b94dd9426`.
Outcome receipt SHA-256:
`867c09b7688b63fda0c33423cfda80ba39249559173ca1dc08477447092af72c`.
Outcome ledger SHA-256:
`3746a6d5098ed8608b2e2cf035884430af89f4aa80ec67232d63d37eb3436247`.
The static package bound 253 files and passed with zero engine transitions.
Two Luna Max auditors approved the package before the one-shot loss run.

The 6d baseline combines 12 directly run rows with behavior-equivalent reused
rows. The full-goal manifest pins the source manifest and combined result file;
the audit found the source `reuse_rows.json` currently matches its recorded
hash, but this package does not recursively verify that source manifest or
directly bind that reuse file. Treat that as a provenance caveat. The saved
top-20 receipt, candidate, panel, loss tapes, trace files, and run code are
hash-bound in the new package.

Decision: retain Ghost + Kwa as an offline base with two confirmed rescues;
do not promote it because the 27/30 loss goal failed and the evidence uses
saved action tapes. Continue with an isolated target/control experiment on
Civitasmass. `main.py` remains unchanged and Kaggle was not accessed.
