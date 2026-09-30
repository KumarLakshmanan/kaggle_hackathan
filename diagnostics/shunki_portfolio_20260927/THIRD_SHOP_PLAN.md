# Later-shop route audit — 2026-09-26

The frozen two-shop lookup gained margin on 29/32 new seeds but had one
large ICE_CREAM_SHOP/BRUNCH_SPOT regression. Its selected public route
had FARMERS_MARKET as the third shop, while the new game's third shop was
YARN_STORE. Three same-pair public routes first diverge around turn 216.
Audit whether recorded route variants can be selected using each shop
only after it appears, without relying on future shops or source seeds.

For all 203 frozen source episodes in `route_manifest.json`, fetch the
public replay and extract the visible shop sequence at turns 72, 144,
216, 288, 360, 432, 504, 576, and 648. Verify each replay's SHA-256,
submission team/seat, and first-two shops against the frozen manifest.
Keep only compact shop sequences and hashes; newly downloaded full replays
can be removed after verification. Compute third-shop coverage per first
two shops, and exact action-prefix compatibility among routes sharing
the same first-two shops until turn 216. Early differences due visible
market/farm state must be reported, not hidden.

Only after this audit, decide whether to build a separate third-shop
candidate. Any candidate needs both-seat loader checks and new, untouched
reactive seed blocks; old development/robustness outcomes cannot validate
its performance. No `main.py` edit or Kaggle upload without the required
evidence and fresh user authorization for upload.
