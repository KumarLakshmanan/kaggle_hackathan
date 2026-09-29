# Ghost + Kwa + Pizza/Ice Cream 100-seat panel results

## Decision

**Keep the V5 composition for offline research; do not promote it.** It preserves all 20 top-team replays above the 90% target, but reaches only 25/30 sweeps on the saved loss panel, below the 27/30 target. Continue with an isolated experiment aimed at the five residual loss fixtures.

## Run and candidate

- Candidate: `8f939ada634f8c1ab57991a6903c731f86551a5bd1e22766987abab752db0c62`.
- Parent V4: `7b354498ef2f7213e24ecb332d92d291d9515b94b2a7a845058e829572c0fca2`.
- Panel: 50 fixtures / 100 seat-games (30 loss fixtures and 20 top20 fixtures).
- Panel SHA-256: `97f1edb85397081d9278cc8b25be1defe018d3062e35c8ce1691ea37f3b9fb48`.
- Outcome receipt SHA-256: `c98768b1d7215e1a2adf9e455b103e391a9a338b3202773939ad8bf8f4beeb6f`.
- Outcomes ledger SHA-256: `7d841687b5c6759b0f39a68f586d63f4a906b29be2b689c8575a22b2ca46d864`.
- Frozen manifest SHA-256: `416c575eb3035e8775177016c33002bf2a9d8465a498516f85b9b4465b0befe7`.

## Results

All 100 games completed DONE/DONE at 720 frames with telemetry passing. Every non-Civitas row (98 seats, including the existing Ghost and Kwa targets) matched direct V4 result, candidate and opponent rewards, margin, statuses, and frames exactly. The two Civitas seats changed from losses at `-8,178` to wins at `+1,539`, a `+9,717` margin change each.

| Panel | V4 | V5 | Goal |
|---|---:|---:|---:|
| Loss fixtures swept | 24/30 (80.0%) | **25/30 (83.3%)** | 27/30 (90%) |
| Top20 fixtures swept | 19/20 (95%) | **19/20 (95%)** | 18/20 (90%) |

The five remaining loss fixtures are unchanged from V4 on both seats:

- `live-114218866`: `-53,956` / `-53,956`
- `live-114223292`: `-33,224` / `-33,224`
- `live-114260122`: `-32,028` / `-32,028`
- `live-114270587`: `-18,815` / `-18,815`
- `live-114274897`: `-17,760` / `-17,099`

The sole top20 fixture not swept remains `top20-01-DECEM-114267880` at `-9,085` in both seats; its outcome matches V4 exactly. The 100-seat receipt is marked `passed: false` only because loss30 is 25/30, below 27/30.

## Limits and next step

These are fixed saved opponent-action tapes in the local native simulator. They measure this frozen panel only and do not establish performance against reacting opponents, a Kaggle score, or promotion readiness. Continue by testing a new isolated change against the five loss targets and a control panel that protects the 19/20 top20 result.

Root `main.py` remains at SHA-256 `4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed`. Kaggle was not checked or accessed.
