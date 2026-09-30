"""Mechanism checks for the rival-aware investment model."""

import unittest

import margin_model as m


def empty_observation():
    board = [[None for _ in range(10)] for _ in range(10)]
    return {
        "day": 0,
        "step": 0,
        "player": 0,
        "farms": [{"tiles": board}, {"tiles": board}],
        "market": {"inventory": {k: 10000 for k in m.e.PRODUCTS}},
        "town": {"unlocked_shops": []},
    }


class MarginModelTests(unittest.TestCase):
    def test_projected_sale_depresses_rival_strawberry_receipts(self):
        obs = empty_observation()
        obs["market"]["inventory"]["STRAWBERRY"] = 10050
        own, rival, extra = (m.e._empty(1) for _ in range(3))
        rival["STRAWBERRY"][0] = 20
        extra["STRAWBERRY"][0] = 50
        demand = {k: [0] for k in m.e.PRODUCTS}
        own_delta, rival_delta = m._project(
            "STRAWBERRY", obs, {}, own, rival, extra, demand, 1.0)
        self.assertGreater(own_delta, 0)
        self.assertLess(rival_delta, 0)
        self.assertGreater(own_delta-rival_delta, own_delta)

    def test_short_cycle_requires_a_complete_crop_horizon(self):
        obs = empty_observation()
        short = m.investment_values(obs, {}, mode="short_cycle")
        terminal = m.investment_values(obs, {}, mode="terminal_margin")
        self.assertGreater(short["WHEAT"]["score"], -1e9)
        self.assertEqual(short["STRAWBERRY"]["score"], -1e9)
        self.assertGreater(terminal["STRAWBERRY"]["score"], -1e9)

    def test_unknown_mode_is_rejected(self):
        with self.assertRaises(ValueError):
            m.investment_values(empty_observation(), {}, mode="oracle")

    def test_score_contains_separate_own_and_rival_cash(self):
        values = m.investment_values(empty_observation(), {}, mode="terminal_margin")
        value = values["WHEAT"]
        self.assertEqual(len(value["own_scenarios"]), 2)
        self.assertEqual(len(value["rival_scenarios"]), 2)
        self.assertEqual(len(value["margin_scenarios"]), 2)
        for own, rival, margin in zip(value["own_scenarios"],
                                      value["rival_scenarios"],
                                      value["margin_scenarios"]):
            self.assertAlmostEqual(own-rival, margin)


if __name__ == "__main__":
    unittest.main()
