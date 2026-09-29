_QUEUE_ENGINE = {}

exec('# Market semantics from Kaggle/kaggle-environments, Apache-2.0, installed version 1.32.7.\n\nimport math\n\nCROPS = {\n    "WHEAT":      {"seed": 10, "first_yield_day": 2, "max_yield_day": 4, "interval": 0, "max_yield": 6, "ongoing": False},\n    "CARROT":     {"seed": 20, "first_yield_day": 2, "max_yield_day": 3, "interval": 0, "max_yield": 4, "ongoing": False},\n    "TOMATO":     {"seed": 50, "first_yield_day": 8, "max_yield_day": 8, "interval": 1, "max_yield": 4, "ongoing": True},\n    "STRAWBERRY": {"seed": 100, "first_yield_day": 10, "max_yield_day": 10, "interval": 2, "max_yield": 4, "ongoing": True},\n    "MELON":      {"seed": 80, "first_yield_day": 10, "max_yield_day": 12, "interval": 0, "max_yield": 6, "ongoing": False},\n}\n\nANIMALS = {\n    "GOOSE": {"cost": 300, "structure": "COOP",    "first_yield_day": 4, "interval": 1, "max_held": 4, "product": "EGG"},\n    "COW":   {"cost": 400, "structure": "PASTURE", "first_yield_day": 8, "interval": 2, "max_held": 6, "product": "MILK"},\n    "SHEEP": {"cost": 500, "structure": "PASTURE", "first_yield_day": 6, "interval": 3, "max_held": 6, "product": "WOOL"},\n}\n\nPRODUCTS = ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL", "FERTILIZER"]\n\nMARKET_I0 = 10000\n\nPRICE_FLOOR = 1\n\nMARKET_PARAMS = {\n    "WHEAT":      {"base":  25, "I0": MARKET_I0, "T": 400, "below_func": "sqrt",   "below_target": 0.80, "above_func": "log",    "above_target": 0.20},\n    "CARROT":     {"base":  35, "I0": MARKET_I0, "T": 450, "below_func": "hinge",  "below_target": 1.00, "above_func": "sqrt",   "above_target": 0.70},\n    "TOMATO":     {"base":  60, "I0": MARKET_I0, "T": 200, "below_func": "hinge",  "below_target": 0.40, "above_func": "sqrt",   "above_target": 0.60},\n    "STRAWBERRY": {"base": 120, "I0": MARKET_I0, "T": 100, "below_func": "sqrt",   "below_target": 0.70, "above_func": "linear", "above_target": 1.60},\n    "MELON":      {"base": 250, "I0": MARKET_I0, "T": 300, "below_func": "log",    "below_target": 0.20, "above_func": "sq",     "above_target": 3.60},\n    "EGG":        {"base":  50, "I0": MARKET_I0, "T": 332, "below_func": "hinge",  "below_target": 0.40, "above_func": "log",    "above_target": 0.20},\n    "MILK":       {"base": 160, "I0": MARKET_I0, "T": 122, "below_func": "sqrt",   "below_target": 0.60, "above_func": "linear", "above_target": 1.60},\n    "WOOL":       {"base": 200, "I0": MARKET_I0, "T": 105, "below_func": "log",    "below_target": 0.20, "above_func": "sq",     "above_target": 3.20},\n    "FERTILIZER": {"base": 100, "I0": MARKET_I0, "T": 200, "below_func": "linear", "below_target": 0.40, "above_func": "linear", "above_target": 0.40},\n}\n\nHINGE_GAIN = 8.0\n\ndef _shape(func, x, T=None):\n    x = max(0.0, x)\n    if func == "linear": return x\n    if func == "sq":     return x * x\n    if func == "sqrt":   return math.sqrt(x)\n    if func == "log":    return math.log(1.0 + x)\n    if func == "log10":  return math.log10(1.0 + x)\n    if func == "hinge":\n        # Degenerates to linear if T is missing or non-positive.\n        if not T or T <= 0:\n            return x\n        u = x / T\n        return u + HINGE_GAIN * max(0.0, u - 1.0) ** 2\n    return x\n\nLAND_ORDER = ["NE", "SW", "SE"]\n\nLAND_PRICES = [1000, 2000, 4000]\n\nFARM_HAND_COST_MULT = 1\n\ndef get(d, key, default):\n    if isinstance(d, dict):\n        return d.get(key, default)\n    return getattr(d, key, default)\n\ndef _quadrant_of(x, y, board_size):\n    half = board_size // 2\n    return ("N" if y < half else "S") + ("W" if x < half else "E")\n\ndef _shed_access_tiles(board_size):\n    """Four inner-corner tiles around the shed, in NWSE order."""\n    half = board_size // 2\n    return [(half - 1, half - 1), (half, half - 1), (half - 1, half), (half, half)]\n\ndef market_price(item, inventory, params=None):\n    """Floor at PRICE_FLOOR."""\n    p = (params or MARKET_PARAMS)[item]\n    base = p["base"]\n    I0 = p["I0"]\n    T = p["T"]\n    if inventory < I0:\n        f = p["below_func"]\n        amp = p["below_target"] * base / _shape(f, T, T)\n        price = base + amp * _shape(f, I0 - inventory, T)\n    else:\n        f = p["above_func"]\n        amp = p["above_target"] * base / _shape(f, T, T)\n        price = base - amp * _shape(f, inventory - I0, T)\n    return max(PRICE_FLOOR, int(round(price)))\n\ndef _refresh_prices(market):\n    params = market.get("params")\n    for item in PRODUCTS:\n        market["prices"][item] = market_price(item, market["inventory"][item], params)\n\ndef _spawn_hand(farm, board_size):\n    """First free shed-access tile (NWSE order); ties broken by min occupancy."""\n    occupants = {tile: 0 for tile in _shed_access_tiles(board_size)}\n    all_pos = [tuple(farm["farmer"])] + [tuple(p) for p in farm["hands"]]\n    for pos in all_pos:\n        if pos in occupants:\n            occupants[pos] += 1\n    best = sorted(occupants.items(), key=lambda kv: (kv[1], _shed_access_tiles(board_size).index(kv[0])))\n    return list(best[0][0])\n\ndef _process_market(state, env):\n    """Per-unit lockstep: at each step, quote both players\' current-unit prices, then commit both."""\n    obs0 = state[0].observation\n    market = obs0.market\n    farms = obs0.farms\n    privates = [s.observation.private for s in state]\n    board_size = int(get(env.configuration, "boardSize", 10))\n    max_orders = max(1, int(get(env.configuration, "maxMarketOrdersPerTurn", 10)))\n    hire_mult = int(get(env.configuration, "farmHandCostMult", FARM_HAND_COST_MULT))\n    shed_capacity = int(get(env.configuration, "shedCapacity", 100))\n\n    queues = []\n    for s in state:\n        action = s.action if isinstance(s.action, dict) else {}\n        m = action.get("market", []) if isinstance(action, dict) else []\n        q = list(m) if isinstance(m, list) else []\n        queues.append(q[:max_orders])\n\n    max_len = max((len(q) for q in queues), default=0)\n    for i in range(max_len):\n        order_states = []\n        for player_id, q in enumerate(queues):\n            ostate = None\n            if i < len(q):\n                ostate = _parse_order(q[i])\n            order_states.append(ostate)\n\n        # Atomic orders (HIRE, BUY_LAND): handle once, in player order.\n        for player_id, ostate in enumerate(order_states):\n            if ostate is None:\n                continue\n            op = ostate["type"]\n            if op == "HIRE":\n                _do_hire(farms[player_id], privates[player_id], board_size, hire_mult)\n                order_states[player_id] = None\n            elif op == "BUY_LAND":\n                _do_buy_land(farms[player_id], board_size)\n                order_states[player_id] = None\n\n        # Per-unit lockstep loop for SELL / BUY_*.\n        idx_esc = 0\n        while True:\n            idx_esc += 1\n            if idx_esc >= 100_000:\n                print("WARNING: kaggriculture market loop exceeded 100k iterations; aborting")\n                break\n            quoted = [None, None]\n            for player_id, ostate in enumerate(order_states):\n                if ostate is None or ostate["remaining"] <= 0:\n                    continue\n                op = ostate["type"]\n                item = ostate["item"]\n                if op == "SELL" and item in PRODUCTS:\n                    quoted[player_id] = ("SELL", item, market_price(item, market["inventory"][item], market.get("params")), ostate)\n                elif op == "BUY_PRODUCT" and item in ("WHEAT", "FERTILIZER"):\n                    # Quote at post-buy inventory so a buy/sell round-trip\n                    # against an unchanged market nets zero.\n                    quoted[player_id] = ("BUY_PRODUCT", item, market_price(item, market["inventory"][item] - 1, market.get("params")), ostate)\n                elif op == "BUY_SEED" and item in CROPS:\n                    quoted[player_id] = ("BUY_SEED", item, CROPS[item]["seed"], ostate)\n                elif op == "BUY_ANIMAL" and item in ANIMALS:\n                    quoted[player_id] = ("BUY_ANIMAL", item, ANIMALS[item]["cost"], ostate)\n                else:\n                    order_states[player_id] = None  # malformed sub-op; abort\n\n            if all(q is None for q in quoted):\n                break\n\n            # Both players see the same pre-commit inventory for this unit.\n            committed_any = False\n            for player_id, q in enumerate(quoted):\n                if q is None:\n                    continue\n                op, item, price, ostate = q\n                ok = _commit_unit(op, item, price, farms[player_id], privates[player_id], market, shed_capacity)\n                if ok:\n                    ostate["remaining"] -= 1\n                    committed_any = True\n                else:\n                    order_states[player_id] = None  # can\'t continue this order\n\n            if not committed_any:\n                break\n\n        _refresh_prices(market)\n\ndef _parse_order(order):\n    if not isinstance(order, list) or not order:\n        return None\n    op = order[0]\n    if op == "HIRE":\n        return {"type": "HIRE"}\n    if op == "BUY_LAND":\n        return {"type": "BUY_LAND"}\n    if op in ("BUY_SEED", "BUY_PRODUCT", "BUY_ANIMAL", "SELL"):\n        if len(order) < 3:\n            return None\n        try:\n            n = int(order[2])\n        except (TypeError, ValueError):\n            return None\n        if n <= 0:\n            return None\n        return {"type": op, "item": order[1], "remaining": n}\n    return None\n\ndef _commit_unit(op, item, price, farm, private, market, shed_capacity=100):\n    if op == "SELL":\n        if private["shed"].get(item, 0) <= 0:\n            return False\n        private["shed"][item] -= 1\n        farm["money"] += price\n        # Sales at $1 do not increase market supply.\n        if price > 1:\n            market["inventory"][item] += 1\n        return True\n    if op == "BUY_PRODUCT":\n        if farm["money"] < price:\n            return False\n        # Bought goods land in the shed, which obeys shedCapacity like every\n        # other deposit path (pickup, shed-drop, end-of-day drop).\n        if sum(private["shed"].values()) >= shed_capacity:\n            return False\n        farm["money"] -= price\n        private["shed"][item] = private["shed"].get(item, 0) + 1\n        market["inventory"][item] -= 1\n        return True\n    if op == "BUY_SEED":\n        if farm["money"] < price:\n            return False\n        farm["money"] -= price\n        private["seeds"][item] = private["seeds"].get(item, 0) + 1\n        return True\n    if op == "BUY_ANIMAL":\n        if farm["money"] < price:\n            return False\n        if sum(private["shed"].values()) >= shed_capacity:\n            return False\n        farm["money"] -= price\n        private["shed"][item] = private["shed"].get(item, 0) + 1\n        return True\n    return False\n\ndef _fib(n):\n    """Indexed so _fib(0)=1, _fib(1)=1, _fib(2)=2, _fib(3)=3, _fib(4)=5..."""\n    a, b = 1, 1\n    for _ in range(n):\n        a, b = b, a + b\n    return a\n\ndef _hire_cost(n_already_today, mult=FARM_HAND_COST_MULT):\n    return mult * _fib(n_already_today)\n\ndef _do_hire(farm, private, board_size, mult=FARM_HAND_COST_MULT):\n    cost = _hire_cost(farm["hires_today"], mult)\n    if farm["money"] < cost:\n        return\n    farm["money"] -= cost\n    farm["hires_today"] += 1\n    farm["hands"].append(_spawn_hand(farm, board_size))\n    private["inventories"].append({})\n\ndef _do_buy_land(farm, board_size):\n    n_unlocked_extra = len(farm["unlocked_quadrants"]) - 1  # NW is always there\n    if n_unlocked_extra >= len(LAND_ORDER):\n        return\n    cost = LAND_PRICES[n_unlocked_extra]\n    if farm["money"] < cost:\n        return\n    farm["money"] -= cost\n    quadrant = LAND_ORDER[n_unlocked_extra]\n    farm["unlocked_quadrants"].append(quadrant)\n    for y in range(board_size):\n        for x in range(board_size):\n            if _quadrant_of(x, y, board_size) == quadrant and farm["tiles"][y][x] == "LOCKED":\n                farm["tiles"][y][x] = None\n', _QUEUE_ENGINE)

