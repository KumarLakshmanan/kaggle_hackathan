# Public melon pressure guard for Goose4 Pizza route

## Status

Static-only derivative of exact parent candidate 257f. No game transitions,
replay execution, network access, or Kaggle operation occurred. This is a
narrow fixed-panel hypothesis, not a promotion or an independent validation.

## Hypothesis and selector

At step 72, when the source branch reaches the existing public leaf
`PIZZA_SHOP|M8+|C<S|G0`, the Goose4 route 113470868 rescues Dieter
114249897 but sharply worsens Pensukesan 114218866. In the frozen 208-seat
source observation census, the only rows for this leaf are those two fixtures:
Pensukesan has 12 publicly visible rival MELON plots in both seats, while
Dieter has 10. The source-side saved margins are -8,665 and -5,454; the exact
257 preservation receipt records -53,956 and +27,854 respectively.

The derivative keeps the existing 113470868 route when the public rival farm
has fewer than 12 MELON plots. At 12 or more it leaves the route map unchanged,
so the step-72 experimental route is not committed. The economic rationale is that a larger visible rival melon footprint is a
public proxy for a more productive opponent and greater shared-market
response. In the prior saved route screen, route 113470868 raised our target
reward by 12,316 but raised the rival reward by 57,607 versus the saved source
row. This motivates checking the optional route under a higher rival
production footprint. The channel is not proven: this is a sparse, fitted
hypothesis based on one fixture, and the census does not establish that the
threshold generalizes or that rival melon count caused the margin change.

The selector uses only the already-public shop/cow/sheep/GOOSE leaf and the
rival farm's publicly visible tile crop values. It does not inspect fixture
identity, seeds, private inventories, cash, or hidden state. Its step-72
fallback fires on exactly two of 208 frozen rows, both Pensukesan seats; it
retains 113470868 on both Dieter seats and fires on zero top20 or public-win
rows. The separate 113517834 alternative is excluded: its prior frozen screen
scored Pensukesan at -58,600 and Dieter at +6,073/+5,948, worse than 113470868
on both fixtures.

## Frozen test, if root authorizes the panel

Run four terminal games from the same saved opponent tapes: both seats of
Pensukesan 114218866 and both seats of Dieter 114249897. The parent is exact
257f (`257f941d…bad55`), not an older 6d/a44 policy.

- All four games must finish DONE/DONE at frame 720 with zero policy or
  telemetry errors.
- Both Pensukesan seats must have margins strictly above the exact 257f
  parent margin (-53,956); report the saved a44/source margin (-8,665) as a
  separate historical reference, not as the 257f parent result.
- Both Dieter seats must exactly preserve the 257f result and rewards
  (win; own 124,604, rival 96,750, margin +27,854).
- Pensukesan telemetry must report the source branch, the exact leaf, public
  melon count 12, fallback true, no Goose4 route commit, and no errors.
  Dieter must report count 10, fallback false, route 113470868, and no errors.
- Any failure rejects this derivative. Even a pass would be a narrow saved
  tape repair only; promotion requires independent reacting evidence and a
  broader predeclared panel.

## Frozen inputs

See `frozen_manifest.json` and `static_preflight.json` for candidate, parent,
receipt, 208-row census, four bound trace hashes, and the prior route screen.
