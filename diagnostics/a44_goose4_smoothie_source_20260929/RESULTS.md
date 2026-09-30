# Goose4 + Smoothie continuation: six-fixture replay results

Completed 2026-09-29 02:17 IST. This is a fixed-action-tape diagnostic, not
independent validation against a reacting policy.

## Frozen candidate and checks

- Exact uploaded a44 source SHA-256:
  `a44c8c2cc453d5b2d0f2be105afe5d650f762fe39674d51cb10d7d54e727090f`.
- Goose4 parent SHA-256:
  `c76dc9078b59b400e4facbf0a70969e6da32c395dc6a1a63fd9bb78cb2b56632`.
- Integrated candidate SHA-256:
  `6d3d1c0df1b06566417d8ba204e05e0caad9a115bb84b73513bef68575a70bf9`.
- Static manifest SHA-256:
  `bb4e44f5d0038ce5fd24c2a9b935e7f341538abe484fef7aa819f38b6c6d900a`.
- Static preflight SHA-256:
  `c472b75e47f4cd953c233d7aa2c0fa68a2b29f6ed3d23931f095268d2a4b727b`.
- All 60 package bindings and all 450 parent Goose4 bindings passed root
  verification. The 12-seat Smoothie predicate covers two loss fixtures and
  four public-win fixtures, both seats each; it overlaps neither Goose4 nor
  the pasture leaf. The other 196 seats are statically decision-equivalent to
  the clean Goose4 parent.
- All 12 new games completed DONE/DONE at 720 frames with zero candidate
  errors and the expected Smoothie activation, pair, route and turn telemetry.
  Receipt SHA-256s: `candidate.json`
  `e2c8ccef4a3584a796f1736c06580ec3f960fdce75154b99508a7fd04d3af3ff`,
  `candidate.jsonl`
  `5a655e7b82944148c91f8265e36abbd807b4fb6e667c23dc018136512db9d0fb`.
- Root independently checked all 208 unique seat keys: the 12 new result keys
  exactly match the frozen panel, and the 196 reused rows are exactly its
  complement. This was a fresh run with no checkpoint resume.

## Saved-panel outcome

| Panel | Goose4 + Smoothie | Exact a44 source | Change |
|---|---:|---:|---:|
| Frozen loss30 both-seat sweeps | 22/30 | 17/30 | +5 sweeps |
| Frozen loss30 seat wins | 45/60 | 34/60 | +11 wins |
| Top20 both-seat sweeps | 19/20 | 19/20 | no change |
| Public-win both-seat sweeps | 53/54 | 53/54 | no change |

The five additional a44 loss sweeps are `live-114223338`,
`live-114229792`, `live-114249897`, `live-114258293`, and `live-114267572`.
No a44 source-winning fixture regressed. Against Goose4 alone, Smoothie adds
one complete loss sweep and two seat wins; it leaves the top20 and public-win
results unchanged. The 90% loss goal is still short by five full sweeps.

On the 12 newly tested seats, paired margin changes versus Goose4 sum to
`+32,684` coins on the four loss-panel seats and `+18,846` on the eight
public-win seats, for `+51,530` total. The public-win margin changes are
uneven across second-shop pairs; for example, `SMOOTHIE_SHOP|BRUNCH_SPOT`
lost 9,317 coins per seat while `SMOOTHIE_SHOP|FARMERS_MARKET` gained
13,512 per seat. Wins remain the primary gate.
The narrowest retained public-win margins are `+1,245` at
`public-win-114216671` and `+330` at `public-win-114248439`; these are useful
margin follow-up targets after the remaining loss-sweep goal.

Combined receipt SHA-256:
`5463a0efa37aebad2c11559cbcd2c39bf2a9a63ec5b2279f409d6360c61ff40d`.

## Decision

**Keep as a separate experimental candidate; do not promote or upload.** The
fixed-tape result improves the frozen loss panel and clears the top20 target,
but it reaches only 22/30 loss sweeps and has no reacting-opponent validation.
It is not yet eligible to replace root `main.py`. Root `main.py` remains
SHA-256 `4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed`.
No Kaggle check, download or upload occurred.