_PLANT_CORE = {}

exec(zlib.decompress(base64.b85decode('c-q}PYjfK;lHaFl{sUIIsUZ_dk(6Y1%862?ag@Y0ww05W&F!jm99pDooh4EsDcic7|NC_}9t22Gk0i7AaP3Yc5@<9UjeemUs?};A)=9{I_ph#!`E<R=@LRk2tke7}%Mw3I=h-}t(wA%=!6$z)|IaXJq?w<EY@LQIjux9{tycT-hxu|9CmCD%*|qut{eyV<;}1Xna6BA*xL{rO<;Ncw{MA0a@ApQvBSwE;YH1h-@U7jdv)XK)q?xywhl{`q{0%(rz|*CFZ#;Vr&*o7UCb#|qzP9ux@ckF~9!FR4Ji3B!Z~a9YKGen7$GzcjAO}}tclICq+4ixYZy9?uIO~lD#j#)5$Ntqa_OIsH?X6>vl65}x#c0_3^jm*8{5!nSNNyjy-Lec$54F)d`;UIsKOLNx7W~&k2Jd{;l0P8(_0CVudZ#)Az8efK`b3CnoMyPFM2Iv?)>GUA@T7J;7<{PJsd*X4=k|rT&MC1<;sAglr2e~iwVeM3pNJ4@=;!63KlCm}ABX)~C0|%p;X0>-HuTxa>F@d27w`N15BjuU960tb=Gf1+j{RvcIIXEg_%Iy2`FK3SRTv8aP*=OLuJ%UVVAZ;0ojRvtUCgL1pu@j!`@_-6>B&F(!`cMLIqMC7?~lBb77PUJ-D>f{PmcTE+ta~dh>x{)A9};y*%sM!>8D5*)_DPAowVSi8UT@2>vtJ0;yZ7)j;1*E^mCFC?}+D_pIn7Vlvb0N-oK1*L)Cf_UkOIz&$ZT_R+ZqAh&`)D>_r)|YuFzl4pv00-E5T+%coI7?60jVsU{KorB#Jkr*!~gt>*KC5c{Q7CG!Mg?M@|P?ZcMxua>2pN1>n8>LtY5I${NJC=lzss6_0U1+koKN{DrA6yuFch&|I0!#yU@(wA}zV$V9?xRm=bKkfRXB4X`o9&2|xhb-kUU%QkfhDwNW4zJ*`7k}PTY82DtqR#xSgLY+3gT0orielJWDT4PW=kNO7yWYt;NZntXB%gzD#=P{}Uxf|=tF!w$8+Fg)D0GkbeD0w!s2Zo$gmLd({%}5H*qn8{YVaeLgrLeIc3*A+gySnEo3O|BW=Td3MKd&NoA}VNjvHTbsCsL7=zv6JPgq5lHm*RiOS`qD6W>*W8u<5!y$P?vC``Z_Pgxc-P66yRV)K+O=V=OkSe&pZjvA{NjrrTKnL~h<QJg_*Xfk52x~!#v*Xfi$UBfcmv!`s7KN5}BfVZ}^kMq@9vj(acmpy*WI=o*FSgd^#rttz;X6Yw4Vdky;#9yWkFj11sgD{m`0KUdq2u#IRVbZ`p>tqUUh-?N93DCjR>;T>e$0lV?3Q*I~<qiwSf(8vx`_Hp*dBlSGG;>xin*l}eNu900^)Vqf@kQ#m4{D8&hzf_J5@qBt{DlVE&!*Q1UiForkBl|KhuBP^3w{+W@H_%XESiQ6!KoAOZfOB|modVaG}o&Dn1y$6jg`o8{PBmkz2RAZ=$#Gz*4GWA^TBZR9=O(lC2h1_rDO*m)#LnWAFN2^a0e{omU{ZBFP=8!W0DA`z4JHTVECp#B;)X$jL(Zt^xr<W>Zl1>ab!TEVOK|q1^)&6t2L2$d+)K~@!(?QoqaqVNn`Kgz3G7d*89CrR)PE*OY@SOe-nxEhm(K&qvv6F(Ri#3(A;1x^!aW0@%;F`ckw}5YX#t@iL1K(y*E7fE=Gf4UkyddMKwSZ_ITLuok@JgMN?Ut#)UZm>mK*s_SJO9(w0<BF3tvn(fgCWnyD4EYR)<2!sGjbFxl6lpU6cY4L+TF$NlpWu$t~0tZ0YOwo{K`6Rg-@x;A6~-w0*z<osgPJLlZ-tCT9Be4L=pZo*AniUGMna9ia&C@Ak9u`hxq0x=*M`v%_nS(cQBQG)IB+7BQQl6mpW0i^~_E@M9lyc9wya=dGQF$28w7wqZNf~0h6=QTun!(Q>`Avm}|*qRGs*QtG?m-pt&e$CZ%YZ!R`bQ-3qm(3Sp>Xgv{x%d_YDo`GjN@E%)@DHQL%unJq2%YRYWC*E_t8@P8q7RxQ2$Ni*?lF_GLya2fGs{nIozc_slf0eT#+|6C%~LVE;6MCn7=iqbQyZ1V_}O~32(gWellVf5!Uewg2v4_@>p=}2g<vZA$x?e;XTVcQ28!2Pg88y3jQ%C(uo}IG%`;oXe&!Uq)pbQrD2z9g@%;p-i)ImX!sRO4uywSEr#E5Xvj1YW)4}oY{WmrEh}_JSTd$2tkZ{AAdSdK}03Xe^%&0`4ds0F^m?1hfCMG0oxUn|O+fB5|)sTK6+HH$@nmL}>KprUTyGZY@Q>1ncDv+jOfRe;en~s{)&Og<RX4iAjc3u|qkVZ?q%2#zeDa`exwV3bP=VZVE8e(ILby5RX&RN@-7>Z%DB;*^g!FiJyqt18YDhX#{5`s9(w<9hFHrdV7ro~~*2HTEXlR7~fw<p$_*$qeRVT!R9>V0GXtdjXH8YNpc3Sy2<47br*%7ij>#1qayBG%_V=qrx#M&yMr(<EL=2>2NxP;mOe*l+Xb76eJ0%wgBHCggcQL(Zu$88IL8SF11z!r*BVE@QOHLLaO-;3>_(u4#af6~8=8O5BDt;8w50tzN_J;g0|V@d5BQj8UP@qTAet<t@3zH%3=)VkMX`UxEC<5mmj(YuwtOqmKR6WN}x)X9@-)aQMnU<QB7-4R|SNI~z07IElj^*LdsNM3KSZ6yD09XBNXgDl$|q9@6W0#ifT@2I+Soo(?z9)pY92vM{(O7ctPq&zKfn%=g|3uyra{&E@pv4Uxt;Gf8d!l;W2wzJC14h(8#~?`XnE6hZNy=+4_r0L-0vO-%dCmHt|I=@W3-2$iSG69*q0{-+6UA`j|!Z1;o!J=R(S&JCSxvMWlxGICn%z=oU=LO2+?MhUr`Rt<(RkC9v8qI*YMM{J)tWc4@%*mYgaSp`9yUUP0q9nL$Y9m^k+{U|xuHC;e`JK5Nt@16-~76s8@QrR}&d!o5y+JdlMfKYc(^3_pPflP<Fryh9I7~q#vn4(8aVsVU3CzXQvW*!A}W&rLPnEcus><4dXB<(ScAIj4N#6Wv_2WlXJmr^s+A&vnQjv~Y98lxEAIugzK=?e&Lf{g(W=*_0Ea^Um(DN_wKK>SE!4SF8MKnu6hG#IP%qY2m3ZGCJ!=2*;UA?WDHOS2GX2X1UdR|j!;LT}82tO-1ALnNd?c*7tH!49O8R=^NG31T(cR@LE0^QFIV_&>C$aut18M4=7G{PoU-^vBv+kYO`%0N8{NWUlG7YDo)(u3pR;Eo952!!}m%w{nW2VdD9>{(RwIE<#&7RN-iIBRKCej@GHwBIKIi;~}&-a_~Dyh~Qq+2JnrwOj7{@B2VDSHN|VdR=Cf#0}5~G&^2RjVr8)RSQ^IWqVZSU{DqwkAizPINO15OG{GX|7^-$IXG&CGxkCtoq;gsyJmOS$mCLA_IKnK+`oeB@nQzD2=w=dINi;`Th(&^*<hB(-L2F`+)b}LyAJce~m+UHu??B?psX)V(4;|2*1qR4h<?b4dWu%`Nb8J{}Ku8FZ0)!(&>sT5#xpnA#c`&t%y*1K9^Jk-5@MQysOeikpqi$QRMs%z60emL)!W*?P6c8C;GXEy5f-@_3f5oCQGt!<Zj@{_uNI4vdlF1`MxX51`bim{Qg(=W#u^}M=?uo{T`nuN{f2BJgHWgMU_Xzg$%Ad}&O&0=%8q0i0Vse|%Y2!@t6j|iwR6uVsU@FLR3Bb;nFBajIzYuRQ1Ol!Xut$`E&DsD1(%8&s#%cj2i7fJ^%OmiafK;L|{~n{+!&{77f>^LE;NceOliSlV8PmAKE8x$7gtHBrR&h$+9RAy$=>EfwormishU1Qt9w*jU9YzXpB>nwZnGyIGL6ZoZ%<h3_1CAPe*p$vDoEC1m2qRlsPzePpf3Y!MxK=k*_w3HVs9fS2(n$e##6^q?=;trMAPxi2a$IOn{fLoM4$a{icOP_cWnUb-U1CGDM3!>2yLi0_Fd##!fFuvF6WD<vg#Md4#1TrMc!j4r#C8tZR(1BN2Z7Q$3$tm{1wg=^oDC5(eHt3DT{7O`%iy|Yj?q^dJ$y(Cxu_jgwWAP2SIBrCVVaC*5U!eWvBqb10kqO*CXO7~Wr%bjVJs$cwT1<4ve9+8p)@mmMPp#T8Q63ZqK~mQQs7L^k2M-9N(qEc!^Mm*?47@XeSa6hV`$=2FcYIG@eJEbh%=0T78f<;Aw7W|NSK&oh~q-vC8InUvBpafxjIBbWE~|K9Y8AtVmR><8pLU6ELcwKH$x1;mv%xq&gt+y?bZ+20fbIB*FzLq(ROBjIu+p-C+&=SLL5vL!6R<AgTo5xum6Gl2iE#JEZ`dhb;L<;L6(EXkgk^wK5K%IUWbT}Yj#J4hu!Cq1JW0Pxg~_D&1);l2wQ1a8mORNv9H;!VwRN~>E!tLkAL3s0x+~*xE?`;-r3aw-B6`?+PaJ;10xf##vL$z3eaD7*)!oOnbWC0O4cRa1qS7S!)_@&nR6t?>L#>BQRkwcuwDY!1`xKLW*`7AH;jbhOCv;%!XiR(ind*fyE|TAT?;j@dH)y^6#_z&mC8#fZw`Y8O!^2uQ=Q$z=};J~WM7dWx0!_dNbS?!algQ8--|sSu^xGXjNCs|a!0u|CT+RIQ)c|Oj^gQby_$zXek9RkJt0qv=Nu@mX@Rl?JIi2sT`aCoXB#AhvukL22`UxhuAr%L7txpnwn(_WK*RucSS)hp$l_dCz@hjxqllQ9A>kARh=|(=&)R%hIGE=a0i7(C+u=(d93tnNBI(jy7tvSE7ccjhE;%<n^;kRpSp>D!BWSx8F=$ofXdr3<2i_gS4LkQaQa7N$J7k4l$5(L#ivW6D2s(WgUb6Ty1VxRXkA>Vfm*eZ?<W~x_T`I0P*@9dsI#}+vL7uLY1nJc!Jy?`dN+lkmPz6Z0atd}8dJx(+uTjr#sq!B8up{ikbGroRPO@EeK4N{4F`JCU7Rds(TxUGLO4^|K0ew|2?a-GbVFVA7@bemv7NLosNr1dh4A8jsnVWmuYVIltceIy4hdArE2y{C1vI=wzWa3L9PAL4l+uD#48+#SJ&x#&JMNf;vBhoGRFpbFp@EA2RSGyQ*st{p2qTsvNft)dm5$D*2f2F(^3+nDi=W!uIKH1UD+6QRBgD*Nqz_c@8#r%0cir`Nsr8%nhTF|?Ih<_C#Au)J?aqxz~L=XNKHu4>i1dgJ(p9SY;+91~Wd7f3GVP^mVMp9_N=W2i!i9>;4K%<jW-Wrsjpw_?{+Vn=g0(ua9B1EeVpPD>lFZ6iA5!!<<-}i=pqZGT+s@WNHKfdE!tK+oqRy6>W*uKztZ$=c5D_IM~phn(e5sPiXAF%;vW$KuUI0G21%k=_l-L$zge+K)B6`<B_FhMJj+mCR`485C!iK)YSjb~3_GEYgx`0R3h)ht62l6l9b)5IePH~Tx1j3B*+=a8s-#00ybxjtWl>5RpH0zCUdg#8%@{(17iYTE!hg8Z~3qNBDV(7&#X7it3kfk#_m76{B!H#iA?F1#c7TY>2`7x-z9puhVPOe2cla4+MU;`bFW-TmwyK3vzfr3*m|tCVP&jZ7a<-x+m2lEq5fPg-wNm;A^`whG|@H1|7%&vEq6o3(V0cvpePWHMGoXBJviiAt48`cGBkJkn$MVR}xh#UCsCQ@tsknNp<g58(bk>h#Z(w*1ifgE`L_DZY6$U93}R?KX>ML4`u&o<crJYcrnz&G;F2XAfe(IeAwgv$Pxcuo)k*A!S&l{DdEJJMYl&gIG9aKu+U$^%RfuD5~%#hIZ$J5#w1|AXEAAv^cjmeaS7$yo1Y&IPSN9s>t)($CFb`S}(<Y545hUu=t`9HE4{7eKC@ypnoz_a+rsGcCG0s?Xh8tE4jC^J=@#RuGrWzC4T3gE{#_*(yQokJUBh=ACEk}*z3=x4uUMm5IxIcvgc%NUGdN`KW;87fTFD2gFwAu|DVM$dQQrIR4{sMS#+MUfd`Quo=b{Dyh9U(nUkmNgTa$w;>2YV--Ho{)R$O@gmGFR$|gVC7LQ1$lj$VWXZOo17JC{3ejY!~9`pQrGkwHGCr7*y)mL=FY-Ej0^5i)>?v5l>b9u!(g?C{g)blYkgke?G;4(}pv<5NCFmO~edGbZ|9o>b$ybOGHa|_8|H@B1wy?y>o%KO2#t%*9V5=jtrxQ4^RJAAEHdd1TeWLhxYw*l%dy46z|phSbhP<Ymi`DjO&iAp)h_^r-9uVe6BE@N;xKm~5XB>h<$;k+YHFRWugD*`RLT*5PKuC4uLiWyBbJ|NhH?^yYdp`$|bFScyTL|iHLQ~83vsC467a&~|dQXODZyrK1_6{KNhj%<GR&jYz=oB%<Za5^-bU#<C>GM1@g!wYDK@<Byh(ZwdVPlbWgu5X0`P0naC1L_2{9>IbMkOC%F5qRJqW;-y#$-f5<K870?&Y(F!u@tIFsAhn6J7hgbPPnyPm89``9j-Z*wQZA=RofIi6o|{*6dz5?NIsS#l42cSG+mt^5OI@{vjHG9=23P_T8sv1thoiBWj@%l*l{USY07<QqB7s=^Y|!V>xrTUC2xk2SbPUVrk}Z(`HUptFkDr=)otmCx_L2+0HZ4e8p%sD$<u|SbiVVvIaEy1NMQs=nOLyvh%t-OiQlbLG#sV9Dw6v?+YW71SC7hEISqgy^GU%o)KQjn<DC_~grkwg%lVXvjpMvO8TRY!w~v4Kuo%-lq7)fQ%9w^!5XL7fO2R7XAn-JZp`&CuxsqM1?m~4g0Y$obUob#7tI{!=7C1XG%>-qB1hI!3o%9u`3^|R7%1$#M>d9$JKv?1h`h+zA)`cgpTiNBD`c=4It~cI7S_oCBeFZ)`Ta+{pe296~=0*SX6jJ99%g4H_72JDaIyK#Uo@<E~PjSIT>nB~yQJj4Fnl5+op!C;52_6E=<6Jk!^;SY@5z^uP6nsf=4*}Q>9*K(Nq?ZiJ52zfkW}((4g!OLB$E0mBvu2D0s}tEQm2uy&53G9uvl%3ZgU1WWuRIC8;&`rluk5v7w2T1R48K~NDV9Z^sPU8W>XL^tDNQbPI2d_qeOMuctq{YN3t(B^;)WCWnv-zyif7F!aVzHZi2W;>V_>3z*_kz9pK2*75Gcmj@8&6_t1TE6oirf(VO0gozw%Kt0zMG#g0wQwO@U<VC<Id-+^V>F2zB*oehra%neMj|`U1UsgUYs3$lWs`IC2{NC_!da;KgH;15n~2M-wR#hCCQ80ZSrQNcNx`xwfO0h81IO7vIP-;Lw8n!8EFLeF<r!Lcr;gU2I!$s+`YCzGyZQPRqvMLK>Pc9<kpv&w~Nod5(v_46#zRA^eSe50FcV2|cJ<3cSl3<7t9VS;K`G!9K=T74k6Q&sz+OT>?|CC2f*=Zi9WcG`>OGj8BCE-cG6eo<;`WW`$%9*Dix^syN1?G#Xvo8K!Lk%s9n&VNgim`Z-gy=Bz-yEG$X~8#+q+aAif+UhZ^jRx=Ng993oa)9XTVKRqi~Pvqtt*RI$~<@Z<HpQ>h+)bNpL@K6rZmd(LZSJmjDkiTyT%Yq6p1s2!7ZaMLU6AIjtXZ8Yc)0)kaO+{W7r%Ok7RnRnBL8NX3)95Ej3<UohrZ~}Occ0<5r(jxR^EugYb8_qENURzLd$j#>#G;4NRRD^ccJ6bnyv4eo^~#lkF?CdtPh-h-s-As8hE}GbmU3$NtrZkGqv;r_em-3mlCghjvmh3!L{r#_sWQ9MHCFpHi&L0lN_M+|YPGpx`UXZ(QF(_*t~Tjr&gK<IVlP^uZiDR6j9tYsW-#;eKJ9W8aBUzASI%Svi2<qSc)+~Tp~aY_3b6;OVc>bF&T2lrS+6)xGy=+00zbVG&l-5@h7VkmhFent(OojQYp;2l6l#>#`zy2W+T}`Ti#>VB0$-F*g}#1u_n);$KPyjLOKh{xd&hi)-2GlN`oGE@B`TSS$a2y7r4t!tp%8FKJ2&R<T5cCy6Z+WBKX%-1M|^zdcAtrl&)x2eW-||f`w%w4E5zy&Ei^N|JRoR<0!8CXs0YB5Edym=p-WLAwDq0H^A{i*gAG3b0zH7CM_X*zyvTxL&X2{!O&GZ~qsOf@RinqJb`6I}qRE<LERJKe>vJX?jCNgNflIMpRYhWvfv~Oq${0u!`NpY`j9_j(9&?Suhi$dGIr)rGn(eSH^3;VQ;XPFLVend2UR$mrf@nC_XM?~$|D@HVQH4ToX%>OL=1}u1^4tn?isjNS${QDfO}_Io$+^j43BRgQtLdVG_u`Qje7D~ubz}yY?{_t_-D+gLqe)E&Rl1qDATHmsrfb_%9rWwE6l3AdG@dAF!b6=p6Q_F^NR>E$!?_#6m(TID;EmZ8JS?3d$s;F75tEmCm(RzbFW9{Z>jD~HK!oZ<UH}evFRJ4(EXAPO;oWeKsc8XH=eg_ZCB_t3{;7zZY0f@k=9NA$<c41bpkfX99LjL1zSNKCtO70qrN&rX2CIE%q#99*W)iBRCO9XjGgayP$#S%mE_9$9prXvMXX&5~v5s(jv<qR%JSJASfQU}Wj*1lxl*xu?NpxrBSb-`8SyAlHSBp7Vjv`T+Ut7St6F0Z5dCB_aGqSmbm$#Z``QYUhD=|Xh-Uw}Y+ZB*|y8sPwwdX#*eGpFl4Nv<|g*?~yn{m3F%W$!g{}gd#Etw{XVU2cFq^pQD3?m=$FID-~)v>JQBG1??-*Z#O2;0AcG!W!;T=ZA?Wbe_irjEKbu$v1k(?O(Ldjqg#jy7zEMYe_&CnI*zo#&{1LKh>y5GH_>rA^LtI%A0(3$OZmrM=iK0^Lc8&s`m2ZXo|ZX2&}}^+eT*V#`7mOS$$V?{idDhhe`y%93?l5y;#QrF>jjRexg%U*|bw70|&9?0f^;?nij--mmSY7ZiXEwx^WahrqOC;6UIUkKdZm%{kp(%+a8cN>v=Tau5^ps{=%eX13sH>L*V280M$E^FdNf=w2|xJi4rm7fYG2q0C7Ee_|1EB^a;GE5{C4m`CibO34%jP`nCeg?b*pFu5lwwcLSg_8>VVq9T66)-9ac<f-E@HGNN;Y4p_@=E(G#?Axb&fJ&=^y=tl)GMY3bxv^v^(k-u4cMmdGs#81<R6K9H4X#4V@U&E^X1+n6{O{2t-;##A)xg-5!CfWJXWy(4W);eyLc-6sNq2R}0%W|vEtZg#qHY9W{2(H29;_28i)ggl2KLq%`W=G>fL|r|r<&OJze?%@DO<!p7D4UnlD(?jTwKT6wk^jo`iz=zRCklmg%>ltMMBAn!d1Y<+ENmLt9a$u?jWRCsEv)ekZK)LX(}pAueTSN@(W#yb*3hC3!;|2Vo!%xLVv$qSus?uHL8gA#BPLDmK&5$vTel}7K_cEz;A}8c}S9~l}b@WUd7~L_6{BiCef7?aNj-dWfKT8zXO*A#%}W8YIN`@SHtT&I7$h{Z&bJyXhjM0`PFhNfgum!zrlM5=$MRt=cROo&pgsEZdtGJeuY0IoIhUD@2Sl2@&=e?FbCNQ=eP3W1%B%g?qdi|VlW1BQ!rO43m2Qpdx(M<lM{@4h14BF>abwj)mjwwfJ^q~RaZbB{qMPg%e-dfmhic$GeVwbED_mu(a6p_M*hcd>JkhJas<M`s9m%=3&XtH8I9c<UA0y&@K~t5R>3d@E5oSR2oiDMkgeRw!?4=sMLUdsSt9R-Z!b_N9a9SwneelJFN(znB~0y=1_uX^KT`Zt3;I6OV!n_)kkJKP!}E7oYlB*KHY2jmqggC-_wbrXf5U6*F_8%G5#&l&{<0Oe6YGH;xxS#z`2}7e@}LP9dd(r1eGYYe%-Wb$4F7-TvVUjtP|cEKhGMCZzN?B|-0}^viiPs@CtLlCmaw!X$h7s=lAV5oensSADoP(@r(~Dx<nFpPc*~D|RNNq3EVZzl7aE3%UFaed_(=x2zEv)g{Y(YruI%ty*qrLY&V!3Lc<@j<Z8$0%Tudp$7dH*I3SkDpV#Dtk#Zw6#;51%sstzY0aSA33!dO)8;_a0fVxjxC(2k|cjpEE-m_LG{jy%xmg}zffs0*5<EHEU>xOlpOmnF0E?=ux0Mr&7jB8ZmB^g6}_WKow#ha%ct{6t|$D24x8>f~T&dT<L2uU<q<_1xO6a@|P%yY^H1ktggSD!L%ES!MpIU4LZMt;!$F*6}JOH_$t6IFwp}?G|6N<yMvRZ5rfYg;iCuwoP@2o_Gq-rJv~%q@@T+E~YvD)C@vlr67s2mg>B;EtkZ6oxf+5o47|;!O<(;ggk@uJbqE`UUhGxX+8ppHcwtRZH~aj-dB{=l>_$1Fd~Vyuqlg}j3?H@FbeB4x-Xl!?}%(R6eHplUWf+ettl;%&#xDw#NOfs54;RVyM#04H$0$@VLhlRvcSVj)(E5~kF-0)32$T3<bCk6fkq|Lt)PXLC|SGax)bX2$belo!Sxl9nZXE*ZfB!NW{2NsO1~$x?My_+W$Z)NDJ4y54~ZjuN=Gd^yhJu)a*Jh=8$!rQknMtaOVMWS0UHv3e8sXGF1fr$TG6V?-%}Dki-E3i7r3MHn&W6(`u3o67rzmn-@^@*`)-sL&+xYrB8h(G1%{U0Sxn|qg1&rveXbCo__EF_NDJal&C}phw_bgfks+V=xc}ZY8Ts0yi@$LjNJ(ahO=Eu)Y5&zTrBRVlw@-|ZAt<7u=++OOv&agluA>(XwrAty3Pzgxc2!@MU7(aYKklYb|4&8jY#N5!+)=|!6{=GL&MlfI*O_^vvf@-tukp5Xz3or7riCJCuq1M`O6L)7NX<>Jrs^Jm$_~}3O_g2j_IYJ<P9RCE9gPKv6uEM5^$(=jAN*oBab+>sp||sRo$_TNvl)LcZU&Wb;a!}d5f8tr8HmPM2dJ5^>cV&`A@X?+6E2PT=@{1N;5i!@_iqO0eT+C`gV`J|(-m;(e&ul0G&6GW5N&qV3|I3s4#Ep~ltNIZQwTU&uLdBhH1R2gtZO)Mt@t_#?_hJPV1p(S3gUp=-ib;jRQz1DZ}s0`ESS$S5!RoBKFX^>oLUbBnd}iTZCqR%aWQLvwY>ig*n)*V')).decode(), _PLANT_CORE)

