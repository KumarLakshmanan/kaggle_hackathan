# Observation-based worker repair for the Shunki route selector

The 203 public Shunki replays show that an otherwise identical shop route
chooses DIG instead of PASS when a visible weed occupies the worker's tile.
The later-shop selector copies recorded actions, so it misses this response
when a new game's weeds differ. Build a separate single-file candidate from
the frozen later-shop selector (SHA-256 `68aad090...`) that:

- aligns the action's hand list with observed workers;
- replaces an idle PASS on a visible weed with DIG;
- for PLANT/BUILD blocked by a weed, digs only when the next scheduled action
  for that worker is PASS, then replays the displaced action on that PASS if
  the worker remains on the tile.

The route data, shop selector, and market orders are unchanged. Count every
repair and error. Do not use hidden future shops, seed identity, opponent
identity, or rival-private state. Verify Python compilation and Kaggle
file-path entrypoint selection.

Evaluate **fresh native seeds 2630400–2630415**, original shops and both
seats, against a reacting unchanged `main.py`. On the same seeds run the
unchanged later-shop selector and main-vs-main controls. Before considering
promotion require all games DONE/DONE; at least three activating paired
seeds; positive aggregate own cash and paired margin versus the unchanged
selector over activated seeds; no activated paired regression below −5,000;
at least 12/16 positive paired margins versus `main.py`; worst paired
margin versus `main.py` at least −10,000; and first-two-shop parity in at
least 30/32 candidate/main seat comparisons. A passing development block
still needs untouched confirmation. No Kaggle upload is authorized.
