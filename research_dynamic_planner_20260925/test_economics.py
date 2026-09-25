"""Exact mechanics parity checks for the independent investment model."""

import unittest
from copy import deepcopy
import economics
from kaggle_environments.envs.kaggriculture import kaggriculture as engine


class EconomicsTests(unittest.TestCase):
    def test_price_matches_engine_including_hinges_and_overrides(self):
        patches = (None, {"CARROT": {"T": 80, "base": 50}, "WOOL": {"above_target": .95}})
        for patch in patches:
            params = engine._resolve_market_params(patch)
            for item in economics.PRODUCTS:
                for n in (1000, 8500, 9499, 9500, 9799, 9899, 9999, 10000, 10001, 10060, 10100, 10450, 11000, 15000):
                    self.assertEqual(economics.price(item, n, patch), engine.market_price(item, n, params), (item, n, patch))

    def test_repeated_shops_and_town_center(self):
        obs = {"town": {"unlocked_shops": ["PET_CAFE", "PET_CAFE", "PIZZA_SHOP"]}}
        rates = economics.demand_per_day(obs, {})
        self.assertEqual(rates["CARROT"], 25)
        self.assertEqual(rates["MILK"], 7)
        self.assertEqual(rates["FERTILIZER"], 0)

    def test_new_livestock_profile_matches_care_bank_order(self):
        for animal in economics.ANIMALS:
            farm = engine._new_farm(10, 3000)
            tile = engine._new_animal(animal, 0)
            farm["tiles"][4][4] = tile
            profile = economics._new_profile(animal, 0, 18)
            product = engine.ANIMALS[animal]["product"]
            for day in range(17):
                tile["yield_units"] = 0
                tile["fed_today"] = True
                tile["cared_today"] = True
                engine._daily_refresh_animals(farm, day)
                self.assertEqual(profile[product][day+1], tile["yield_units"], (animal, day))
                self.assertEqual(profile["FERTILIZER"][day+1], 1)

    def test_unfertilized_one_time_crops_match_engine(self):
        for crop, age in (("WHEAT", 4), ("CARROT", 3), ("MELON", 10)):
            farm = engine._new_farm(10, 3000)
            private = engine._new_private()
            farm["tiles"][4][4] = engine._new_plant(crop, 0, 24)
            for day in range(age+1):
                engine._apply_unit_action(farm, private, 0, ["WATER"], 10, day, 24)
                if day < age:
                    engine._daily_refresh_plants(farm, day, 24)
            expected = farm["tiles"][4][4]["yield_units"]
            self.assertEqual(economics._new_profile(crop, 0, 30)[crop][age], expected)
            if crop == "MELON":
                younger = engine._new_plant(crop, 0, 24)
                younger["yield_units"] = 6
                farm["tiles"][4][4] = younger
                engine._apply_unit_action(farm, private, 0, ["HARVEST"], 10, 8, 24)
                self.assertEqual(private["inventories"][0], {})

    def test_ongoing_production_and_fertilizer_dates(self):
        for crop in ("TOMATO", "STRAWBERRY"):
            farm = engine._new_farm(10, 3000)
            private = engine._new_private()
            private["inventories"][0]["FERTILIZER"] = 2
            farm["tiles"][4][4] = engine._new_plant(crop, 0, 24)
            schedule = (7, 10) if crop == "TOMATO" else (9, 13)
            profile = economics._new_profile(crop, 0, 18)
            for day in range(17):
                if day in schedule:
                    engine._apply_unit_action(farm, private, 0, ["FERTILIZE"], 10, day, 24)
                engine._apply_unit_action(farm, private, 0, ["WATER"], 10, day, 24)
                engine._daily_refresh_plants(farm, day, 24)
                tile = farm["tiles"][4][4]
                self.assertEqual(profile[crop][day+1], tile["yield_units"], (crop, day))
                tile["yield_units"] = 0


if __name__ == "__main__":
    unittest.main()
