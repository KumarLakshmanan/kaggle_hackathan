# When high-strawberry rivals become visible — 2026-09-26

`analyze_opening_signals.py` inspected existing exact native traces against
four saved high-ranked rival routes. The current agent buys all twelve of
its opening melon seeds by turn 17 and plants them by turn 18 on the DSM
trace; its first strawberry seed purchase is at turn 130.

| Rival trace | First visible rival strawberry | First visible rival strawberry lead over us |
| --- | ---: | ---: |
| Lucas Boesen | turn 14 | turn 14 |
| DSM | turn 63 | turn 63 |
| Arda Ceylan | turn 63 | turn 63 |
| Boey | turn 87 | turn 87 |

Lucas reveals its lead before only the last two opening melon seeds are
bought at turn 17. DSM, Arda and Boey reveal their strawberry lead after
every opening melon seed has been bought and planted. A policy that waits
for a visible strawberry-tile lead therefore cannot decide the original
melon-to-strawberry opening swap in those three matchups. It would need an
earlier public signal, a different default opening, or a funded later
expansion with workers and crop care.

This is a read-only timing diagnosis on four saved scenarios, not proof that
early adaptation is impossible in general. **Decision: do not promote a
strawberry-tile reactive opening gate from this evidence.** No `main.py`
change or Kaggle upload.
