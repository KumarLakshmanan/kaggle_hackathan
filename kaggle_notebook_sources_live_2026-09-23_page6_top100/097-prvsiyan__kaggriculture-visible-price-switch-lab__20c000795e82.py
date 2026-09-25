CROP_YIELD = {"WHEAT": 4.0, "CARROT": 3.0}

def choose_fast_crop(prices, current="CARROT", margin=1.0):
    """Choose a crop from current public prices only."""
    if current not in CROP_YIELD:
        raise ValueError("current must be WHEAT or CARROT")
    values = {crop: CROP_YIELD[crop] * float(prices[crop])
              for crop in CROP_YIELD}
    other = "WHEAT" if current == "CARROT" else "CARROT"
    return other if values[other] - values[current] >= margin else current

examples = [
    {"WHEAT": 4, "CARROT": 5},
    {"WHEAT": 7, "CARROT": 6},
    {"WHEAT": 5, "CARROT": 7},
]
for prices in examples:
    choice = choose_fast_crop(prices, current="CARROT")
    values = {crop: CROP_YIELD[crop] * prices[crop] for crop in CROP_YIELD}
    print(prices, "value=", values, "choice=", choice)

def route_late_wave(price_trace, current="CARROT", margin=1.0):
    """Return one auditable choice per visible observation."""
    return [choose_fast_crop(prices, current=current, margin=margin)
            for prices in price_trace]

trace = [
    {"WHEAT": 5, "CARROT": 7},
    {"WHEAT": 8, "CARROT": 7},
    {"WHEAT": 6, "CARROT": 8},
]
print(route_late_wave(trace, current="CARROT", margin=1.0))