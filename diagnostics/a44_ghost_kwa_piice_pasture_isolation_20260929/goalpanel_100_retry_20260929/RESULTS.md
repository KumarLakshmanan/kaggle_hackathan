# Full saved loss30 and top20 panel: isolated THIRD pasture route

## Outcome

The retry completed all 100 frozen native fixed-tape games, with 100 unique
fixture-seat rows. Every game finished DONE/DONE at 720 frames; all candidate
telemetry checks passed. Both `live-114274897` / THIRD seats won, at margins
`+5,983` and `+2,235`. All 98 non-trigger rows matched V5 on result, rewards,
margin, statuses, frame count, and prior-policy telemetry.

| Panel | V5 parent | Candidate | Threshold | Result |
|---|---:|---:|---:|---|
| Saved loss30 both-seat sweeps | 25/30 (83.3%) | **26/30 (86.7%)** | 27/30 | Missed by one fixture |
| Saved top20 both-seat sweeps | 19/20 (95%) | **19/20 (95%)** | 18/20 | Passed |

The remaining loss fixtures are `live-114218866` (margin `-53,956`),
`live-114223292` (`-33,224`), `live-114260122` (`-32,028`), and
`live-114270587` (`-18,815`). One both-seat rescue among them would raise this
panel to the requested 27/30. The two rescued seats add `+43,077` combined
paired margin versus V5 (`+23,743` and `+19,334`), a `+430.77` mean over all
100 seat rows; the other 98 margins are unchanged.

## Frozen provenance

- Candidate SHA-256: `6a0a3b38782ba21a4933827888b503dae00fe73182599bc8c801302f959372dc`
- Exact V5 parent SHA-256: `8f939ada634f8c1ab57991a6903c731f86551a5bd1e22766987abab752db0c62`
- Panel SHA-256: `418a1be5beb005509a02206d315954b209f67061b3a1c9e7767bdfe3c8f499df`
- Frozen manifest SHA-256: `66b03619639f915196f6929ffaeb60e3bf98d846ad6ea3a24b6e46e8bf88901c`
- Outcome receipt SHA-256: `f5b962c853b8812f231c85af41a608e6df1b1ede99dd14c22a2bcaeb10bc8b2`

The first attempt in `../goalpanel_100/` stopped after 93 flushed rows because
Windows cp1252 could not print a non-ASCII fixture name. Its partial ledger is
preserved and separately documented in `../goalpanel_100/INTERRUPTED_ATTEMPT.md`.
The retry used ASCII-escaped logging, restarted all 100 rows, and wrote this
complete receipt. The runner's `passed` field is false solely because the
predeclared loss threshold is 27/30 and the candidate achieved 26/30.

## Decision and scope

Keep the candidate as an offline research artifact; do not promote it. The
top20 threshold passes, but the loss30 threshold does not. These are saved
fixed action tapes, not reactive validation against changing opponents. Root
`main.py` remains SHA-256
`4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed`;
Kaggle was not checked or changed. A subsequent candidate needs a second
loss-fixture rescue while preserving the top20 panel.
