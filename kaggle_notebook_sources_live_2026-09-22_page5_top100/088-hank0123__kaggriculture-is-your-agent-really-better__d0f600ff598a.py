from pathlib import Path

RESULTS_PATH = ""  # e.g. "/kaggle/input/your-results/results.jsonl"
AGENT_A = "candidate"
AGENT_B = "baseline"
N_BOOT = 5000

BASE_OUTPUT = Path("/kaggle/working") if Path("/kaggle/working").is_dir() else Path.cwd()
OUTPUT_DIR = BASE_OUTPUT / "paired_eval_output"

import json
import math
import hashlib
import platform
import pandas as pd
import matplotlib.pyplot as plt
from IPython.display import display

print("Input mode:", "SYNTHETIC DEMO" if RESULTS_PATH == "" else "USER-SUPPLIED RESULTS")


"""Paired-seed outcome aggregation + bootstrap CIs (EXP-002/003).

Unit of resampling = the seed PAIR (both seat orderings of one seed), which
respects the seat-swap pairing structure: each seed contributes one paired
outcome in [0, 1] for agent A (win=1, tie=0.5, loss=0 per game, averaged over
the two seats).
"""

import random


def paired_outcomes(rows, agent_a, agent_b):
    """rows: result_row dicts (agents=[name0, name1], winner in {0,1,-1},
    margin = rewards[0]-rewards[1]). Returns dict seed -> {"score": s in [0,1],
    "margin": mean margin from A's perspective, "games": n}."""
    per_seed = {}
    for r in rows:
        a0, a1 = r["agents"]
        if {a0, a1} != {agent_a, agent_b}:
            continue
        seed = r["seed"]
        if r["winner"] == -1:
            score_a = 0.5
        else:
            winner_name = r["agents"][r["winner"]]
            score_a = 1.0 if winner_name == agent_a else 0.0
        margin_a = None
        if r["margin"] is not None:
            margin_a = r["margin"] if a0 == agent_a else -r["margin"]
        d = per_seed.setdefault(seed, {"score_sum": 0.0, "margin_sum": 0.0,
                                       "margin_n": 0, "games": 0})
        d["score_sum"] += score_a
        d["games"] += 1
        if margin_a is not None:
            d["margin_sum"] += margin_a
            d["margin_n"] += 1
    out = {}
    for seed, d in per_seed.items():
        out[seed] = {
            "score": d["score_sum"] / d["games"],
            "margin": (d["margin_sum"] / d["margin_n"]) if d["margin_n"] else None,
            "games": d["games"],
        }
    return out


def bootstrap_ci(values, n_boot=10000, alpha=0.05, rng_seed=1234):
    """Percentile bootstrap CI for the mean of `values` (resample with
    replacement). Deterministic given rng_seed."""
    values = [v for v in values if v is not None]
    n = len(values)
    if n == 0:
        return None, None, None
    mean = sum(values) / n
    if n == 1:
        return mean, values[0], values[0]
    rng = random.Random(rng_seed)
    boots = []
    for _ in range(n_boot):
        s = 0.0
        for _ in range(n):
            s += values[rng.randrange(n)]
        boots.append(s / n)
    boots.sort()
    lo = boots[int((alpha / 2) * n_boot)]
    hi = boots[min(n_boot - 1, int((1 - alpha / 2) * n_boot))]
    return mean, lo, hi


def matchup_summary(rows, agent_a, agent_b, n_boot=10000):
    per_seed = paired_outcomes(rows, agent_a, agent_b)
    scores = [d["score"] for d in per_seed.values()]
    margins = [d["margin"] for d in per_seed.values() if d["margin"] is not None]
    wr, wr_lo, wr_hi = bootstrap_ci(scores, n_boot=n_boot)
    mg, mg_lo, mg_hi = bootstrap_ci(margins, n_boot=n_boot, rng_seed=5678)
    wins = losses = ties = 0
    for r in rows:
        if {r["agents"][0], r["agents"][1]} != {agent_a, agent_b}:
            continue
        if r["winner"] == -1:
            ties += 1
        elif r["agents"][r["winner"]] == agent_a:
            wins += 1
        else:
            losses += 1
    return {
        "agent": agent_a, "opponent": agent_b,
        "paired_seeds": len(per_seed), "games": wins + losses + ties,
        "wins": wins, "losses": losses, "ties": ties,
        "win_rate": wr, "ci95_low": wr_lo, "ci95_high": wr_hi,
        "coin_margin_mean": mg, "coin_margin_ci95": [mg_lo, mg_hi],
    }


