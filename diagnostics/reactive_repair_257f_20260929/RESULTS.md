# Reactive route-map audit for upload 257 — 2026-09-29

## Decision

Reject the blind mirror-gated fallback as a candidate change. The public
trigger is narrow and observable, and it does not overlap the saved
BRUNCH/PIZZA wins, but the existing mirror flag does not establish that the
incumbent route is compatible with the candidate's day-six state. No
candidate was built and no games, transitions, network calls, or edits to
`main.py` or `agent.md` were made.

## Evidence

- Root `main.py` is SHA-256
  `4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed`.
  Its embedded route map selects **113784024** for
  `BRUNCH_SPOT|PIZZA_SHOP`; the only source-level map rewrite at lines 49–51
  changes entries whose route is 113445495.
- The uploaded candidate source is
  [main.py](H:/hackathan/diagnostics/upload_pet_source_guard_20260929_257f941d/main.py:654),
  SHA-256
  `257f941d06fcd6dd9185ca58bc98d1af83dc4c3fafc24e275a1bf057b61bad55`.
  Lines 654–660 replace this pair and every longer matching prefix with
  route **113413613**. The paired route telemetry is recorded from step 144
  onward.
- In the 96-game reactive receipt
  [outcomes.jsonl](H:/hackathan/diagnostics/a44_ghost_kwa_piice_petmarket114260_reactive_20260929/outcomes.jsonl),
  SHA-256
  `055bb21dcb06ff7237e6e628c92c173e9b0d40f57fdc1d712b8d3f42b61c8c1f`,
  each of the three tested policies (a44, 6a, and 6a+Pet) scored 16/10/6
  W/D/L overall, with identical row rewards and margins. Against root 4ee,
  each scored 1/4/3. The exact 257 file was **not** an arm in this panel;
  this receipt cannot be presented as a direct reactive result for 257.
  On seed `2026092911`, both seats had pair
  `BRUNCH_SPOT|PIZZA_SHOP`, `mirror_quantity_active=true`, selected route
  113413613, and lost by 3,203. On the other three seeds the pair did not
  trigger this loss-pool replacement; losses/draws there are not explained
  by this route hypothesis. The receipt SHA-256 is
  `86d70abbf809baf29c6227141036624131856bed40b7f04664f13ba7093693c9`.
- The 102-row guarded-257 preservation ledger
  [preservation_outcomes.jsonl](H:/hackathan/diagnostics/pet_source_guard_20260929/preservation_outcomes.jsonl),
  SHA-256
  `5079974842ce4ef889b49832d4287057650482f93284004c3d97de5476055790`,
  has four same-pair seats, all with `mirror_quantity_active=false` and
  route 113413613: `live-114257327` wins both seats at +2,992; and
  `live-114274897` wins at +5,983 / +2,235. Thus a condition requiring both
  the exact pair and the mirror flag would leave those saved wins untouched.
  Vadim (`top20-05`, +16,140 both) has a Smoothie/Ice Cream pair and mirror
  false; Majkel (`top20-06`, +2,867 both) has no loss-pool pair. Both saved
  top-team controls are outside the proposed trigger.

## Compatibility limit and next step

The candidate's `_mirror_quantity_signature` at lines 266–285 compares
unlocked quadrants and placed tile dictionaries. It omits hand count, weeds,
cash, and private inventory. It therefore signals mirrored farm layouts,
not a complete route starting state.

Static route data also show a substantial branch difference: routes 113784024
and 113413613 each contain 719 actions and differ on all 575 turns from step
144 through 718. At step 144, 113784024 collects fertilizer with three hand
orders, while 113413613 passes with four hand orders and uses a different
fertilizer, hire, seed, and wheat market bundle. The reactive package has no
step-144 state trace to establish that the 257 candidate can safely enter the
incumbent schedule. Farm-layout equality alone is not enough to choose it.

The useful follow-up, if revisited, is a prospective exact-pair experiment
only after a full own-state/start-schedule compatibility check is available.
Keep the trigger public (`BRUNCH_SPOT|PIZZA_SHOP` plus the documented mirror
predicate); do not key on seed or opponent. Until then, leave route 113413613
unchanged and make no win or transfer claim from the reactive/fixed panels.
