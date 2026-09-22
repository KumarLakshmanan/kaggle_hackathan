"""Kaggriculture v7: the v5 economy, re-aimed from E[money] at P(win).

Per the current #1's writeup (discussion/736219): the ladder rating and the final
Bradley-Terry tournament count WINS AND LOSSES ONLY. The coin margin is worth
nothing, and "most improvements that raise your average coin total but increase
variance are rating-negative." The opponent's farm and bank are public in the
observation, so v7 plays the scoreboard, not just the economy:

  * LEAD TRACKING - each turn, lead = (my bank + liquidation value of my shed)
    - opponent bank. Their shed is private, so the estimate is optimistic;
    thresholds below account for that bias.
  * DEFEND (ahead, late) - stop discretionary spending, sell faster, bank the
    win. When ahead, variance is the enemy.
  * PUSH (behind, late) - hold premium inventory for the seasonal price peak and
    dump in the final days. When behind, variance is the only friend.
  * FRONT-RUN - premium prices are a shared commons; the first seller collects
    the scarcity rent and leaves the crash to the other. If the opponent's farm
    shows more exposure to a product (their cows, their berry tiles), cut our
    floor and sell ahead of their harvest.
  * TOTAL LIQUIDATION from day 28 - a banked $1 beats a shelved $250, because
    unsold inventory scores zero.


The model that beat us (tetsuya, $125k) inverts the naive read of the price table.
The naive read looks at the GLUT side and concludes milk/wool/strawberry "crash to
$1", so you farm eggs. That is wrong, for two reasons:

  1. The town DRAINS inventory every turn and its demand roughly absorbs both
     players' premium output. Inventory therefore sits at or below I0 all game, and
     the premium goods have tiny anchor throughput T (milk 122, strawberry 100,
     wool 105) with steep scarcity curves -- so they sit ABOVE base, not below.
     Observed over a full episode: milk $160->$242, strawberry $120->$221,
     wool $200->$223. Meanwhile EGG has T=332 and barely moves: $50->$54.
     Eggs are safe and cheap; that is the worst combination.

  2. CARE banks +1 per fed-and-cared day and pays the whole bank on the next
     scheduled production. The bank therefore scales with the production INTERVAL:

        goose  interval 1 -> banks 1 -> 2 units/harvest @ $50  = ~$100/tile/day
        cow    interval 2 -> banks 2 -> 3 units/harvest @ $220 = ~$330/tile/day
        sheep  interval 3 -> banks 3 -> 4 units/harvest @ $223 = ~$297/tile/day

     A goose is the worst animal in the game on both axes at once.

FERTILIZER is the real trap: the town centre explicitly does NOT consume it, so
nothing absorbs it and both players dumping drove it $100 -> $3. Collect it early,
then spend it on strawberries rather than selling into the floor.
"""

