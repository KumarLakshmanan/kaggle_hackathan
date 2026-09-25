# Four near-tie loss traces — 2026-09-25

The frozen `main.py` (SHA-256
`04b0bdc3bbe319d969170ddc8007bd6300af254a98151d6ef990c9ed2ebbabc1`)
was replayed in candidate seat 0 against four exact top-50 public action
tapes, using native Kaggriculture 1.32.7. All four games finished `DONE`.

| Route episode | Our final cash | Opponent final cash | Margin | Final `SELL` orders | Post-game shed |
| --- | ---: | ---: | ---: | ---: | --- |
| marwar22 112934493 | 57,331 | 57,415 | −84 | 5 | empty |
| Yannik Schiffner 112937001 | 144,082 | 144,247 | −165 | 2 | empty |
| feles99 112939452 | 89,029 | 89,202 | −173 | 3 | empty |
| hiroshi murakami 112936862 | 61,929 | 62,095 | −166 | 3 | empty |

The terminal action left no carried product with an actor that failed to
`DROP`/`PLACE`, and no inventory remained in the shed. The agent's final-turn
liquidation is not the cause of these narrow losses. Day-30 hires were real
productive work (harvesting and delivery among the tasks), so indiscriminately
removing hires to save their 232- to 609-coin daily costs is not justified by
this trace. No policy change was made on the strength of these four cases.

Source event traces are `neartie_marwar22_trace_20260925.json.gz`,
`neartie_Yannik_trace_20260925.json.gz`,
`neartie_feles99_trace_20260925.json.gz`, and
`neartie_hiroshi_trace_20260925.json.gz` in this directory. This diagnostic
does not imply that earlier sale timing or production choices are optimal.
