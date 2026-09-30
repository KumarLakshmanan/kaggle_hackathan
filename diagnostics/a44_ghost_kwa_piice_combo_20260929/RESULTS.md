# Ghost + Kwa + Pizza/Ice Cream paired diagnostic results

## Decision

**Keep as a promising offline candidate; continue to the full saved loss30 and top20 panel. Do not promote to `main.py`.** This was a fixed-tape run and does not establish performance against reacting opponents.

## Candidate and panel

- Parent Ghost + Kwa candidate: `7b354498ef2f7213e24ecb332d92d291d9515b94b2a7a845058e829572c0fca2`.
- Composed candidate: `8f939ada634f8c1ab57991a6903c731f86551a5bd1e22766987abab752db0c62`.
- Frozen panel: four fixtures and eight seat games; target `live-114238112` plus three same-key public-win controls.
- Panel SHA-256: `ecf09fbde109bc13922f16851257939923ada9f158dc4e33c2e5e6b1a0f4b247`.
- Outcome receipt SHA-256: `7d9e9ae29f420e361aec8c3d060089eb8dd969416bf2b65cb2fd23812fada14e`.
- Static preflight SHA-256: `d6940502e6c2c0c4e8892f76e47fac848ecf3dcaac30479969b7735408cfc9df`.

## Results

Both target seats changed from parent losses at margin `-8,178` to wins at `+1,539`, improving paired margin by `9,717` per seat. The layer activated on the exact source-branch step-72 key and step-144 public shop pair, selected route `113339524`, ran 575 turns, and reported zero errors.

All six controls matched the direct V4 parent on result, candidate and opponent reward, margin, statuses, and 720-frame completion. All eight games were clean and all activation checks passed. Ghost and Kwa remained inactive in these Pizza fixtures.

The static probe made 2,320 policy action calls over saved observations and ran zero game transitions. In the 208-seat saved feature panel, the exact pair appeared only on the two Civitas seats and appeared on zero top20 seats. All eight focus traces matched the direct V4 parent through step 143. At step 144, only the target route map changed, and only at `PIZZA_SHOP|ICE_CREAM_SHOP`; the six control actions remained equal.

## Limits and next step

This candidate has only been tested on the eight focused saved seats. The V4 baseline recorded 24/30 loss fixture sweeps and 19/20 top20 sweeps; the paired Civitas result suggests one additional loss sweep, but the full candidate count must be measured on the frozen 100-fixture panel. The static no-trigger census supports carrying the V4 top20 result forward, but the next panel will also replay all 20 top-team fixtures against this exact composed hash.

Root `main.py` is unchanged at SHA-256 `4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed`. Kaggle was not checked or accessed.