def seat_split(rows, agent_a, agent_b):
    """Win rate of agent_a split by seat, for EXP-003 seat-effect analysis."""
    by_seat = {0: [], 1: []}
    for r in rows:
        a0, a1 = r["agents"]
        if {a0, a1} != {agent_a, agent_b}:
            continue
        seat = 0 if a0 == agent_a else 1
        if r["winner"] == -1:
            s = 0.5
        else:
            s = 1.0 if r["agents"][r["winner"]] == agent_a else 0.0
        by_seat[seat].append(s)
    out = {}
    for seat, vals in by_seat.items():
        m, lo, hi = bootstrap_ci(vals, rng_seed=42 + seat)
        out[f"seat{seat}"] = {"n": len(vals), "win_rate": m, "ci95": [lo, hi]}
    return out


"""Publication adapter: validation and readable labels; legacy statistics stay unchanged."""
from pathlib import Path
from collections import defaultdict
import gzip
import hashlib
import json
import math


class ResultsError(ValueError):
    """Input is not a complete, comparable two-seat result set."""


def _finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def _strict_json(text):
    def reject_constant(value):
        raise ResultsError(f"Non-finite JSON constant: {value}")
    return json.loads(text, parse_constant=reject_constant)


def read_results(path, max_bytes=50_000_000, max_rows=100_000):
    """Read a JSON array / JSONL, optionally gzip. Never replace a bad file with a demo."""
    path = Path(path).expanduser()
    if not path.is_file():
        raise FileNotFoundError(f"Results file not found: {path}")
    suffixes = ''.join(path.suffixes).lower()
    if not any(suffixes.endswith(s) for s in ('.json', '.jsonl', '.json.gz', '.jsonl.gz')):
        raise ResultsError("Use .json, .jsonl, .json.gz or .jsonl.gz; no archives or raw replays.")
    opener = gzip.open if suffixes.endswith('.gz') else open
    with opener(path, 'rb') as handle:
        raw = handle.read(max_bytes + 1)
    if len(raw) > max_bytes:
        raise ResultsError("Decompressed input exceeds the size limit; split by experiment/matchup.")
    try:
        text = raw.decode('utf-8-sig')
        if suffixes.endswith(('.jsonl', '.jsonl.gz')):
            rows = []
            for line_number, line in enumerate(text.splitlines(), start=1):
                if line.strip():
                    try:
                        rows.append(_strict_json(line))
                    except (ValueError, TypeError) as exc:
                        raise ResultsError(f"Invalid JSONL at line {line_number}.") from exc
                    if len(rows) > max_rows:
                        raise ResultsError("Too many result rows; split by experiment/matchup.")
        else:
            rows = _strict_json(text)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ResultsError("Input must be valid UTF-8 JSON/JSONL.") from exc
    if not isinstance(rows, list):
        raise ResultsError("Expected a result-row array, not a raw replay or summary object.")
    if len(rows) > max_rows:
        raise ResultsError("Too many result rows; split by experiment/matchup.")
    return rows, hashlib.sha256(raw).hexdigest()