_QUEUE_ANIMALS = _QUEUE_ENGINE['ANIMALS']

class _QueueBox:
    def __init__(self, **values):
        self.__dict__.update(values)

def _queue_stock(obs, action, cfg):
    farm, private = obs["farms"][int(obs["player"])], obs["private"]
    stock = dict(private["shed"])
    half, cap = int(cfg.get("boardSize", 10)) // 2, int(cfg.get("shedCapacity", 100))
    positions = [farm["farmer"]] + farm["hands"]
    units = [action.get("farmer", [])] + action.get("hands", [])
    for pos, unit, inv in zip(positions, units, private["inventories"]):
        if not unit or pos[0] not in (half - 1, half) or pos[1] not in (half - 1, half):
            continue
        if unit[0] == "PICKUP" and len(unit) > 1:
            item, qty = unit[1], max(0, int(unit[2]) if len(unit) > 2 else 1)
            stock[item] = max(0, stock.get(item, 0) - qty)
        elif unit[0] == "DROP":
            for item, qty in inv.items():
                stock[item] = stock.get(item, 0) + min(max(0, int(qty)), max(0, cap - sum(stock.values())))
        elif unit[0] == "PLACE" and len(unit) > 1 and unit[1] not in _QUEUE_ANIMALS:
            item, qty = unit[1], max(0, int(unit[2]) if len(unit) > 2 else 1)
            stock[item] = stock.get(item, 0) + min(qty, int(inv.get(item, 0)), max(0, cap - sum(stock.values())))
    return stock

