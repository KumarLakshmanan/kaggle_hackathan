# Candidate status

- Static outcome-blind status: passed. No native simulation or outcome run was performed.
- Plan: `PLAN.md` SHA-256 `e7c2b704a7dca092f8e760ba89df326bb283f44e89053d6c6cf2d88a9567b300`
- Manifest: `manifest.json` SHA-256 `15599920d47d783c127f392460a6b2eeefb7540418ce94a0a9bc6db0af8c0f24`
- Candidate: `candidate_a44_melon_delivery_v2.py` SHA-256 `dbf54f4d89d0c56d89959e858bde7ffd02a160c1c4013c6cf7c80b25b522313e`
- Builder: `build_candidate.py` SHA-256 `52fd610e8a6578369e7feaf81412dbbd944a045af04dbdaa257775ecfb914e83`
- Checker: `check_observation_stream.py` SHA-256 `afb0effbb285e345175a070ddfc762fc096fa031738b108bf372c35286887d9b`
- Receipt: `observation_stream_receipt.json` SHA-256 `0ee2187efb7bc046b6f234351c284bbbbba6f831b716e247288a1c26522bff67`; it binds the final manifest SHA `15599920d47d783c127f392460a6b2eeefb7540418ce94a0a9bc6db0af8c0f24`.

The streaming checker passed exact action/output parity for all 69,024 steps in the 96 nonactivation rows. It validated all four projected activation rows and 12 planned hand/order action transforms, plus latch reset/scope, trigger-only continuation, mismatch clearing, `boardSize=10` requirements, and safe fallback transforms. These are action-transform checks only; the a44 policy was not rerun on counterfactual states.

**Still required before any outcome run:** native step-by-step prefix validation for both seats of offhand and Unknown Mother-Goose, including the candidate state fed into each next parent-policy call. Frozen outcome gates and both-seat margin criteria are in `PLAN.md`.
