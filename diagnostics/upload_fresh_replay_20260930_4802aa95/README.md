# Requested experimental upload: 4802aa95

Kaggle accepted **submission 56685623** at **2026-09-29 19:15:57 UTC /
2026-09-30 00:45:57 IST**. The authenticated listing at 19:16:00 UTC
verified **PENDING**, with no score yet. All eight operational checks passed.
The exact file, hashes, one upload attempt, and status are in
`upload_receipt.json` and `loader_parity.json`.

## Authorization and identity

The user explicitly requested: "ok so can you upload that new candidate to the kaggle please".
This package permits one upload of the previously discussed candidate as `main.py`.

- Source: `../../main_candidate_fresh_replay_20260930_4802aa95.py`
- Exact SHA-256: `4802aa95c1b960f6bdba3ac313870a847dba8e93dce7d22edfeaca4cee7c19f4`
- Expected Kaggle callable: `kaggle_fresh_execution_schedule_entrypoint`
- Root `main.py` remains `4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed`.

## Evidence and limits

The research report is `../fresh90_improvement_20260929/RESULTS.md`.
Against the newest saved top100, candidate wins are 156/200 versus baseline
132/200. Top20 wins are 36/40 versus 32/40. Two reserved saved sets total
269/400 versus 263/400. These are fixed replay comparisons.

The reacting screen was 34 wins / 26 draws / 4 losses, versus baseline
34 wins / 30 draws / 0 losses. The candidate **failed research promotion**.
This is an explicitly requested experimental upload, with no promise of a
rating gain. The greater-than-90% objective remains unmet.

## Operational verification

`verify_loader.py` stages the exact bytes and checks the real Kaggle loader
and native framework against the reacting cb76 baseline, in both seats.
It uses the existing loader control seed 12929001 and the already-exposed
regression seed 22929006, each with direct and file loading: eight games.

Required checks: correct entry point, 720 frames, 719 calls per player,
DONE/DONE, no errors or timeouts, nonnegative remaining overage, exact
action and reward parity between direct and file loading, and unchanged
candidate, baseline, and root-main hashes. Success is recorded only in
`loader_parity.json`; script presence does not establish success.

These checks establish upload execution only. They do not reverse the
research rejection or consume the reserved confirmation seeds. Historical
research receipts are preserved.

## One upload and audit trail

After operational checks pass, `upload_once.py --submit-once` records the
attempt before calling the authenticated Kaggle CLI. It refuses repeat
attempts and matching existing submissions. Inspect `upload_receipt.json`
and the before/after listings if the network response is ambiguous.

Upload success, submission ID, timestamp and evaluation status are verified
through the submission listing and recorded in `upload_receipt.json`.
An accepted upload with PENDING status is not a completed evaluation.

## Authentication recovery

The first attempt stopped at the read-only submissions preflight because
the CLI requested authentication; it never called the submit endpoint.
Browser automation could not initialize. The supported `kaggle auth login`
command confirmed an existing cached login. `with_cached_auth.py` used the
official token command and passed its output only in the child process
environment, without printing or writing the token. The authenticated probe
matched the expected prior submission IDs, after which exactly one upload
succeeded. Future repeat uploads still require a fresh user request.