def _queue_signature(farm, private):
    return (tuple(sorted(private["shed"].items())),
            tuple(sorted(private["seeds"].items())),
            tuple(tuple(p) for p in farm["hands"]),
            tuple(farm["unlocked_quadrants"]), farm.get("hires_today", 0))

def _queue_simulate(obs, own_orders, rival_orders, stock, cfg):
    player = int(obs["player"])
    farms = copy.deepcopy(obs["farms"])
    market = copy.deepcopy(obs["market"])
    private = obs["private"]
    # The opposing stock is a hypothetical mirror, never rival-private data.
    privates = [{"shed": dict(stock), "seeds": dict(private["seeds"]),
                 "inventories": [{} for _ in range(len(f["hands"])+1)]}
                for f in farms]
    states = [_QueueBox(action={"market": own_orders if i == player else rival_orders},
                        observation=_QueueBox(farms=farms, market=market, private=privates[i]))
              for i in range(2)]
    _QUEUE_ENGINE["_process_market"](states, _QueueBox(configuration=cfg))
    own = farms[player]["money"]
    rival = farms[1-player]["money"]
    return (own, rival, _queue_signature(farms[player], privates[player]),
            _queue_signature(farms[1-player], privates[1-player]))

def _queue_optimize(obs, action, configuration):
    cfg = configuration or {}
    orders = action.get("market", [])
    if len(orders) < 2 or len(orders) > int(cfg.get("maxMarketOrdersPerTurn", 10)):
        return action
    proposals, seen = [], {tuple(tuple(o) for o in orders)}
    for index, order in enumerate(orders):
        if index == 0 or not order or order[0] != "SELL":
            continue
        for earlier in range(index):
            permuted = orders[:earlier] + [order] + orders[earlier:index] + orders[index+1:]
            key = tuple(tuple(o) for o in permuted)
            if key not in seen:
                seen.add(key)
                proposals.append(permuted)
            if len(proposals) >= 24:
                break
        if len(proposals) >= 24:
            break
    if not proposals:
        return action
    stock = _queue_stock(obs, action, cfg)
    original_idle = _queue_simulate(obs, orders, [], stock, cfg)
    original_mirror = _queue_simulate(obs, orders, orders, stock, cfg)
    best_orders = orders
    best = (original_mirror[0]-original_mirror[1], original_mirror[0])
    for proposal in proposals:
        _QUEUE_STATS["queue_proposals"] += 1
        idle = _queue_simulate(obs, proposal, [], stock, cfg)
        if idle[2] != original_idle[2] or idle[0] < original_idle[0]:
            continue
        mirror = _queue_simulate(obs, proposal, orders, stock, cfg)
        if mirror[2:] != original_mirror[2:] or mirror[0] < original_mirror[0]:
            continue
        score = (mirror[0]-mirror[1], mirror[0])
        if score > best and score[0] > original_mirror[0]-original_mirror[1]:
            best, best_orders = score, proposal
    if best_orders is not orders:
        action["market"] = best_orders
        _QUEUE_STATS["queue_turns"] += 1
        _QUEUE_STATS["predicted_margin_gain"] += best[0]-(original_mirror[0]-original_mirror[1])
    return action