def validate_results(rows, agent_a, agent_b):
    """Return sorted selected rows plus an audit. Fail rather than silently drop bad games."""
    if not all(isinstance(a, str) and a.strip() for a in (agent_a, agent_b)) or agent_a == agent_b:
        raise ResultsError("Choose two distinct, non-empty agent labels.")
    if not isinstance(rows, list) or not rows:
        raise ResultsError("No result rows supplied.")
    selected = []
    ignored = 0
    notices = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ResultsError(f"Row {index}: expected an object.")
        agents = row.get('agents')
        if (not isinstance(agents, list) or len(agents) != 2 or
                not all(isinstance(a, str) and a.strip() for a in agents) or agents[0] == agents[1]):
            raise ResultsError(f"Row {index}: agents must contain two distinct labels.")
        if set(agents) != {agent_a, agent_b}:
            ignored += 1
            continue  # Unrelated matchups are counted in the audit, never used in this estimate.
        if type(row.get('seed')) is not int:
            raise ResultsError(f"Row {index}: seed must be an integer, not a string or boolean.")
        if type(row.get('winner')) is not int or row['winner'] not in (-1, 0, 1):
            raise ResultsError(f"Row {index}: winner must be -1 (draw), 0 or 1 (seat index).")
        if 'margin' not in row or (row['margin'] is not None and not _finite(row['margin'])):
            raise ResultsError(f"Row {index}: margin must be finite numeric or null.")
        if row['margin'] is not None:
            expected = 0 if row['margin'] > 0 else 1 if row['margin'] < 0 else -1
            if row['winner'] != expected:
                raise ResultsError(f"Row {index}: winner conflicts with margin = reward[0] - reward[1].")
        if 'rewards' in row:
            rewards = row['rewards']
            if not isinstance(rewards, list) or len(rewards) != 2 or not all(_finite(v) for v in rewards):
                raise ResultsError(f"Row {index}: incomplete/non-finite rewards need a fault audit.")
            difference = rewards[0] - rewards[1]
            expected = 0 if difference > 0 else 1 if difference < 0 else -1
            if row['winner'] != expected:
                raise ResultsError(f"Row {index}: winner conflicts with rewards.")
            if row['margin'] is not None and not math.isclose(row['margin'], difference, rel_tol=1e-9, abs_tol=1e-9):
                raise ResultsError(f"Row {index}: margin conflicts with rewards.")
        if 'statuses' in row and row['statuses'] != ['DONE', 'DONE']:
            raise ResultsError(f"Row {index}: terminal statuses are not DONE/DONE; audit, do not filter away.")
        if 'fault_counts' in row:
            counts = row['fault_counts']
            if (not isinstance(counts, list) or len(counts) != 2 or
                    any(not isinstance(c, dict) or not c for c in counts)):
                raise ResultsError(f"Row {index}: fault_counts must contain two non-empty count objects.")
            if any(type(v) is not int or v < 0 for c in counts for v in c.values()):
                raise ResultsError(f"Row {index}: fault counts must be nonnegative integers.")
            if any(v > 0 for c in counts for v in c.values()):
                raise ResultsError(f"Row {index}: a recorded fault needs a separate audit; no silent exclusion.")
        if 'config' in row:
            if not isinstance(row['config'], dict):
                raise ResultsError(f"Row {index}: config must be an object.")
            if 'seed' in row['config'] and (type(row['config']['seed']) is not int or row['config']['seed'] != row['seed']):
                raise ResultsError(f"Row {index}: config.seed conflicts with the recorded seed.")
        selected.append(row)
    if not selected:
        raise ResultsError("No rows match the selected two agents; check labels.")

    # Only metadata that is actually present can be checked. Never assert engine identity from a label.
    checked_metadata = []
    for key in ('config', 'engine_sha256', 'engine_version', 'experiment_id', 'runner', 'agent_sha256', 'data_kind'):
        present = [key in r for r in selected]
        if any(present) and not all(present):
            raise ResultsError(f"Metadata '{key}' is present only on some selected rows.")
        if not any(present):
            continue
        values = []
        for row in selected:
            value = row[key]
            if key == 'config':
                value = {k: v for k, v in value.items() if k != 'seed'}
            if key == 'agent_sha256':
                if (not isinstance(value, dict) or set(value) != {agent_a, agent_b} or
                        not all(isinstance(v, str) and len(v) == 64 and
                                all(c in '0123456789abcdefABCDEF' for c in v) for v in value.values())):
                    raise ResultsError("agent_sha256 must map each selected label to its 64-hex source hash.")
            if key in ('engine_sha256', 'engine_version', 'experiment_id', 'runner', 'data_kind'):
                if not isinstance(value, str) or not value.strip():
                    raise ResultsError(f"Metadata '{key}' must be a non-empty string when supplied.")
            if key == 'engine_sha256' and (len(value) != 64 or any(c not in '0123456789abcdefABCDEF' for c in value)):
                raise ResultsError("engine_sha256 must be a 64-hex source hash.")
            try:
                values.append(json.dumps(value, sort_keys=True, allow_nan=False))
            except (TypeError, ValueError) as exc:
                raise ResultsError(f"Metadata '{key}' must be finite JSON data.") from exc
        if len(set(values)) != 1:
            raise ResultsError(f"Mixed '{key}' values: do not merge different experiments or versions.")
        checked_metadata.append(key)
    for key in ('config', 'engine_sha256', 'agent_sha256', 'experiment_id'):
        if key not in checked_metadata:
            notices.append(f"{key}: absent; comparability is not verified for this field.")
    for key in ('statuses', 'fault_counts'):
        available = sum(key in r for r in selected)
        if available != len(selected):
            notices.append(f"{key}: only {available}/{len(selected)} rows have health metadata; audit the rest.")
    groups = defaultdict(list)
    for row in selected:
        groups[row['seed']].append(row)
    for seed, pair in groups.items():
        seats = [r['agents'].index(agent_a) for r in pair]
        if len(pair) != 2 or sorted(seats) != [0, 1]:
            raise ResultsError(f"Seed {seed}: require exactly one A/B and one B/A result; got A seats {seats}.")
        if sum(r['margin'] is not None for r in pair) == 1:
            raise ResultsError(f"Seed {seed}: one margin is missing; use two known margins or two nulls.")
    selected = sorted(selected, key=lambda r: (r['seed'], r['agents'].index(agent_a)))
    missing_margin_pairs = sum(all(r['margin'] is None for r in pair) for pair in groups.values())
    if missing_margin_pairs:
        notices.append(f"{missing_margin_pairs} seed pairs lack margins: score uses all pairs; margin uses only complete-margin pairs.")
    if len(groups) < 20:
        notices.append("Fewer than 20 seed pairs: small-sample warning (a display heuristic, not a validity threshold).")
    if ignored:
        notices.append(f"{ignored} rows belong to other matchups and are not part of this comparison.")
    audit = dict(input_rows=len(rows), selected_rows=len(selected), other_matchup_rows=ignored,
                 complete_seed_pairs=len(groups), missing_margin_pairs=missing_margin_pairs,
                 checked_metadata=checked_metadata, notices=notices)
    return selected, audit


