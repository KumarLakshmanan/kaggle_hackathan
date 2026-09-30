# Saved first-place Boey plan as a complete policy — 2026-09-26

The September 25 top-100 snapshot has one saved public action history for first-place Boey. Its fixed tape earned 82,596 against local `main.py`'s 74,738 on its original episode seed in both seats. This is an episode, not Boey's executing agent.

I replayed that exact action history as a complete candidate against **reacting** local `main.py` on three predeclared fresh native seeds 2609500–2609502, both seats, under engine 1.32.7. All six games were DONE. The raw plan **lost 0/6 wins** with per-seat margins -10,618, -7,259, and -37,693. Its candidate cash was 121,836, 128,174, and 80,774 versus the incumbent's 132,454, 135,433, and 118,467. The exact artifact is `boey_raw_vs_main_3fresh.json`.

**Decision: reject direct transfer of this fixed action history.** The original-episode win does not generalize across these three shop and market paths. This says nothing conclusive about Boey's unavailable adaptive submitted policy or about selectively importing a separately tested production mechanism. No `main.py` change or Kaggle upload.