def _purchase_queue_apply(obs, action, configuration):
    cfg = configuration or {}
    orders = action.get("market", [])
    if len(orders) < 2 or len(orders) > int(cfg.get("maxMarketOrdersPerTurn", 10)):
        return action
    proposals, seen = [], {tuple(tuple(order) for order in orders)}
    for index, order in enumerate(orders):
        if index == 0 or not order or order[0] != "BUY_PRODUCT":
            continue
        for earlier in range(index):
            proposed = orders[:earlier] + [order] + orders[earlier:index] + orders[index+1:]
            key = tuple(tuple(item) for item in proposed)
            if key not in seen:
                seen.add(key)
                proposals.append(proposed)
            if len(proposals) >= 24:
                break
        if len(proposals) >= 24:
            break
    if not proposals:
        return action
    stock = _queue_stock(obs, action, cfg)
    idle_control = _queue_simulate(obs, orders, [], stock, cfg)
    mirror_control = _queue_simulate(obs, orders, orders, stock, cfg)
    baseline = (mirror_control[0] - mirror_control[1], mirror_control[0])
    best, chosen = baseline, orders
    for proposed in proposals:
        _PURCHASE_QUEUE_STATS["purchase_queue_proposals"] += 1
        idle = _queue_simulate(obs, proposed, [], stock, cfg)
        if idle[2] != idle_control[2] or idle[0] < idle_control[0]:
            continue
        mirror = _queue_simulate(obs, proposed, orders, stock, cfg)
        if mirror[2:] != mirror_control[2:] or mirror[0] < mirror_control[0]:
            continue
        score = (mirror[0] - mirror[1], mirror[0])
        if score > best and score[0] > baseline[0]:
            best, chosen = score, proposed
    if chosen is not orders:
        action["market"] = chosen
        _PURCHASE_QUEUE_STATS["purchase_queue_turns"] += 1
        _PURCHASE_QUEUE_STATS["purchase_predicted_margin_gain"] += best[0] - baseline[0]
    return action