def build_report(rows, agent_a, agent_b, n_boot=5000):
    """Run the preserved calculations and add explicit semantics / caveats."""
    if type(n_boot) is not int or not 100 <= n_boot <= 50_000:
        raise ResultsError("n_boot must be an integer between 100 and 50,000.")
    selected, audit = validate_results(rows, agent_a, agent_b)
    legacy = matchup_summary(selected, agent_a, agent_b, n_boot=n_boot)
    by_seed = paired_outcomes(selected, agent_a, agent_b)
    scores = [r['score'] for r in by_seed.values()]
    notices = list(audit['notices'])
    degenerate = len(scores) < 2 or len(set(scores)) == 1
    if degenerate:
        notices.append("DEGENERATE score bootstrap: a point interval is not proof of certainty or equal agents.")
    margins = [r['margin'] for r in by_seed.values() if r['margin'] is not None]
    if margins and (len(margins) < 2 or len(set(margins)) == 1):
        notices.append("DEGENERATE margin bootstrap: interpret the point interval as descriptive only.")
    lo, hi = legacy['ci95_low'], legacy['ci95_high']
    interval_reading = ('Descriptive only: degenerate paired-score sample.' if degenerate else
                        'The displayed interval includes 0.5; this comparison does not separate the mean score from parity.' if lo <= .5 <= hi else
                        'The displayed interval lies above 0.5 for this matchup and seed set; this is not a promotion decision.' if lo > .5 else
                        'The displayed interval lies below 0.5 for this matchup and seed set; this is not a global ranking.')
    fingerprint_rows = [{k: r[k] for k in ('seed', 'agents', 'winner', 'margin', 'config', 'engine_sha256',
                                          'engine_version', 'experiment_id', 'runner', 'agent_sha256', 'data_kind') if k in r}
                        for r in selected]
    fingerprint = hashlib.sha256(json.dumps(fingerprint_rows, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()
    report = {
        'schema': 'paired-evaluation-review-v1', 'agent': agent_a, 'opponent': agent_b,
        'data_kind': selected[0].get('data_kind', 'user_supplied_results_unverified'),
        'games': legacy['games'], 'seed_pairs': len(by_seed),
        'wins': legacy['wins'], 'draws': legacy['ties'], 'losses': legacy['losses'],
        'raw_win_rate': legacy['wins'] / legacy['games'],
        'mean_score': legacy['win_rate'], 'score_ci95_percentile': [lo, hi],
        'mean_reward_margin': legacy['coin_margin_mean'], 'margin_ci95_percentile': legacy['coin_margin_ci95'],
        'margin_seed_pairs': len(margins), 'score_bootstrap_degenerate': degenerate,
        'bootstrap': {'method': 'legacy percentile', 'unit': 'whole seed pair',
                      'score_margin_resamples': n_boot, 'seat_resamples': 10000,
                      'rng_seeds': {'score': 1234, 'margin': 5678, 'seat0': 42, 'seat1': 43}},
        'seat_scores': seat_split(selected, agent_a, agent_b),
        'input_audit': audit, 'notices': notices, 'interval_reading': interval_reading,
        'selected_results_sha256': fingerprint, 'legacy_summary': legacy,
        'publication_status': 'not_published',
    }
    if report['data_kind'].startswith('synthetic'):
        report['interval_reading'] = 'SYNTHETIC DEMO ONLY. ' + interval_reading
    return report, by_seed, selected


def make_demo_rows(agent_a='candidate', agent_b='baseline'):
    """96 deliberately constructed results. Not simulated games or research measurements."""
    import random
    outcomes = ([('W', 'W')] * 5 + [('W', 'L')] * 6 + [('L', 'W')]
                + [('L', 'L')] * 3 + [('D', 'D')]) * 3
    random.Random(20260907).shuffle(outcomes)
    rows = []
    for seed, pair in enumerate(outcomes, start=1000):
        for seat_a, outcome in enumerate(pair):
            agents = [agent_a, agent_b] if seat_a == 0 else [agent_b, agent_a]
            margin_a = (80 + seed % 23) * (1 if outcome == 'W' else -1 if outcome == 'L' else 0)
            margin = margin_a if seat_a == 0 else -margin_a
            winner = -1 if outcome == 'D' else seat_a if outcome == 'W' else 1 - seat_a
            rows.append({'seed': seed, 'agents': agents, 'winner': winner, 'margin': float(margin),
                         'rewards': [1000.0 + margin, 1000.0], 'statuses': ['DONE', 'DONE'],
                         'fault_counts': [{'ERROR': 0, 'INVALID': 0, 'TIMEOUT': 0} for _ in range(2)],
                         'config': {'seed': seed, 'scenario': 'constructed_demo_not_engine_configuration'},
                         'experiment_id': 'synthetic_teaching_example', 'data_kind': 'synthetic_demo'})
    return rows


if RESULTS_PATH == "":
    rows = make_demo_rows(AGENT_A, AGENT_B)
    input_file_sha256 = None
    input_origin = "constructed synthetic demo"
else:
    rows, input_file_sha256 = read_results(RESULTS_PATH)
    input_origin = "user-supplied local file"

report, per_seed, validated_rows = build_report(rows, AGENT_A, AGENT_B, n_boot=N_BOOT)
report["input_origin"] = input_origin
report["input_file_sha256_decompressed"] = input_file_sha256
report["statistics_source_sha256"] = "deeed3920edc0182787f6b3ee082639d08a6620ebaa0c4035b6bbeb3e135570a"
report["runtime"] = {"python": platform.python_version(), "pandas": pd.__version__,
                     "matplotlib": __import__("matplotlib").__version__}

IS_DEMO = report["data_kind"].startswith("synthetic")
LABEL = "SYNTHETIC DEMO" if IS_DEMO else "USER RESULTS / IDENTITY NOT INDEPENDENTLY VERIFIED"
print(LABEL)
print("Input rows:", report["input_audit"]["input_rows"])
print("Selected games:", report["games"], "| Complete seed pairs:", report["seed_pairs"])
print("Rows from other matchups:", report["input_audit"]["other_matchup_rows"])
print("Consistent provided metadata:", ", ".join(report["input_audit"]["checked_metadata"]) or "none")


lo, hi = report["score_ci95_percentile"]
summary = pd.DataFrame([
    ("Data", LABEL),
    ("Complete seed pairs", report["seed_pairs"]),
    ("Games", report["games"]),
    ("Wins / draws / losses", f'{report["wins"]} / {report["draws"]} / {report["losses"]}'),
    ("Raw win fraction", f'{report["raw_win_rate"]:.2%}'),
    ("Mean score (draw = 0.5)", f'{report["mean_score"]:.2%}'),
    ("Paired-score percentile interval", f'{lo:.2%} to {hi:.2%}'),
    ("Mean reward margin from A's perspective", report["mean_reward_margin"]),
    ("Pairs with complete margins", report["margin_seed_pairs"]),
], columns=["Measure", "Value"])
display(summary.set_index("Measure"))
print(report["interval_reading"])
print("\nAudit notes:")
for note in report["notices"]:
    print(" -", note)


fig = plt.figure(figsize=(9, 2.9))
ax = fig.add_subplot(111)
lo, hi = report["score_ci95_percentile"]
ax.plot([lo, hi], [0, 0], linewidth=3, label="95% percentile interval")
ax.plot([report["mean_score"]], [0], marker="o", markersize=9, linestyle="none", label="Mean score")
ax.axvline(0.5, linestyle="--", linewidth=1, label="Parity (0.5)")
ax.set_xlim(0, 1)
ax.set_ylim(-0.5, 0.5)
ax.set_yticks([])
ax.set_xlabel("A's draw-adjusted mean score")
ax.set_title(f"{LABEL} | Pair-level estimate, not a leaderboard forecast")
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.3), ncol=3)
fig.tight_layout()
plt.show()


