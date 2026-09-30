# Interrupted full-panel attempt

The one-shot runner completed 93/100 rows, then stopped while writing a
progress line for a non-ASCII fixture name to the Windows cp1252 console. The
game row had already been flushed to `outcomes.jsonl`. No final outcome receipt
was written, so this is not a completed 100-seat result.

Candidate SHA-256: `6a0a3b38782ba21a4933827888b503dae00fe73182599bc8c801302f959372dc`.
Parent V5 SHA-256: `8f939ada634f8c1ab57991a6903c731f86551a5bd1e22766987abab752db0c62`.
Panel SHA-256: `418a1be5beb005509a02206d315954b209f67061b3a1c9e7767bdfe3c8f499df`.

The partial ledger contains 93 unique rows: 60 loss30 seats and 33 top20
seats. Every recorded row completed DONE/DONE at 720 frames and passed
telemetry. All recorded non-trigger outcomes and telemetry match V5. Both
THIRD target seats won (+5,983 and +2,235); the final recorded row is seat 0
of top20 fixture `top20-17-有辣条有权-114262952`.

`outcomes.jsonl` SHA-256:
`547cb41046b6955bbb22a0a6325190ab26e6d998fa8cbab5b0ae4d34b157a39d`.
The retry is isolated at `../goalpanel_100_retry_20260929/`, retains the same
candidate and panel hashes, and uses ASCII-escaped progress output. It starts
from row one; this partial ledger is preserved and is not resumed or combined
with the retry receipt.