def _iterated_queue_apply(obs, action, configuration):
    cfg = configuration or {}
    base = action.get("market", [])
    if len(base) < 2 or len(base) > int(cfg.get("maxMarketOrdersPerTurn", 10)):
        return action
    stock = _queue_stock(obs, action, cfg)
    raw = _ITERATED_QUEUE_RAW(obs, configuration).get("market", [])
    forecasts = [[], base]
    if raw != base:
        forecasts.append(raw)
    controls = [_queue_simulate(obs, base, rival, stock, cfg) for rival in forecasts]
    current, best_key = base, (0, 0, 0)
    seen = {tuple(tuple(order) for order in base)}
    accepted_passes = 0
    for _ in range(2):
        proposals = []
        for index, order in enumerate(current):
            if index == 0 or not order or order[0] not in ("SELL", "BUY_PRODUCT"):
                continue
            for earlier in range(index):
                candidate = current[:earlier] + [order] + current[earlier:index] + current[index+1:]
                signature = tuple(tuple(o) for o in candidate)
                if signature not in seen:
                    seen.add(signature)
                    proposals.append(candidate)
                if len(proposals) >= 48:
                    break
            if len(proposals) >= 48:
                break
        best_orders = current
        for proposal in proposals:
            _ITERATED_QUEUE_STATS["iterated_queue_proposals"] += 1
            relative_gains, own_gains = [], []
            valid = True
            for forecast_index, (rival, control) in enumerate(zip(forecasts, controls)):
                result = _queue_simulate(obs, proposal, rival, stock, cfg)
                if result[0] < control[0] or result[2] != control[2]:
                    valid = False
                    break
                if forecast_index:
                    if result[3] != control[3]:
                        valid = False
                        break
                    relative_gains.append((result[0]-result[1])-(control[0]-control[1]))
                own_gains.append(result[0]-control[0])
            if not valid or min(relative_gains) < 0 or sum(relative_gains) <= 0:
                continue
            key = (min(relative_gains), sum(relative_gains), min(own_gains))
            if key > best_key:
                best_key, best_orders = key, proposal
        if best_orders is current:
            break
        current = best_orders
        accepted_passes += 1
    if accepted_passes:
        action["market"] = current
        _ITERATED_QUEUE_STATS["iterated_queue_turns"] += 1
        _ITERATED_QUEUE_STATS["iterated_queue_second_pass_turns"] += int(accepted_passes == 2)
        _ITERATED_QUEUE_STATS["iterated_queue_predicted_gain"] += best_key[0]
    return action