seat_rows = []
for seat in (0, 1):
    item = report["seat_scores"][f"seat{seat}"]
    seat_rows.append({"A's seat": seat, "Games": item["n"], "Mean score": item["win_rate"],
                      "Percentile lower": item["ci95"][0], "Percentile upper": item["ci95"][1]})
seat_table = pd.DataFrame(seat_rows)
display(seat_table.set_index("A's seat").style.format({"Mean score": "{:.2%}",
        "Percentile lower": "{:.2%}", "Percentile upper": "{:.2%}"}))

fig = plt.figure(figsize=(8, 4))
ax = fig.add_subplot(111)
values = seat_table["Mean score"].tolist()
bars = ax.bar(["A in seat 0", "A in seat 1"], values, width=0.55)
ax.axhline(report["mean_score"], linestyle="--", linewidth=1, label=f'Both seats: {report["mean_score"]:.2%}')
for bar, value in zip(bars, values):
    ax.text(bar.get_x() + bar.get_width()/2, value + 0.025, f"{value:.2%}", ha="center")
ax.set_ylim(0, 1.05)
ax.set_ylabel("Draw-adjusted mean score")
ax.set_title(f"{LABEL} | Seat split")
ax.legend()
fig.tight_layout()
plt.show()


seed_table = pd.DataFrame([
    {"seed": seed, "mean_score": item["score"], "mean_reward_margin": item["margin"], "games": item["games"]}
    for seed, item in per_seed.items()
])
display(seed_table.head(12).set_index("seed"))

