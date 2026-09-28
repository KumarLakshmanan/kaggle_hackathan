# MELON/MILK sale-timing screen — 2026-09-28

## Decision

**Reject a blanket earlier-sale rule at feasibility; no candidate outcomes were run.** The replayed quote paths show a modest early-gross-receipt opportunity at the first held turn, especially for MELON, but they do not establish a paired-margin gain. MILK is mixed across the 30 loss episodes at that first observable turn, and the much larger last-held-turn spread uses a hindsight endpoint. Adding our sales changes the shared market price and the rival's later receipts; these fixed action tapes do not react. The movement-based sale-timing mechanism was already rejected after improving cash margins by only 211–379 coins in ten saved games without a new both-seat win ([prior results](../shunki_sale_model_20260927/RESULTS.md)).

## Frozen corpus and method

- The incumbent was `main.py` SHA-256 `4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed`.
- I read the 30 exact native loss traces in `diagnostics/loss_class_20260927/traces/` and the four current top-20 traces in `diagnostics/loss_class_20260927/top20_traces/` (DECEM, Boey, Vadim Vasilenko, and Majkel1337 as a winning control). The current frozen target and promotion gate are in [PLAN.md](../local_target_20260928/PLAN.md).
- A held turn has positive MELON or MILK shed stock and no same-item `SELL` in the candidate's submitted market queue. Consecutive held turns form a spell. Rival sales count only successful native `SELL` events.
- At the first and last turn of each spell, I compared that turn's quoted price to the per-unit realized prices at the candidate's first later successful sale turn. Matched units are `min(shed units at reference turn, units sold at that later turn)`. “Early gross advantage” is the matched units' current quoted value minus those later receipts. This is a quote-path diagnostic, not a simulated or causal counterfactual; it does not track unit identity through worker transfers, and an earlier sale changes later prices.

## Hold frequency and market capacity

| Corpus | Item | Held turns / episodes | Consecutive spells; spells ≥2 turns | Long spells with rival sales before our next sale | Held turns with rival sale | At 10-order cap | Held turns with scheduled buy orders |
|---|---|---:|---:|---:|---:|---:|---:|
| 30 losses | MELON | 332 / 27 | 71; 31 | 5 spells / 4 episodes | 8 | 57 | 132 |
| 30 losses | MILK | 3,594 / 30 | 512; 263 | 131 spells / 29 episodes | 278 | 293 | 1,755 |
| Four top-20 traces | MELON | 12 / 3 | 4; 2 | 0 | 0 | 3 | 9 |
| Four top-20 traces | MILK | 317 / 4 | 53; 29 | 18 spells / all 4 episodes | 35 | 28 | 168 |

The engine allows at most 10 market orders per turn. A SELL can be appended on the other held turns only if it preserves the existing queue; at the cap it must replace an existing order. Many held turns already have scheduled BUY_PRODUCT, BUY_SEED, or BUY_ANIMAL orders. The counts above are per-turn order instances, not unique long-term commitments.

## Gross quote-path comparison

Positive figures in the risk/upside column mean an actual later unit price exceeded/was below the held-turn quote. Net early gross is upside minus risk. “Later units” is the total number actually sold at the next sale turn; matched units bound the comparison to stock visible at the reference turn.

| Corpus | Item | Reference | Matched / later units | Gross downside risk / upside if later price is lower | Net early gross | Episodes with positive per-episode gross |
|---|---|---|---:|---:|---:|---:|
| 30 losses | MELON | First held turn | 498 / 518 | 79 / 2,959 | +2,880 | 27/27 with a hold |
| 30 losses | MELON | Last held turn | 512 / 518 | 53 / 2,543 | +2,490 | 27/27 with a hold |
| 30 losses | MILK | First held turn | 2,697 / 3,358 | 10,486 / 12,665 | +2,179 | 17/30 |
| 30 losses | MILK | Last held turn | 2,881 / 3,358 | 2,344 / 20,546 | +18,202 | 30/30 |
| Four top-20 traces | MELON | First held turn | 24 / 24 | 6 / 50 | +44 | 3/3 with a hold |
| Four top-20 traces | MELON | Last held turn | 24 / 24 | 4 / 60 | +56 | 3/3 with a hold |
| Four top-20 traces | MILK | First held turn | 272 / 287 | 715 / 1,299 | +584 | 4/4 |
| Four top-20 traces | MILK | Last held turn | 281 / 287 | 103 / 1,823 | +1,720 | 4/4 |

At the first observable held turn, MELON's historical gross quote gap is consistent, but most MELON long spells have no rival same-turn sale and the comparison says nothing about how an extra MELON sale changes shared-market prices. MILK's first-turn gross gap is small and net-positive in only 17 of 30 loss episodes; 13 go the other way. The last-turn sums are not usable as a rule because the endpoint is known only after the spell ends.

## Promotion conclusion

The saved traces establish that unsold stock is frequent and that orders sometimes compete for all 10 market slots. They do not establish an observable price trigger with repeatable paired benefit. Prior public-movement timing already tried advancing planned sales and failed the win gate. I therefore reject a blanket “sell held MELON/MILK earlier” variant and ran no candidate, fixed-tape policy comparison, or reacting native game. Any distinct timing candidate needs its own frozen trigger and both-seat plan under the local 50-entry gate, including price impact and `delta_own - delta_rival`; see [local target PLAN.md](../local_target_20260928/PLAN.md).

`main.py` and `agent.md` were not changed. No Kaggle access, downloads, or uploads occurred.