def _partial_plant(obs, action, cfg):
    units = [action.get("farmer", ["PASS"]), *action.get("hands", [])]
    need = {}
    for unit in units:
        if len(unit) >= 2 and unit[0] == "PLANT":
            need[unit[1]] = need.get(unit[1], 0) + 1
    available = obs["private"]["seeds"]
    blocked = {crop for crop, count in need.items() if 0 < available.get(crop, 0) < count}
    if not blocked:
        return action
    farm, private = copy.deepcopy(obs["farms"][int(obs["player"])]), copy.deepcopy(obs["private"])
    chosen = copy.deepcopy(units)
    kept = removed = 0
    for index, unit in enumerate(units):
        target = len(unit) >= 2 and unit[0] == "PLANT" and unit[1] in blocked
        before = private["seeds"].get(unit[1], 0) if target else 0
        _PLANT_CORE["_apply_unit_action"](farm, private, index, unit,
            int(cfg.get("boardSize", 10)), int(obs["step"]) // int(cfg.get("turnsPerDay", 24)),
            int(cfg.get("turnsPerDay", 24)), int(cfg.get("shedCapacity", 100)))
        if target:
            if private["seeds"].get(unit[1], 0) == before - 1:
                kept += 1
            else:
                chosen[index] = ["PASS"]
                removed += 1
    if removed:
        action["farmer"], action["hands"] = chosen[0], chosen[1:]
        _PARTIAL_STATS["partial_plant_turns"] += 1
        _PARTIAL_STATS["partial_plant_kept"] += kept
        _PARTIAL_STATS["partial_plant_removed"] += removed
    return action

