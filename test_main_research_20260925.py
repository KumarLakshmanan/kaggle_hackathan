"""Mechanism checks for the separate research policy overlays."""

import unittest

import main_research as research


def observation(shed=None, step=120, hands=None, rival_hands=None):
    own_tiles = [[None for _ in range(10)] for _ in range(10)]
    rival_tiles = [[None for _ in range(10)] for _ in range(10)]
    own_tiles[0][0] = {"animal": "SHEEP", "placed_day": 0,
                       "yield_units": 6}
    rival_tiles[0][0] = {"animal": "SHEEP", "placed_day": 0,
                         "yield_units": 6}
    own_hands = hands or []
    return {
        "step": step, "player": 0,
        "farms": [
            {"farmer": [0, 0], "hands": own_hands, "tiles": own_tiles},
            {"farmer": [0, 0], "hands": rival_hands or [],
             "tiles": rival_tiles},
        ],
        "private": {"shed": shed or {},
                    "inventories": [{} for _ in range(len(own_hands)+1)]},
    }


class ResearchPlannerTests(unittest.TestCase):
    def test_idle_full_animal_is_harvested_before_scheduled_yield(self):
        result = research._spare_yield_rescue(
            observation(), {"farmer": ["PASS"], "hands": [], "market": []}, {})
        self.assertEqual(result["farmer"], ["HARVEST"])

    def test_no_shed_room_prevents_extra_harvest(self):
        result = research._spare_yield_rescue(
            observation(shed={"WHEAT": 95}),
            {"farmer": ["PASS"], "hands": [], "market": []}, {})
        self.assertEqual(result["farmer"], ["PASS"])

    def test_busy_unit_is_not_preempted(self):
        result = research._spare_yield_rescue(
            observation(), {"farmer": ["CARE"], "hands": [], "market": []}, {})
        self.assertEqual(result["farmer"], ["CARE"])

    def test_market_purchase_reserves_shed_room(self):
        result = research._spare_yield_rescue(
            observation(),
            {"farmer": ["PASS"], "hands": [],
             "market": [["BUY_PRODUCT", "WHEAT", 1]]}, {})
        self.assertEqual(result["farmer"], ["PASS"])

    def test_rival_ready_deduplicates_colocated_hands(self):
        self.assertEqual(research._rival_ready(
            observation(rival_hands=[[0, 0], [0, 0]]))["WOOL"], 6)


if __name__ == "__main__":
    unittest.main()