# EVOLVE-BLOCK-START
P = dict(
    # 12 cows was the top replay's herd, but at OUR routing quality it overextends:
    # the objective-landscape sweep (analysis/) found (n_cow=8, melon=6) and a
    # 14-seed verification confirmed it -- mean $71k -> $100k, blowups 1/14 -> 0/14.
    # The smaller herd never hits the $0-cash death spiral.
    n_cow=8, n_sheep=4,
    melon_tiles=6,            # THE bootstrap: seed $80 -> 6 units @ $250 on day 10
    melon_plant_until=4,
    wheat_tiles=8,           # feed base; the rest of the shortfall is bought
    max_hands=13, hand_per_task=6, hire_hours=3, hire_per_turn=4,
    animal_buy_until=19,
    early_flock=3,            # before melon cash lands, land+seed beat livestock
    melon_cash_day=11,
    melon_seed_batch=10,
    straw_seed_batch=5,
    expand=True, land_day_min=8, land_day_max=16, land_buffer=1200,
    # 16 cows eat ~320 wheat over the season. Even at $70 that is ~$22k against
    # ~$108k of milk -- buy the feed, don't spend land and walking on growing it.
    wheat_buy_price=75,
    wheat_days_ahead=2.0, animal_margin=2, wheat_bank=34,
    money_floor=350,
    reserve_days=0.0,   # swept: a solvency buffer did not remove the tail and cost ~$11k mean
    fert_min_price=25,        # below this, fertilizer is worth more on a berry
    sell_batch=5,             # premium sells walk the curve; bleed them out slowly
    melon_batch=8,            # melon is a RACE: 158 units total absorbable, shared
    sell_floor={"MILK": 90, "WOOL": 110, "STRAWBERRY": 70, "MELON": 35,
                "EGG": 20, "CARROT": 12, "TOMATO": 20},
    drop_at=12,
    # ---- win-probability layer (v7, per discussion/736219) ----
    endgame_day=23,          # scoreboard modes switch on here
    lead_safe=9000,          # optimistic-lead threshold to DEFEND (their shed is hidden)
    lead_push=6000,          # deficit threshold to PUSH
    defend_extra=6,          # extra sell batch while defending
    exp_slack=2,             # opponent-exposure margin before we front-run
    liquidate_day=28,        # from here: sell everything at any price
)
LAND_COST = [1000, 2000, 4000]
APROD = {"GOOSE": "EGG", "COW": "MILK", "SHEEP": "WOOL"}
ACOST = {"GOOSE": 300, "COW": 400, "SHEEP": 500}
ASTRUCT = {"COW": "PASTURE", "SHEEP": "PASTURE", "GOOSE": "COOP"}
PREMIUM = ("MILK", "WOOL", "STRAWBERRY", "MELON")
S = {"day": -1, "tgt": {}}


def _quad(x, y, hh):
    return ("N" if y < hh else "S") + ("W" if x < hh else "E")


def _sd(px, py, tx, ty):
    if px < tx: return "EAST"
    if px > tx: return "WEST"
    if py < ty: return "SOUTH"
    return "NORTH"


def _tile_ops(t, kind, day, inv, px, days_left):
    """Pending (op, value) pairs for the tile a unit is standing on."""
    out = []
    if kind == "ANIMAL":
        prod = APROD.get(t.get("animal"), "EGG")
        val = px.get(prod, 1)
        yu = t.get("yield_units", 0)
        if yu > 0:
            out.append((["HARVEST"], yu * val))
        if not t.get("fed_today") and inv.get("WHEAT", 0) > 0:
            # Unfed twice and the animal is gone, taking $400-500 with it.
            out.append((["FEED"], min(days_left, 8) * val))
        # CARE is the highest-leverage action on a long-interval animal.
        if not t.get("cared_today") and t.get("fed_today") and days_left > 1:
            out.append((["CARE"], val))
        if t.get("fertilizer_available") and px.get("FERTILIZER", 0) >= P["fert_min_price"]:
            out.append((["COLLECT_FERTILIZER"], px["FERTILIZER"]))
    elif kind == "PLANT":
        crop = t["crop"]; val = px.get(crop, 1)
        age = day - t["planted_day"]
        yu = t.get("yield_units", 0)
        if yu > 0 and (crop != "WHEAT" or age >= 4):
            out.append((["HARVEST"], yu * val))
        if not t.get("watered_today"):
            urgent = t.get("consecutive_unwatered", 0) >= 1
            out.append((["WATER"], val * (6 if urgent else 2)))
        # Fertilizer doubles a berry's scheduled yield; that beats selling it.
        if (crop == "STRAWBERRY" and inv.get("FERTILIZER", 0) > 0
                and t.get("fertilized_until_day", -1) < day and days_left > 2):
            out.append((["FERTILIZE"], val))
    return out


