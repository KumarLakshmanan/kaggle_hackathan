"""Fit a small visible-state opening selector to the development arm screen.

No episode or opponent identity enters a rule. Results remain development
evidence and require separate native reacting confirmation.
"""
from pathlib import Path
import itertools
import json

HERE = Path(__file__).resolve().parent
CONDITIONS = ([{"feature": "rival_hands", "threshold": n} for n in (0, 2, 4, 6, 8)] +
              [{"feature": "rival_cash", "threshold": n} for n in (500, 1000, 1500, 2000, 2500)] +
              [{"feature": "rival_wheat_net_buy", "threshold": n} for n in (0, 4, 8, 16, 32)])


def features(row):
    obs = row["candidate_capture"]
    rival = obs["farms"][1 - int(obs["player"])]
    return {"rival_hands": int(rival["hands"]), "rival_cash": float(rival["money"]),
            "rival_wheat_net_buy": 10000 - int(obs["inventory"]["WHEAT"]) - 6}


def branch_condition(condition, item):
    return item[condition["feature"]] <= condition["threshold"]


def main():
    data = json.loads((HERE / "arms.json").read_text(encoding="utf-8"))
    assert data["complete"] and data["game_count"] == 200 and data["same_step1_captures"]
    games = data["games"]
    cases = {}
    for row in games:
        key = (row["fixture_id"], row["candidate_seat"])
        cases.setdefault(key, {})[row["arm"]] = row
    ordered = sorted(cases)
    pairs = list(dict.fromkeys(key[0] for key in ordered))
    case_indices = {key: i for i, key in enumerate(ordered)}
    paired_indices = [(case_indices[(fixture, 0)], case_indices[(fixture, 1)]) for fixture in pairs]
    x = [features(cases[key]["4ee"]) for key in ordered]
    for key, item in zip(ordered, x):
        assert features(cases[key]["v43"]) == item
    prediction_cache = {}

    def evaluate(selection):
        selection = tuple(selection)
        if selection in prediction_cache:
            return prediction_cache[selection]
        chosen = [cases[key][arm] for key, arm in zip(ordered, selection)]
        wins = [r["result"] == "win" for r in chosen]
        draws = [r["result"] == "draw" for r in chosen]
        sweeps = sum(wins[a] and wins[b] for a, b in paired_indices)
        regressions = sum(r["baseline_result"] == "win" and r["result"] != "win" for r in chosen)
        score = (sweeps, 2 * sum(wins) + sum(draws), -regressions,
                 sum(r["margin_delta"] for r in chosen))
        result = {"score": score, "sweeps": sweeps, "seat_wins": sum(wins),
                  "seat_draws": sum(draws), "lost_incumbent_win_seats": regressions,
                  "summed_margin_delta": score[3], "selection": selection}
        prediction_cache[selection] = result
        return result

    best = None
    best_no_regression = None

    def consider(rule, selection):
        nonlocal best, best_no_regression
        result = evaluate(selection)
        candidate = {"rule": rule, **result}
        if best is None or result["score"] > best["score"]:
            best = candidate
        if result["lost_incumbent_win_seats"] == 0 and (
                best_no_regression is None or result["score"] > best_no_regression["score"]):
            best_no_regression = candidate

    for arm in ("4ee", "v43"):
        consider({"arm": arm}, [arm] * len(x))
    tests = [[branch_condition(c, item) for item in x] for c in CONDITIONS]
    for ci, condition in enumerate(CONDITIONS):
        for yes, no in (("4ee", "v43"), ("v43", "4ee")):
            rule = {"condition": condition, "yes": {"arm": yes}, "no": {"arm": no}}
            consider(rule, [yes if t else no for t in tests[ci]])
        for cj, second in enumerate(CONDITIONS):
            if ci == cj:
                continue
            for split_yes in (False, True):
                for a, b, c in itertools.product(("4ee", "v43"), repeat=3):
                    subtree = {"condition": second, "yes": {"arm": a}, "no": {"arm": b}}
                    rule = {"condition": condition,
                            "yes": subtree if split_yes else {"arm": c},
                            "no": {"arm": c} if split_yes else subtree}
                    selection = [((a if t2 else b) if t1 == split_yes else c)
                                 for t1, t2 in zip(tests[ci], tests[cj])]
                    consider(rule, selection)
    for candidate in (best, best_no_regression):
        if candidate and "selection" in candidate:
            candidate["choices"] = [{"fixture_id": key[0], "seat": key[1], "features": item,
                                      "arm": arm, "result": cases[key][arm]["result"],
                                      "margin": cases[key][arm]["margin"]}
                                     for key, item, arm in zip(ordered, x, candidate.pop("selection"))]
    oracle_sweeps = 0
    for fixture in pairs:
        oracle_sweeps += any(all(cases[(fixture, seat)][arm]["result"] == "win" for seat in (0, 1))
                             for arm in ("4ee", "v43"))
    output = {"fit_scope": "All 50 saved fixtures are development; not independent validation.",
              "allowed_conditions": CONDITIONS, "unique_rule_predictions": len(prediction_cache),
              "best": best, "best_preserving_incumbent_wins": best_no_regression,
              "oracle_both_seat_sweeps": oracle_sweeps,
              "oracle_interpretation": "Chooses each entire arm after seeing rewards; diagnostic ceiling only."}
    (HERE / "selection.json").write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"oracle_both_seat_sweeps": oracle_sweeps,
                      "best": {k:v for k,v in best.items() if k != "choices"},
                      "best_preserving_incumbent_wins": None if best_no_regression is None else
                          {k:v for k,v in best_no_regression.items() if k != "choices"}}, indent=2))


if __name__ == "__main__":
    main()