def _hire_recovery_apply(obs, action, configuration):
    global _HIRE_RECOVERY_PLAN, _HIRE_RECOVERY_QUEUES
    cfg = configuration or {}; step = int(obs['step'])
    per_day = int(cfg.get('turnsPerDay', 24)); hour = step % per_day
    own = obs['farms'][int(obs['player'])]; hands = own['hands']
    moves = {'NORTH', 'SOUTH', 'EAST', 'WEST'}
    if hour == 0:
        _HIRE_RECOVERY_STATS['hire_recovery_day_aborts'] += len(_HIRE_RECOVERY_QUEUES)
        _HIRE_RECOVERY_QUEUES = {}; _HIRE_RECOVERY_PLAN = None
        hires = sum(order == ['HIRE'] for order in action.get('market', []))
        farmer = action.get('farmer', ['PASS'])
        if not hands and hires and farmer and farmer[0] not in moves:
            planned = copy.deepcopy(own)
            for _ in range(hires):
                planned['hands'].append(_QUEUE_ENGINE['_spawn_hand'](planned, int(cfg.get('boardSize', 10))))
            _HIRE_RECOVERY_PLAN = dict(step=step, farmer=copy.deepcopy(own['farmer']), hands=planned['hands'])
        return action

    for worker, pending in list(_HIRE_RECOVERY_QUEUES.items()):
        if worker >= len(hands) or worker >= len(action.get('hands', [])):
            _HIRE_RECOVERY_STATS['hire_recovery_unfilled'] += 1
            del _HIRE_RECOVERY_QUEUES[worker]
            continue
        current = action['hands'][worker]
        if pending and pending[0] == 'CARE':
            _HIRE_RECOVERY_STATS['hire_recovery_caught_up'] += 1
            del _HIRE_RECOVERY_QUEUES[worker]
        else:
            action['hands'][worker] = pending
            _HIRE_RECOVERY_QUEUES[worker] = current
            _HIRE_RECOVERY_STATS['hire_recovery_delayed_commands'] += 1

    plan = _HIRE_RECOVERY_PLAN
    if hour != 1 or not plan or plan['step'] != step - 1:
        return action
    missing = len(plan['hands']) - len(hands)
    if missing not in (1, 2) or hands != plan['hands'][:len(hands)] or own['farmer'] != plan['farmer']:
        return action
    active_commands = [action.get('farmer', ['PASS']), *action.get('hands', [])[:len(hands)]]
    if any(command and command[0] in moves for command in active_commands):
        return action
    orders = action.get('market', [])
    if any(order == ['HIRE'] for order in orders) or len(orders) + missing > int(cfg.get('maxMarketOrdersPerTurn', 10)):
        return action
    schedule = _hire_recovery_schedule(obs)
    allowed = moves | {'PICKUP', 'FEED', 'CARE', 'COLLECT_FERTILIZER', 'WATER', 'PASS'}
    delayed = {}
    for worker in range(len(hands), len(plan['hands'])):
        commands = action.get('hands', [])
        if worker >= len(commands) or commands[worker][:2] != ['PICKUP', 'WHEAT']:
            return action
        found = False
        for future in range(step + 1, min(step + 9, len(schedule))):
            upcoming = schedule[future].get('hands', [])
            if worker >= len(upcoming) or not upcoming[worker] or upcoming[worker][0] not in allowed:
                return action
            if upcoming[worker][0] == 'CARE':
                found = True
                break
        if not found:
            return action
        delayed[worker] = copy.deepcopy(commands[worker])
    proposal = orders + [['HIRE'] for _ in range(missing)]
    stock = _queue_stock(obs, action, cfg)
    raw = _ITERATED_QUEUE_RAW(obs, configuration).get('market', [])
    forecasts = [[], orders] + ([raw] if raw != orders else [])
    for rival in forecasts:
        old = _queue_simulate(obs, orders, rival, stock, cfg)
        new = _queue_simulate(obs, proposal, rival, stock, cfg)
        if new[0] < 0 or new[2][0:2] != old[2][0:2] or new[2][3] != old[2][3]:
            return action
        if new[2][2] != tuple(tuple(p) for p in plan['hands']):
            return action
    action['market'] = proposal
    _HIRE_RECOVERY_QUEUES = delayed
    _HIRE_RECOVERY_STATS['hire_recovery_turns'] += 1
    _HIRE_RECOVERY_STATS['hire_recovery_requested'] += missing
    return action

_QUEUE_STATS = {"queue_turns": 0, "queue_proposals": 0, "queue_errors": 0,
                "predicted_margin_gain": 0.0}

_PURCHASE_QUEUE_STATS = {"purchase_queue_turns": 0, "purchase_queue_proposals": 0,
                         "purchase_queue_errors": 0, "purchase_predicted_margin_gain": 0.0}

_ITERATED_QUEUE_STATS = {
    "iterated_queue_turns": 0,
    "iterated_queue_second_pass_turns": 0,
    "iterated_queue_proposals": 0,
    "iterated_queue_predicted_gain": 0.0,
    "iterated_queue_errors": 0,
}

_PARTIAL_STATS = {"partial_plant_turns": 0, "partial_plant_kept": 0,
                  "partial_plant_removed": 0, "partial_plant_errors": 0}

_HIRE_RECOVERY_STATS = {'hire_recovery_turns': 0, 'hire_recovery_requested': 0,
                        'hire_recovery_delayed_commands': 0, 'hire_recovery_caught_up': 0,
                        'hire_recovery_unfilled': 0, 'hire_recovery_day_aborts': 0,
                        'hire_recovery_errors': 0}
