# Frozen bridge pilot — 28 September 2026

## Decision: both variants rejected under their frozen advance gate

The 48-game development pilot completed at
2026-09-28T17:29:34.233005+00:00, exit 0. Every game was clean: 720 frames,
DONE/DONE, zero policy errors/collisions, zero common/source procurement
failures, zero donor guard refusals. Both variants passed the earlier
physical feasibility study but failed this separate competitive gate.

| Policy | Wins/draws/losses | Both-seat wins | New rescues | Regressed source-winning fixtures | Advance |
| --- | --- | ---: | ---: | --- | --- |
| Exact32e control | 14/0/10 | 7/12 | — | — | Control |
| five_hand ceed697f | 16/0/8 | 8/12 | 2 | Boey | Reject |
| five_or_zero be5172f7 | 10/0/14 | 5/12 | 2 | offhand, Yaroslav, Boey, Vadim | Reject |

All regressions occurred in both seats. The two new rescues in each
variant were public fixtures booming114232208 and mhw114235177. The
frozen gate required preserving every source-winning seat, so five_hand's
net gain in wins does not make it a pass. No full50 stage is inherited or
launched from this result. Any prospective review of the user's explicit
18/20 top-team objective requires a new plan before untested outcomes;
this receipt and rejection remain unchanged.

## Native transition margins

Values are candidate cash minus rival cash. A single value denotes the
same result in both seats; two values denote seats0/1.

| Saved opponent | Exact32e | five_hand | five_or_zero |
| --- | ---: | ---: | ---: |
| booming114232208 | -13,830 | +5,539 | +5,539 |
| mhw114235177 | -9,646 / -29,166 | +9,994 / +9,145 | +9,994 / +9,145 |
| booming114279308 | -26,613 | -23,186 | -23,186 |
| Ghost114288168 | -2,085 | -2,085 | -3,366 |
| carbonapi114215872 | +9,413 | +9,413 | +419 |
| leaveyou114289228 | +3,256 | +3,256 | +1,159 |
| offhand114271958 | +670 | +670 | -23,790 |
| Yaroslav114283577 | +902 | +902 | -32,743 |
| Boey114266440 | +4,935 | -1,943 | -1,943 |
| Vadim114265033 | +16,140 | +16,140 | -26,219 |
| Majkel114263239 | +13,889 | +2,867 | +2,867 |
| DECEM114267880 | -9,085 | -9,085 | -18,375 |

The five_hand selector improved mean seat margin by 2,822.625 coins;
five_or_zero reduced it by 7,354.542. Each row in the receipt records
delta own cash, delta rival cash and their difference. For example,
booming114232208 seat0 improved own cash by 14,681 and reduced rival cash
by 4,688, yielding +19,369 paired margin. Against mhw seat0, own cash fell
26,685 but rival cash fell 46,325, yielding +19,640 paired margin.

The 114279308 game actually revealed PET_CAFE|ICE_CREAM_SHOP at turn144;
the donor correctly retained default route0. Its archived
FARMERS_MARKET|ICE_CREAM_SHOP label was never treated as a future-shop
promise. Boey's regression shows that a public five-hand opening is not
sufficient to select donor151 safely under the frozen preservation gate.
The zero-hand extension introduced several further regressions.

## Evidence and limits

These are saved-tape development games using verified cached native
transitions, not independent reacting-policy validation. Framework schema,
timeout and actual file-loader checks were not performed for these
candidates. Maximum observed individual candidate call was 0.445 seconds
in this diagnostic harness, which is not a timeout qualification.

- Exact five_hand SHA-256:
  `ceed697f9af3927fe4abc5b62e9e1e0ad7358361b3581a087da86558c8294d46`.
- Exact five_or_zero SHA-256:
  `be5172f7db0df094a61c22279b0d9e944445d501e7ad63493c43157257e1e47a`.
- `development_results.json` SHA-256:
  `224cae4a3f69ac480ee2979db33df1d21aaaa5ff3ba2cfa3f2c3183fbdd91605`.
- `development_pool.json` SHA-256:
  `99df986a45fb3835d1b1873739b53ae865bd5d2896f083bef4c137be70f7ca78`.
- `development.py` SHA-256:
  `5a1fa8e15d67daaf5ade0946689171804a676321f9970b1bad909bdff4befe71`.

All bound artifacts were rechecked unchanged after completion. The pool
contains the exact32e original-native controls and immutable fixture
bindings; each per-game trace is separately hashed in the receipt.
Reproduction uses `development.py prepare` then `development.py run` in
a clean evidence copy, respecting its overwrite guards. Root main/source,
existing donor files and plans, and Kaggle remain unchanged.