margins = [item["margin"] for item in per_seed.values() if item["margin"] is not None]
if margins:
    fig = plt.figure(figsize=(8, 4))
    ax = fig.add_subplot(111)
    ax.hist(margins, bins=min(15, max(1, len(set(margins)))))
    ax.axvline(0, linestyle="--", linewidth=1, label="Zero reward difference")
    ax.set_xlabel("Per-seed mean reward margin from A's perspective")
    ax.set_ylabel("Seed pairs")
    ax.set_title(f"{LABEL} | Margin coverage: {len(margins)}/{report['seed_pairs']} pairs")
    ax.legend()
    fig.tight_layout()
    plt.show()
else:
    print("No complete reward margins available. The score analysis remains available.")


import unittest

def _row(a, b, winner, seed, margin=100.0):
    return {"agents": [a, b], "winner": winner, "seed": seed,
            "margin": margin, "rewards": [0, 0]}


def _paired_rows(a, b, seeds, a_wins_both=True):
    rows = []
    for s in seeds:
        rows.append(_row(a, b, 0 if a_wins_both else 1, s, 50.0))
        rows.append(_row(b, a, 1 if a_wins_both else 0, s, -50.0))
    return rows


class TestBootstrap(unittest.TestCase):
    def test_constant_values(self):
        m, lo, hi = bootstrap_ci([1.0] * 20)
        self.assertEqual((m, lo, hi), (1.0, 1.0, 1.0))

    def test_deterministic(self):
        vals = [0.0, 0.5, 1.0, 1.0, 0.0, 0.5]
        self.assertEqual(bootstrap_ci(vals), bootstrap_ci(vals))

    def test_ci_brackets_mean(self):
        vals = [0.0, 1.0] * 25
        m, lo, hi = bootstrap_ci(vals)
        self.assertAlmostEqual(m, 0.5)
        self.assertLess(lo, 0.5)
        self.assertGreater(hi, 0.5)

    def test_paired_outcomes_scores(self):
        rows = _paired_rows("A", "B", [1, 2, 3])
        per_seed = paired_outcomes(rows, "A", "B")
        self.assertEqual(len(per_seed), 3)
        for d in per_seed.values():
            self.assertEqual(d["score"], 1.0)
            self.assertEqual(d["games"], 2)
            self.assertEqual(d["margin"], 50.0)

    def test_tie_scores_half(self):
        rows = [_row("A", "B", -1, 1, 0.0), _row("B", "A", -1, 1, 0.0)]
        per_seed = paired_outcomes(rows, "A", "B")
        self.assertEqual(per_seed[1]["score"], 0.5)

    def test_matchup_summary_counts(self):
        rows = _paired_rows("A", "B", range(10))
        s = matchup_summary(rows, "A", "B", n_boot=200)
        self.assertEqual(s["games"], 20)
        self.assertEqual(s["wins"], 20)
        self.assertEqual(s["win_rate"], 1.0)
        self.assertEqual(s["paired_seeds"], 10)

    def test_seat_split(self):
        # A wins only when seated first.
        rows = []
        for s in range(6):
            rows.append(_row("A", "B", 0, s))
            rows.append(_row("B", "A", 0, s))
        sp = seat_split(rows, "A", "B")
        self.assertEqual(sp["seat0"]["win_rate"], 1.0)
        self.assertEqual(sp["seat1"]["win_rate"], 0.0)


import copy
import tempfile
import unittest


