# Farming method comparisons — 2026-09-27

| Variant | Result | Decision |
| --- | --- | --- |
| Fertilize before an existing watering/fertilizer pair, `e46194f0...` | No eligible swaps in sixteen known-loss games; exact source outcomes | Reject for lack of activation |
| Replace the full carrot crop chain with wheat, `72ba0715...` | 84/100 seat wins; 42/50 both-seat wins; all DONE/DONE | Reject: no net sweep gain |

The crop substitution changes seeds, planting, explicit transfers and sale
products while retaining the original work calendar. It changes marwar22
from -114 to +3,818 per seat, but loses the previously won Kaggledew Valley
matchup (-8,812 per seat). Seven other known-loss margins worsen. Lower
seed cost alone is insufficient: observed first carrot-investment prices
in the Snorlax matchup were wheat 22, carrot 53. The native price audit is
in `crop_price_audit.json`; complete results and hashes are in
`crop_top50.json` and `crop_top50_decision.json`.

These variants do not replace main. During these experiments, the main
leaderboard task promoted and uploaded the independently validated complete
ICE/BRUNCH schedule `3cc0f69f...` as submission 56591314. Its remote loader
validation passed. It wins 42/50 versus the old main's 31/50 both-seat
matchups. The user's all-50 and live top-ten goals remain unachieved.

The old main is backed up in the project root as
`main_before_shunki_promotion_20260927_489fe8e4.py`; uploaded bytes are
`main_uploaded_shunki_schedule_20260927_3cc0f69f.py`. Both experimental
farming scripts remain separate root files, named in `manifest.json`.

No independent confirmation was run for either rejected farming variant.
If their frozen confirmation recipe is reused for a future candidate,
"frozen main" means the `489fe8e4...` snapshot, not the now-updated main.py.
