# Kaggriculture live code-example static comparison

This report is static: it reads downloaded notebook sources and decoded literal agent payloads. It never executes notebook cells or submits to Kaggle.

- Extracted payloads: **9**
- Unique source hashes: **9**
- Duplicate rank groups: **none**
- Production file: `H:\hackathan\main.py` (2,892,150 bytes; 31,975 lines)

## Extracted sources

| Rank | Title | Bytes | Lines | Agent defs | Main markers | Hash |
|---:|---|---:|---:|---:|---|---|
| 5 | Kaggriculture, Visualized: What Every Crop Pays | 3,722 | 83 | 1 | market=21, seed=11, harvest=4, sell=3, weed=3, buy=1 | `5895dbb1f1cb` |
| 26 | Kaggriculture Mathematical Exploit Agent | 9,388 | 208 | 1 | market=26, buy=11, seed=8, fertilizer=7, pickup=3, pasture=2 | `99e4f796b15f` |
| 29 | Kaggriculture Carrot Fleet: Simple Python Baseline | 5,685 | 186 | 1 | seed=13, market=5, harvest=2, sell=2, buy=1, weed=1 | `783899022db1` |
| 37 | kaggriculture-agent-builder | 7,573 | 209 | 1 | market=18, buy=5, fertilizer=2, pasture=2, pickup=2, harvest=1 | `23b0d0c93bcf` |
| 50 |  The Complete Getting-Started Guide | 6,343 | 161 | 1 | seed=13, market=11, harvest=3, sell=3, buy=2, milk=1 | `4801bac332f4` |
| 58 |  Kaggriculture | 40,824 | 1,554 | 1 | seed=121, market=36, sell=32, buy=30, milk=28, harvest=23 | `77ddc97f12ba` |
| 59 | Kaggriculture / Ultimate Mega-Ensemble 3000+ | 1,238 | 42 | 1 | market=10, route=2 | `bc2213715fe3` |
| 66 | Kaggriculture: full engine teardown + my agent | 58,013 | 1,258 | 1 | sell=48, market=35, buy=30, route=25, seed=24, fertilizer=15 | `8fb49dce3b29` |
| 79 | kaggriculture_utils_v1 | 318,226 | 3,367 | 27 | market=292, route=173, sell=145, fertilizer=131, buy=100, seed=73 | `3abe0ca715ba` |

## Interpretation

These are static source observations, not strength results. Keyword counts and parseable function structure do not establish that an agent is valid, fast, or competitive; any source selected for head-to-head testing must first be reviewed and run in a controlled benchmark.

The production agent remains unchanged by this report. Experimental router files and replay benchmarks are kept separately so a future promotion can be audited against the same panel.
