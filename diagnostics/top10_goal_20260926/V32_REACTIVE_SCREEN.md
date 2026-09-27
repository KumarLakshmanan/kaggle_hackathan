# Local v32 portfolio reactive screen — 2026-09-26

The local `main_v32_observable_portfolio.py` (SHA-256
`9cb69949b55e2a781d1f19f2ef036fccecf588bae0722ce0cfd30d9e161e39ba`)
was compared with the current `main.py` hash
`489fe8e4...` on four predeclared fresh native seeds 2612000–2612003,
both seats. The two agents executed reactively; this did not replay saved
opponent actions. All eight games ended `DONE`.

The v32 file lost every seed pair and all eight seat-games. Mean seat margin
was −47,765.75 coins; paired seed margins were −115,996, −78,602,
−112,952 and −74,576. There were no draws or wins. Raw per-game rewards,
statuses, timings and source hashes are in `v32_reactive_fresh4.json`.

**Decision: reject the local v32 file as a replacement for the current
agent.** Its old historical Kaggle score is not evidence of current strength.
No `main.py` edit or Kaggle upload followed this screen.
