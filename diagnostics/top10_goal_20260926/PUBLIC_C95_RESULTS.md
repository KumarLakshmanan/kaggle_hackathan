# Public C95 replacement screen — 2026-09-26

The public Kaggle notebook
[Kaggriculture: Findings from Zero to Top Meta](https://www.kaggle.com/code/raykkretzschmar/kaggriculture-findings-from-zero-to-top-meta)
contains a compressed, exact C95 single-file artifact. It describes a
trajectory-based production plan with market timing for planned wheat and
fertilizer sales. The notebook source was downloaded read-only with the Kaggle
CLI. `diagnostics/public_rayk_top_meta/extract_c95.py` decoded only literal
source data, without executing the notebook. The extracted file was 75,098
bytes, compiled, and matched its declared SHA-256
`489f5d197527f107027626cce79d850fd2ca90edd43d94384b849b6511e27bdb`.

The predeclared independent native seeds were 2609900–2609907. The exact C95
agent played the current local `main.py` reactively under engine 1.32.7, each
candidate seat. All 16 games were DONE. C95 won **0/8 seed pairs and 0/16
seat-games**. Its mean per-seat terminal margin was **-34,386.8125** coins;
every seat margin was negative, from -24,225 to -66,633. Maximum measured C95
call was 205.2 ms with four concurrent local workers. The results and both
players' terminal cash are in `public_c95_vs_main_8native.json`.

**Decision: reject C95 as a replacement for local `main.py`.** The notebook's
historical public scores and tournament panel characterize its own prior
population; they do not establish strength against this local policy or the
latest leaders. The source is useful research context on ordered market
actions and demand, but this screen supplies no reason to adopt its artifact.
No `main.py` edit or Kaggle upload occurred. This test is against one reacting
opponent and does not prove universal weakness.

Reproduce from the workspace root:

```powershell
python -B -X utf8 diagnostics\public_rayk_top_meta\extract_c95.py
python -B -X utf8 diagnostics\top10_goal_20260926\public_c95_reactive_screen.py
```