class TestPublicationAdapter(unittest.TestCase):
    def sample(self):
        return make_demo_rows()[:4]

    def test_valid_balanced_input(self):
        rows, audit = validate_results(self.sample(), 'candidate', 'baseline')
        self.assertEqual((len(rows), audit['complete_seed_pairs']), (4, 2))

    def test_missing_seat_is_rejected(self):
        with self.assertRaises(ResultsError):
            validate_results(self.sample()[:-1], 'candidate', 'baseline')

    def test_duplicate_row_is_rejected(self):
        rows = self.sample()
        with self.assertRaises(ResultsError):
            validate_results(rows + [copy.deepcopy(rows[0])], 'candidate', 'baseline')

    def test_two_same_seats_are_not_a_pair(self):
        rows = self.sample()
        rows[1] = copy.deepcopy(rows[0])
        with self.assertRaises(ResultsError):
            validate_results(rows, 'candidate', 'baseline')

    def test_bad_winner_and_boolean_are_rejected(self):
        for value in (2, True, '0'):
            rows = self.sample()
            rows[0]['winner'] = value
            with self.assertRaises(ResultsError):
                validate_results(rows, 'candidate', 'baseline')

    def test_bad_seed_types_are_rejected(self):
        for value in ('1000', True, None):
            rows = self.sample()
            rows[0]['seed'] = value
            with self.assertRaises(ResultsError):
                validate_results(rows, 'candidate', 'baseline')

    def test_nonfinite_margin_is_rejected(self):
        for value in (float('nan'), float('inf'), True):
            rows = self.sample()
            rows[0]['margin'] = value
            with self.assertRaises(ResultsError):
                validate_results(rows, 'candidate', 'baseline')

    def test_winner_margin_disagreement_is_rejected(self):
        rows = self.sample()
        rows[0]['winner'] = 1 - rows[0]['winner']
        with self.assertRaises(ResultsError):
            validate_results(rows, 'candidate', 'baseline')

    def test_reward_margin_disagreement_is_rejected(self):
        rows = self.sample()
        rows[0]['rewards'][0] += 1.0
        with self.assertRaises(ResultsError):
            validate_results(rows, 'candidate', 'baseline')

    def test_recorded_fault_is_not_silently_dropped(self):
        rows = self.sample()
        rows[0]['fault_counts'][0]['ERROR'] = 1
        with self.assertRaises(ResultsError):
            validate_results(rows, 'candidate', 'baseline')

    def test_unfinished_episode_is_rejected(self):
        rows = self.sample()
        rows[0]['statuses'] = ['ACTIVE', 'ACTIVE']
        with self.assertRaises(ResultsError):
            validate_results(rows, 'candidate', 'baseline')

    def test_mixed_configuration_is_rejected(self):
        rows = self.sample()
        rows[0]['config']['scenario'] = 'different'
        with self.assertRaises(ResultsError):
            validate_results(rows, 'candidate', 'baseline')

    def test_configuration_seed_mismatch_is_rejected(self):
        rows = self.sample()
        rows[0]['config']['seed'] += 1
        with self.assertRaises(ResultsError):
            validate_results(rows, 'candidate', 'baseline')

    def test_mixed_engine_hash_is_rejected(self):
        rows = self.sample()
        for r in rows:
            r['engine_sha256'] = 'a' * 64
        rows[0]['engine_sha256'] = 'b' * 64
        with self.assertRaises(ResultsError):
            validate_results(rows, 'candidate', 'baseline')

    def test_partial_metadata_is_rejected(self):
        rows = self.sample()
        del rows[0]['config']
        with self.assertRaises(ResultsError):
            validate_results(rows, 'candidate', 'baseline')

    def test_missing_metadata_is_reported_not_invented(self):
        rows = [{k: r[k] for k in ('seed', 'agents', 'winner', 'margin')} for r in self.sample()]
        _, audit = validate_results(rows, 'candidate', 'baseline')
        self.assertTrue(any('engine_sha256: absent' in n for n in audit['notices']))
        self.assertEqual(audit['checked_metadata'], [])

    def test_one_sided_missing_margin_is_rejected(self):
        rows = self.sample()
        rows[0]['margin'] = None
        with self.assertRaises(ResultsError):
            validate_results(rows, 'candidate', 'baseline')

    def test_both_missing_margins_preserve_score_and_report_coverage(self):
        rows = self.sample()
        rows[0]['margin'] = rows[1]['margin'] = None
        report, _, _ = build_report(rows, 'candidate', 'baseline', 100)
        self.assertEqual(report['games'], 4)
        self.assertEqual(report['margin_seed_pairs'], 1)
        self.assertEqual(report['input_audit']['missing_margin_pairs'], 1)

    def test_row_order_does_not_change_report(self):
        rows = make_demo_rows()[:20]
        a, _, _ = build_report(rows, 'candidate', 'baseline', 100)
        b, _, _ = build_report(list(reversed(rows)), 'candidate', 'baseline', 100)
        self.assertEqual(a, b)

    def test_draw_score_is_not_raw_win_rate(self):
        rows = self.sample()
        for row in rows:
            row.update(winner=-1, margin=0.0, rewards=[1000.0, 1000.0])
        report, _, _ = build_report(rows, 'candidate', 'baseline', 100)
        self.assertEqual(report['mean_score'], 0.5)
        self.assertEqual(report['raw_win_rate'], 0.0)
        self.assertTrue(report['score_bootstrap_degenerate'])

    def test_empty_results_and_unknown_matchup_are_rejected(self):
        for rows, a, b in (([], 'A', 'B'), (self.sample(), 'unknown', 'baseline')):
            with self.assertRaises(ResultsError):
                validate_results(rows, a, b)

    def test_unrelated_matchup_rows_are_counted(self):
        rows = self.sample() + make_demo_rows('other_a', 'other_b')[:2]
        _, audit = validate_results(rows, 'candidate', 'baseline')
        self.assertEqual(audit['other_matchup_rows'], 2)
        self.assertEqual(audit['selected_rows'], 4)

    def test_jsonl_gzip_and_json_load_identically(self):
        rows = self.sample()
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / 'results.jsonl'
            text = '\n'.join(json.dumps(r) for r in rows) + '\n'
            p.write_text(text, encoding='utf-8')
            gz = Path(directory) / 'results.jsonl.gz'
            with gzip.open(gz, 'wt', encoding='utf-8') as h:
                h.write(text)
            j = Path(directory) / 'results.json'
            j.write_text(json.dumps(rows), encoding='utf-8')
            self.assertEqual(read_results(p)[0], rows)
            self.assertEqual(read_results(gz), read_results(p))
            self.assertEqual(read_results(j)[0], rows)

    def test_missing_file_never_falls_back_to_demo(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(FileNotFoundError):
                read_results(Path(directory) / 'absent.jsonl')

    def test_raw_replay_object_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / 'replay.json'
            p.write_text(json.dumps({'steps': []}), encoding='utf-8')
            with self.assertRaises(ResultsError):
                read_results(p)

    def test_nonfinite_json_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / 'results.json'
            p.write_text('[NaN]', encoding='utf-8')
            with self.assertRaises(ResultsError):
                read_results(p)

    def test_single_pair_does_not_claim_certainty(self):
        report, _, _ = build_report(self.sample()[:2], 'candidate', 'baseline', 100)
        self.assertTrue(report['score_bootstrap_degenerate'])
        self.assertIn('Descriptive only', report['interval_reading'])

    def test_resampling_budget_is_validated(self):
        for n in (0, True, 99, 50001):
            with self.assertRaises(ResultsError):
                build_report(self.sample(), 'candidate', 'baseline', n)

    def test_loading_size_limit_is_enforced(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / 'results.json'
            p.write_text('[1,2,3]', encoding='utf-8')
            with self.assertRaises(ResultsError):
                read_results(p, max_bytes=3)

    def test_agent_hashes_are_mapped_by_name_not_seat(self):
        rows = self.sample()
        for r in rows:
            r['agent_sha256'] = {'candidate': 'a'*64, 'baseline': 'b'*64}
        _, audit = validate_results(rows, 'candidate', 'baseline')
        self.assertIn('agent_sha256', audit['checked_metadata'])
        rows[1]['agent_sha256']['candidate'] = 'c'*64
        with self.assertRaises(ResultsError):
            validate_results(rows, 'candidate', 'baseline')

    def test_demo_counts_match_construction(self):
        report, _, _ = build_report(make_demo_rows(), 'candidate', 'baseline', 100)
        self.assertEqual((report['games'], report['seed_pairs']), (96, 48))
        self.assertEqual((report['wins'], report['draws'], report['losses']), (51, 6, 39))
        self.assertEqual(report['mean_score'], 0.5625)
        self.assertEqual(report['data_kind'], 'synthetic_demo')


import io
import unittest

suite = unittest.TestSuite()
for case in (TestBootstrap, TestPublicationAdapter):
    suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(case))
stream = io.StringIO()
test_result = unittest.TextTestRunner(stream=stream, verbosity=1).run(suite)
print(stream.getvalue())
assert test_result.wasSuccessful(), "Do not use this notebook until the failed tests are resolved."
report["self_tests"] = {"tests_run": test_result.testsRun, "failures": len(test_result.failures),
                       "errors": len(test_result.errors), "passed": test_result.wasSuccessful()}


OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
report_path = OUTPUT_DIR / "paired_evaluation_report.json"
report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
seed_table.to_csv(OUTPUT_DIR / "per_seed_results.csv", index=False)
if RESULTS_PATH == "":
    (OUTPUT_DIR / "synthetic_demo_results.jsonl").write_text(
        "\n".join(json.dumps(row, sort_keys=True, allow_nan=False) for row in rows) + "\n", encoding="utf-8")

# Verify the file we just wrote can be read back without losing its semantics.
roundtrip = json.loads(report_path.read_text(encoding="utf-8"))
assert roundtrip == report
print("Written files:")
for name in ("paired_evaluation_report.json", "per_seed_results.csv"):
    print(" -", name)
if RESULTS_PATH == "":
    print(" - synthetic_demo_results.jsonl (not real match data)")
print("Report round-trip: PASS | Notebook publication: NOT PERFORMED")