def agent(obs, config=None):
    me = obs["player"]
    farm = obs["farms"][me]; priv = obs["private"]; tiles = farm["tiles"]
    n = len(tiles); hh = n // 2
    day, hour, money = obs["day"], obs["hour"], farm["money"]
    if obs.get("step", 0) == 0: S.update(day=-1, tgt={})
    if S["day"] != day:
        S["day"] = day; S["tgt"] = {}
    shed = dict(priv["shed"]); seeds = dict(priv["seeds"])
    px = {k: max(1, v) for k, v in obs["market"]["prices"].items()}
    unlocked = set(farm["unlocked_quadrants"])
    sheds = [(hh - 1, hh - 1), (hh, hh - 1), (hh - 1, hh), (hh, hh)]
    units = [tuple(farm["farmer"])] + [tuple(p) for p in farm["hands"]]
    invs = [dict(i) for i in priv["inventories"]]
    while len(invs) < len(units): invs.append({})
    days_left = max(1, 30 - day)

    # ---- scoreboard (all public info) ----
    opp = obs["farms"][1 - me]
    opp_exp = {"MILK": 0, "WOOL": 0, "STRAWBERRY": 0, "MELON": 0}
    for row in opp["tiles"]:
        for c in row:
            if isinstance(c, dict):
                if c.get("animal") == "COW": opp_exp["MILK"] += 1
                elif c.get("animal") == "SHEEP": opp_exp["WOOL"] += 1
                elif c.get("kind") == "PLANT" and c.get("crop") in ("STRAWBERRY", "MELON"):
                    opp_exp[c["crop"]] += 1
    my_exp = {"MILK": 0, "WOOL": 0, "STRAWBERRY": 0, "MELON": 0}
    for row in tiles:
        for c in row:
            if isinstance(c, dict):
                if c.get("animal") == "COW": my_exp["MILK"] += 1
                elif c.get("animal") == "SHEEP": my_exp["WOOL"] += 1
                elif c.get("kind") == "PLANT" and c.get("crop") in ("STRAWBERRY", "MELON"):
                    my_exp[c["crop"]] += 1
    inv_value = sum(px.get(k, 0) * v for k, v in shed.items() if k not in ACOST)
    lead = money + inv_value - opp["money"]  # optimistic: their shed is hidden
    endgame = day >= P["endgame_day"]
    defend = endgame and lead > P["lead_safe"]
    push = endgame and lead < -P["lead_push"]

    owned = [(x, y) for y in range(n) for x in range(n) if _quad(x, y, hh) in unlocked]
    owned.sort(key=lambda p: abs(p[0] - hh + .5) + abs(p[1] - hh + .5))
    n_an = P["n_cow"] + P["n_sheep"]
    pasture_role = set(owned[:n_an])
    rest = owned[n_an:]
    melon_role = set(rest[:P["melon_tiles"]])
    rest2 = rest[P["melon_tiles"]:]
    straw_role = set(rest2[:-P["wheat_tiles"]] if len(rest2) > P["wheat_tiles"] else [])
    wheat_role = set(c for c in rest2 if c not in straw_role)

    animals, empty_str, weeds, empties, plants = [], [], [], [], []
    for (x, y) in owned:
        t = tiles[y][x]
        if t is None: empties.append((x, y))
        elif t["kind"] in ("COOP", "PASTURE"):
            (animals if "animal" in t else empty_str).append((x, y))
        elif t["kind"] == "PLANT": plants.append((x, y))
        else: weeds.append((x, y))
    na = len(animals)
    ncow = sum(1 for (x, y) in animals if tiles[y][x].get("animal") == "COW")

    ops = [None] * len(units); claimed = set()
    an_shed = {a: shed.get(a, 0) for a in ACOST}
    wheat_shed = shed.get("WHEAT", 0)
    unfed = sum(1 for (x, y) in animals if not tiles[y][x].get("fed_today"))
    for ui in range(len(units)):
        t = S["tgt"].get(ui)
        if t: claimed.add(t)

    def want_seed(cell):
        # Melon only in the opening window -- it needs 10 days to first yield.
        if cell in melon_role and day <= P["melon_plant_until"]: return "MELON"
        if cell in wheat_role: return "WHEAT"
        if days_left > 13: return "STRAWBERRY"
        if days_left > 5: return "WHEAT"
        return None

    for ui, (ux, uy) in enumerate(units):
        inv = invs[ui]; carry = sum(inv.values()); at_shed = (ux, uy) in sheds
        held_an = sum(inv.get(a, 0) for a in ACOST)

        if at_shed:
            if carry - inv.get("WHEAT", 0) - held_an >= P["drop_at"]:
                ops[ui] = ["DROP"]; S["tgt"].pop(ui, None); continue
            if held_an == 0 and empty_str:
                for a in ("COW", "SHEEP", "GOOSE"):
                    if an_shed.get(a, 0) > 0:
                        an_shed[a] -= 1; ops[ui] = ["PICKUP", a, 1]; break
                if ops[ui]: continue
            if inv.get("WHEAT", 0) == 0 and unfed > 0 and wheat_shed > 0:
                k = min(wheat_shed, 8, unfed)
                wheat_shed -= k; ops[ui] = ["PICKUP", "WHEAT", k]; continue

        if held_an > 0 and empty_str:
            a = next(a for a in ACOST if inv.get(a, 0) > 0)
            free = [c for c in empty_str
                    if tiles[c[1]][c[0]]["kind"] == ASTRUCT[a] and c not in claimed]
            free = free or [c for c in empty_str if tiles[c[1]][c[0]]["kind"] == ASTRUCT[a]]
            if free:
                tgt = min(free, key=lambda c: abs(c[0] - ux) + abs(c[1] - uy))
                S["tgt"][ui] = tgt; claimed.add(tgt)
                ops[ui] = ["PLACE", a] if tgt == (ux, uy) else [_sd(ux, uy, *tgt)]
                continue

        if carry - inv.get("WHEAT", 0) >= P["drop_at"]:
            sp = min(sheds, key=lambda p: abs(p[0] - ux) + abs(p[1] - uy))
            ops[ui] = ["DROP"] if (ux, uy) == sp else [_sd(ux, uy, *sp)]
            S["tgt"].pop(ui, None); continue

        tgt = S["tgt"].get(ui)
        if tgt:
            tx, ty = tgt; t = tiles[ty][tx]; kind = None
            if isinstance(t, dict):
                kind = "ANIMAL" if "animal" in t else ("PLANT" if t["kind"] == "PLANT" else t["kind"])
            pend = _tile_ops(t, kind, day, inv, px, days_left) if kind in ("ANIMAL", "PLANT") else []
            if kind == "WEED": pend = [(["DIG"], 20)]
            if t is None:
                if tgt in pasture_role:
                    pend = [([("BUILD_PASTURE")], 400)]
                else:
                    sc = want_seed(tgt)
                    if sc and seeds.get(sc, 0) > 0 and hour < 21:
                        pend = [(["PLANT", sc], px.get(sc, 10) * 3)]
            if pend:
                ops[ui] = list(max(pend, key=lambda z: z[1])[0]) if (ux, uy) == tgt else [_sd(ux, uy, tx, ty)]
                continue
            S["tgt"].pop(ui, None); claimed.discard(tgt)

        best, bs = None, 0.0
        for (x, y) in animals + plants + weeds + empties:
            if (x, y) in claimed: continue
            t = tiles[y][x]
            if isinstance(t, dict) and "animal" in t:
                pend = _tile_ops(t, "ANIMAL", day, inv, px, days_left)
                if not pend: continue
                val = sum(v for _, v in pend)
            elif isinstance(t, dict) and t["kind"] == "PLANT":
                pend = _tile_ops(t, "PLANT", day, inv, px, days_left)
                if not pend: continue
                val = sum(v for _, v in pend)
            elif isinstance(t, dict):
                val = 20
            elif (x, y) in pasture_role:
                if not (any(an_shed.values()) or money > 500): continue
                val = 400
            else:
                sc = want_seed((x, y))
                if not sc or seeds.get(sc, 0) <= 0 or hour >= 21: continue
                val = px.get(sc, 10) * 3
            d = abs(x - ux) + abs(y - uy)
            sc2 = val / (d + 1.5)
            if sc2 > bs: best, bs = (x, y), sc2
        if best:
            S["tgt"][ui] = best; claimed.add(best)
            if best != (ux, uy):
                ops[ui] = [_sd(ux, uy, *best)]
            else:
                t = tiles[best[1]][best[0]]
                if t is None and best in pasture_role: ops[ui] = ["BUILD_PASTURE"]
                elif t is None:
                    sc = want_seed(best); ops[ui] = ["PLANT", sc] if sc else ["PASS"]
                else:
                    k = "ANIMAL" if "animal" in t else ("PLANT" if t["kind"] == "PLANT" else None)
                    pend = _tile_ops(t, k, day, inv, px, days_left) if k else []
                    ops[ui] = list(max(pend, key=lambda z: z[1])[0]) if pend else ["PASS"]
        else:
            sp = min(sheds, key=lambda p: abs(p[0] - ux) + abs(p[1] - uy))
            ops[ui] = (["DROP"] if carry else ["PASS"]) if (ux, uy) == sp else [_sd(ux, uy, *sp)]

    # ---------------- market ----------------
    mkt = []
    if hour <= P["hire_hours"]:
        work = na * 3 + len(plants) + len(empties)
        want = max(3, min(P["max_hands"], work // P["hand_per_task"]))
        if money < 300: want = min(want, 4)
        for _ in range(max(0, min(want - farm["hires_today"], P["hire_per_turn"]))):
            mkt.append(["HIRE"])

    # Premium goods move the price ~$2/unit sold, so bleed them out in small lots
    # and never sell into the floor -- town demand pulls the price back up.
    for item in PREMIUM + ("EGG", "CARROT", "TOMATO"):
        q = shed.get(item, 0)
        if q <= 0 or len(mkt) >= 10:
            continue
        floor = P["sell_floor"].get(item, 5)
        batch = P["melon_batch"] if item == "MELON" else P["sell_batch"]
        # Front-run: their standing exposure is future supply that will crash this price.
        if item in opp_exp and opp_exp[item] > my_exp.get(item, 0) + P["exp_slack"]:
            floor = int(floor * 0.6); batch += 3
        if day >= P["liquidate_day"]:
            floor, batch = 2, q
        elif defend:
            batch += P["defend_extra"]
        elif push and item in ("MILK", "WOOL", "STRAWBERRY") and day < P["liquidate_day"] - 1:
            continue  # hold for the seasonal peak; dump in the final days
        if px.get(item, 0) >= floor:
            mkt.append(["SELL", item, min(q, batch)])
    if shed.get("FERTILIZER", 0) > 0 and len(mkt) < 10:
        fq = shed["FERTILIZER"]
        if day >= P["liquidate_day"] and px.get("FERTILIZER", 0) >= 2:
            mkt.append(["SELL", "FERTILIZER", fq])
        elif px.get("FERTILIZER", 0) >= P["fert_min_price"]:
            mkt.append(["SELL", "FERTILIZER", min(fq, P["sell_batch"])])
    keep = max(P["wheat_bank"], int(na * P["wheat_days_ahead"]) + 4)
    if day >= P["liquidate_day"]:
        keep = na  # one last day of feed; the rest becomes cash
    if shed.get("WHEAT", 0) > keep and len(mkt) < 10:
        mkt.append(["SELL", "WHEAT", shed["WHEAT"] - keep])

    # ORDER MATTERS: orders are funded sequentially, so the opening melon crop --
    # the only thing that turns $960 of seed into ~$10k by day 12 -- is queued
    # ahead of livestock. Cows funded first would eat the entire opening bank.
    # Buy against UNPLANTED tiles minus seeds already held, or this re-buys a full
    # batch every turn and drains the opening bank into a seed pile.
    free_melon = sum(1 for c in melon_role if tiles[c[1]][c[0]] is None)
    need = min(free_melon - seeds.get("MELON", 0), P["melon_seed_batch"])
    if len(mkt) < 10 and day <= P["melon_plant_until"] and need > 0 and money > 300:
        mkt.append(["BUY_SEED", "MELON", need])
    if len(mkt) < 10 and days_left > 5 and money > 200 and seeds.get("WHEAT", 0) < 10:
        mkt.append(["BUY_SEED", "WHEAT", 10])

    # SOLVENCY RESERVE. Hitting $0 is unrecoverable, not merely slow: with no cash
    # the HIRE orders fail, the crew collapses to the lone farmer, and one unit
    # cannot water 30 berries or feed 9 cows -- so the whole farm starves in ~2 days.
    # Every discretionary purchase below must leave this much in the bank.
    burn = 50 * P["max_hands"] + na * px.get("WHEAT", 30)
    reserve = int(P["reserve_days"] * burn)

    bought = len(unlocked) - 1
    if (bought < 3 and P["expand"] and not defend
            and P["land_day_min"] <= day <= P["land_day_max"]
            and money > LAND_COST[bought] + P["land_buffer"] + reserve and len(mkt) < 10):
        mkt.append(["BUY_LAND"]); money -= LAND_COST[bought]

    tw = shed.get("WHEAT", 0) + sum(i.get("WHEAT", 0) for i in invs)
    want_wheat = max(P["wheat_bank"], int(na * P["wheat_days_ahead"]) + 4)
    if (tw < want_wheat and day < P["liquidate_day"] and px["WHEAT"] <= P["wheat_buy_price"]
            and money > P["money_floor"] and len(mkt) < 10):
        k = int(min(want_wheat - tw, (money - P["money_floor"]) // px["WHEAT"]))
        if k > 0: mkt.append(["BUY_PRODUCT", "WHEAT", k])

    # Livestock: cows first (interval 2, $220/unit), then sheep. Gated on feed.
    slots = len(empty_str) + sum(1 for t in empties if t in pasture_role)
    held = sum(shed.get(a, 0) + sum(i.get(a, 0) for i in invs) for a in ACOST)
    # One day of feed in hand is enough to justify the purchase; the buy order above
    # keeps the bank topped up. Demanding a fat buffer stalls the flock permanently.
    feed_ok = tw >= (na + held) + P["animal_margin"]
    # Animals must be bought EARLY -- a cow needs 8 days to first milk, so a cow
    # bought after ~day 20 never pays for itself.
    if day <= P["animal_buy_until"] and not defend and feed_ok and slots > held and len(mkt) < 10:
        cap = P["early_flock"] if day < P["melon_cash_day"] else P["n_cow"]
        buy = "COW" if ncow + held < cap else (
            "SHEEP" if na + held < n_an and day >= P["melon_cash_day"] else None)
        if buy and money > ACOST[buy] + reserve:
            k = min(int((money - reserve) // ACOST[buy]), slots - held, 4)
            if k > 0: mkt.append(["BUY_ANIMAL", buy, k])


    free_str = sum(1 for c in straw_role if tiles[c[1]][c[0]] is None)
    need_s = min(free_str - seeds.get("STRAWBERRY", 0), P["straw_seed_batch"])
    if len(mkt) < 10 and days_left > 13 and money > 900 + reserve and need_s > 0:
        mkt.append(["BUY_SEED", "STRAWBERRY", need_s])

    return {"farmer": ops[0] if ops else ["PASS"], "hands": ops[1:], "market": mkt[:10]}
# EVOLVE-BLOCK-END


!pip install -q -U kaggle-environments

from kaggle_environments import make

env = make("kaggriculture", configuration={"episodeSteps": 720}, debug=True)
env.run([agent, "starter"])

final = env.steps[-1]
for i, s in enumerate(final):
    print(f"Player {i}: reward={s['reward']:,.0f}  status={s['status']}")
