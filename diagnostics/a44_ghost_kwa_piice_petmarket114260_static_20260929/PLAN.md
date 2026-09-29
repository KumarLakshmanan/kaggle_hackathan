# 114260122 Pet Cafe market gate: static stage

## Frozen question

Can the existing route `113517834` be selected on the exact Ghost + Kwa +
PiIce 8f parent at step 72 using only public state:

`PET_CAFE|M8+|C>S|G0`, rival visible MELON count `== 12`, and public market
WHEAT inventory `== 9975`?

The expected target is both seats of `live-114260122`. Both seats of
`public-win-114192390` are the named no-change control. A candidate may be
frozen only if the 208-trace census triggers exactly the two target seats,
the control stays inactive, exact-parent composition and route identity pass,
and saved-observation action comparisons show no unexpected changes.

## Static scope

- Parent bytes must equal exact V5 8f
  `8f939ada634f8c1ab57991a6903c731f86551a5bd1e22766987abab752db0c62`.
- Route 113517834 must exist in the 8f route table and match the bound source
  schedule byte-for-byte after canonical JSON serialization.
- Verify all 208 frozen observation-trace hashes, then count the public gate.
- Compare the parent and candidate policy actions on the same saved
  observations. This calls policy functions only; it performs no engine
  transitions.
- Bind the 8f 100-seat panel, its panel builder and runner, its preflight,
  parent composition artifacts, route source, feature inventory, and all
  trace files.

There is no game runner in this package. The 8f panel and source feature traces
are fixed-tape evidence; they do not establish reacting-opponent performance.
This package cannot authorize a terminal game, promotion, or upload.
