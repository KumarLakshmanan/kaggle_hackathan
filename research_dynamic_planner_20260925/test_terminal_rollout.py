"""Unit checks for the controlled terminal-cash A/B accounting."""

import unittest

from terminal_rollout import score_block


def row(seed, seat, own, rival, result="loss"):
    return {
        "seed": seed,
        "candidate_seat": seat,
        "candidate_reward": own,
        "opponent_reward": rival,
        "margin": own-rival,
        "candidate_status": "DONE",
        "opponent_status": "DONE",
        "candidate_timing": {"max_ms": 5.0},
        "result": result,
    }


class RolloutAccountingTests(unittest.TestCase):
    def test_margin_decomposes_into_own_and_rival_cash(self):
        block = score_block(row(7, 1, 100, 120),
                            row(7, 1, 130, 140, "loss"))
        self.assertEqual(block["own_delta"], 30)
        self.assertEqual(block["rival_delta"], 20)
        self.assertEqual(block["margin_delta"], 10)
        self.assertTrue(block["all_done"])

    def test_identity_intervention_has_zero_effect(self):
        observation = row(9, 0, 111, 222)
        block = score_block(observation, dict(observation))
        self.assertEqual((block["own_delta"], block["rival_delta"],
                          block["margin_delta"]), (0, 0, 0))

    def test_mismatched_seat_is_rejected(self):
        with self.assertRaises(ValueError):
            score_block(row(7, 0, 100, 120), row(7, 1, 130, 140))

    def test_inconsistent_margin_is_rejected(self):
        changed = row(7, 0, 130, 140)
        changed["margin"] = 999
        with self.assertRaises(AssertionError):
            score_block(row(7, 0, 100, 120), changed)


if __name__ == "__main__":
    unittest.main()
