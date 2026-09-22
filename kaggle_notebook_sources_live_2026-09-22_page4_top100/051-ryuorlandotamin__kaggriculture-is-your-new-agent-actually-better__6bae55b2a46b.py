from __future__ import annotations

import math
from collections.abc import Iterable

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import norm

RNG_SEED = 20260812
pd.set_option("display.max_columns", 30)
pd.set_option("display.float_format", lambda value: f"{value:,.4f}")


def make_dummy_panel(seed: int = RNG_SEED) -> pd.DataFrame:
    """Create a small correlated panel for a baseline and a challenger."""
    rng = np.random.default_rng(seed)
    families = [f"family_{index:02d}" for index in range(1, 13)]
    family_difficulty = dict(
        zip(families, rng.normal(0.0, 0.55, len(families)), strict=True)
    )
    challenger_interaction = {
        family: rng.normal(0.0, 0.16) for family in families
    }
    challenger_interaction["family_11"] = -0.70

    rows = []
    for random_seed in range(10_000, 10_040):
        seed_shock = rng.normal(0.0, 0.45)
        for family in families:
            for seat in (0, 1):
                seat_effect = 0.14 if seat == 1 else -0.14
                shared_match_noise = rng.normal(0.0, 0.20)

                for agent, uplift in (("baseline", 0.00), ("challenger", 0.52)):
                    interaction = (
                        challenger_interaction[family]
                        if agent == "challenger"
                        else 0.0
                    )
                    latent = (
                        -0.08
                        - family_difficulty[family]
                        + seat_effect
                        + seed_shock
                        + shared_match_noise
                        + uplift
                        + interaction
                        + rng.normal(0.0, 0.10)
                    )

                    if latent > 0.22:
                        score = 1.0
                    elif latent < -0.22:
                        score = 0.0
                    else:
                        score = 0.5

                    margin = 8_000 * (latent + rng.normal(0.0, 0.25))
                    latency = max(0.05, rng.lognormal(1.5, 0.35))
                    rows.append(
                        {
                            "agent": agent,
                            "family": family,
                            "seed": random_seed,
                            "seat": seat,
                            "score": score,
                            "margin": float(margin),
                            "status": "DONE",
                            "latency_ms": float(latency),
                            "data_time": "2026-08-01",
                        }
                    )

    return pd.DataFrame(rows)


games = make_dummy_panel()
print(games.shape)
games.head()


def audit_design(frame: pd.DataFrame) -> dict[str, object]:
    required = {
        "agent", "family", "seed", "seat", "score",
        "margin", "status", "latency_ms", "data_time",
    }
    missing_columns = sorted(required - set(frame.columns))
    if missing_columns:
        return {"missing_columns": missing_columns}

    key = ["agent", "family", "seed", "seat"]
    duplicates = int(frame.duplicated(key).sum())
    allowed_scores = frame["score"].isin([0.0, 0.5, 1.0])
    agent_count = frame["agent"].nunique()
    coverage = frame.groupby(["family", "seed", "seat"])["agent"].nunique()

    return {
        "missing_columns": [],
        "duplicate_cells": duplicates,
        "invalid_scores": int((~allowed_scores).sum()),
        "agents": agent_count,
        "behavioral_families": frame["family"].nunique(),
        "unique_seeds": frame["seed"].nunique(),
        "seats": sorted(frame["seat"].unique().tolist()),
        "incomplete_shared_cells": int((coverage != agent_count).sum()),
        "runtime_failures": int((frame["status"] != "DONE").sum()),
        "games_per_agent": frame.groupby("agent").size().to_dict(),
    }


audit_design(games)


def point_summary(frame: pd.DataFrame, agent: str) -> dict[str, object]:
    sample = frame.loc[frame["agent"] == agent].copy()
    family_scores = sample.groupby("family")["score"].mean().sort_values()
    tail_count = max(1, math.ceil(0.10 * len(family_scores)))
    seat_scores = sample.groupby("seat")["score"].mean()

    return {
        "games": len(sample),
        "score": sample["score"].mean(),
        "mean_margin": sample["margin"].mean(),
        "weakest_family_score": family_scores.iloc[0],
        "lower_tail_family_mean_10pct": family_scores.iloc[:tail_count].mean(),
        "seat_scores": seat_scores.to_dict(),
        "seat_gap": seat_scores.max() - seat_scores.min(),
        "runtime_failures": int((sample["status"] != "DONE").sum()),
        "latency_p99_ms": sample["latency_ms"].quantile(0.99),
    }


pd.DataFrame(
    {name: point_summary(games, name) for name in ["baseline", "challenger"]}
).T


def outcome_counts(scores: Iterable[float]) -> np.ndarray:
    values = np.asarray(list(scores), dtype=float)
    if not np.isin(values, [0.0, 0.5, 1.0]).all():
        raise ValueError("Scores must be 0, 0.5, or 1")
    return np.array(
        [
            np.sum(values == 1.0),
            np.sum(values == 0.5),
            np.sum(values == 0.0),
        ],
        dtype=float,
    )


def dirichlet_score_posterior(
    scores: Iterable[float],
    threshold: float = 0.50,
    prior: tuple[float, float, float] = (0.5, 0.5, 0.5),
    draws: int = 30_000,
    seed: int = RNG_SEED,
) -> dict[str, float]:
    counts = outcome_counts(scores)
    rng = np.random.default_rng(seed)
    posterior = rng.dirichlet(counts + np.asarray(prior), size=draws)
    point_score = posterior[:, 0] + 0.5 * posterior[:, 1]

    return {
        "wins": int(counts[0]),
        "draws": int(counts[1]),
        "losses": int(counts[2]),
        "observed_score": float((counts[0] + 0.5 * counts[1]) / counts.sum()),
        "posterior_mean_score": float(point_score.mean()),
        "credible_low_95": float(np.quantile(point_score, 0.025)),
        "credible_high_95": float(np.quantile(point_score, 0.975)),
        "probability_above_threshold": float((point_score > threshold).mean()),
    }


small_example = [1.0] * 8 + [0.0] * 2
pd.Series(dirichlet_score_posterior(small_example, threshold=0.60))


def posterior_predictive_batch(
    scores: Iterable[float],
    future_games: int = 50,
    draws: int = 20_000,
    seed: int = RNG_SEED,
) -> dict[str, float]:
    counts = outcome_counts(scores)
    rng = np.random.default_rng(seed)
    theta = rng.dirichlet(counts + 0.5, size=draws)

    uniforms = rng.random((draws, future_games))
    win_cut = theta[:, 0, None]
    draw_cut = (theta[:, 0] + theta[:, 1])[:, None]
    future_wins = (uniforms < win_cut).sum(axis=1)
    future_draws = ((uniforms >= win_cut) & (uniforms < draw_cut)).sum(axis=1)
    future_score = (future_wins + 0.5 * future_draws) / future_games

    return {
        "expected_future_score": float(future_score.mean()),
        "predictive_low_90": float(np.quantile(future_score, 0.05)),
        "predictive_high_90": float(np.quantile(future_score, 0.95)),
        "probability_next_batch_above_65pct": float((future_score >= 0.65).mean()),
    }


challenger_scores = games.loc[games["agent"] == "challenger", "score"]
posterior_predictive_batch(challenger_scores, future_games=50)


def paired_table(
    frame: pd.DataFrame,
    challenger: str,
    baseline: str,
) -> pd.DataFrame:
    key = ["agent", "family", "seed", "seat"]
    if frame.duplicated(key).any():
        raise ValueError("Duplicate agent, family, seed, seat cells found")

    wide = frame.pivot(
        index=["family", "seed", "seat"],
        columns="agent",
        values=["score", "margin"],
    )
    required = [
        ("score", challenger),
        ("score", baseline),
        ("margin", challenger),
        ("margin", baseline),
    ]
    if any(column not in wide.columns for column in required):
        raise ValueError("Challenger and baseline do not share the required matrix")

    paired = wide.loc[:, required].copy()
    if paired.isna().any().any():
        raise ValueError("Incomplete paired matrix. Repair coverage before inference")

    paired.columns = [
        "challenger_score",
        "baseline_score",
        "challenger_margin",
        "baseline_margin",
    ]
    paired["score_delta"] = paired["challenger_score"] - paired["baseline_score"]
    paired["margin_delta"] = paired["challenger_margin"] - paired["baseline_margin"]
    return paired.reset_index()


paired = paired_table(games, "challenger", "baseline")
paired[["score_delta", "margin_delta"]].describe()


def paired_dirichlet_posterior(
    paired_frame: pd.DataFrame,
    minimum_effect: float = 0.02,
    prior_per_joint_cell: float = 0.5,
    draws: int = 40_000,
    seed: int = RNG_SEED,
) -> dict[str, float]:
    levels = np.array([0.0, 0.5, 1.0])
    counts = np.zeros((3, 3), dtype=float)

    for challenger_score, baseline_score in paired_frame[
        ["challenger_score", "baseline_score"]
    ].itertuples(index=False):
        challenger_match = np.where(levels == challenger_score)[0]
        baseline_match = np.where(levels == baseline_score)[0]
        if len(challenger_match) != 1 or len(baseline_match) != 1:
            raise ValueError("Scores must be 0, 0.5, or 1")
        counts[challenger_match[0], baseline_match[0]] += 1

    rng = np.random.default_rng(seed)
    posterior = rng.dirichlet(
        counts.reshape(-1) + prior_per_joint_cell,
        size=draws,
    )
    delta_grid = (levels[:, None] - levels[None, :]).reshape(-1)
    uplift = posterior @ delta_grid

    return {
        "observed_mean_uplift": float(paired_frame["score_delta"].mean()),
        "posterior_mean_uplift": float(uplift.mean()),
        "credible_low_95": float(np.quantile(uplift, 0.025)),
        "credible_high_95": float(np.quantile(uplift, 0.975)),
        "probability_challenger_better": float((uplift > 0).mean()),
        "probability_practically_better": float((uplift > minimum_effect).mean()),
    }


paired_bayes = paired_dirichlet_posterior(paired, minimum_effect=0.02)
pd.Series(paired_bayes)


def seed_cluster_bootstrap(
    paired_frame: pd.DataFrame,
    value: str = "score_delta",
    repetitions: int = 10_000,
    seed: int = RNG_SEED,
) -> dict[str, float]:
    counts_per_seed = paired_frame.groupby("seed").size()
    if counts_per_seed.nunique() != 1:
        raise ValueError("Each seed must contain the same fixed family and seat panel")

    seed_means = paired_frame.groupby("seed")[value].mean().to_numpy(dtype=float)
    rng = np.random.default_rng(seed)
    sampled = rng.choice(
        seed_means,
        size=(repetitions, len(seed_means)),
        replace=True,
    )
    estimates = sampled.mean(axis=1)

    return {
        "point": float(seed_means.mean()),
        "one_sided_95_lcb": float(np.quantile(estimates, 0.05)),
        "two_sided_low_95": float(np.quantile(estimates, 0.025)),
        "two_sided_high_95": float(np.quantile(estimates, 0.975)),
        "bootstrap_standard_error": float(estimates.std(ddof=1)),
        "independent_seed_units": int(len(seed_means)),
    }


seed_bootstrap = seed_cluster_bootstrap(paired, "score_delta")
pd.Series(seed_bootstrap)


pd.DataFrame(
    {
        "paired Bayesian model": {
            "estimate": paired_bayes["posterior_mean_uplift"],
            "low": paired_bayes["credible_low_95"],
            "high": paired_bayes["credible_high_95"],
        },
        "seed cluster bootstrap": {
            "estimate": seed_bootstrap["point"],
            "low": seed_bootstrap["two_sided_low_95"],
            "high": seed_bootstrap["two_sided_high_95"],
        },
    }
).T


def empirical_bayes_family_scores(
    frame: pd.DataFrame,
    agent: str,
    prior_strength: float = 12.0,
    threshold: float = 0.50,
    draws: int = 20_000,
    seed: int = RNG_SEED,
) -> pd.DataFrame:
    if prior_strength <= 0:
        raise ValueError("prior_strength must be positive")

    sample = frame.loc[frame["agent"] == agent].copy()
    global_counts = outcome_counts(sample["score"])
    global_proportions = (global_counts + 0.5) / (global_counts.sum() + 1.5)
    prior_alpha = prior_strength * global_proportions

    rng = np.random.default_rng(seed)
    rows = []
    for family, family_frame in sample.groupby("family"):
        counts = outcome_counts(family_frame["score"])
        posterior = rng.dirichlet(prior_alpha + counts, size=draws)
        score_draws = posterior[:, 0] + 0.5 * posterior[:, 1]
        rows.append(
            {
                "family": family,
                "games": int(counts.sum()),
                "raw_score": float(family_frame["score"].mean()),
                "posterior_mean": float(score_draws.mean()),
                "posterior_sd": float(score_draws.std(ddof=1)),
                "credible_low_95": float(np.quantile(score_draws, 0.025)),
                "credible_high_95": float(np.quantile(score_draws, 0.975)),
                "probability_above_threshold": float((score_draws > threshold).mean()),
            }
        )

    return pd.DataFrame(rows).sort_values("posterior_mean").reset_index(drop=True)


family_posterior = empirical_bayes_family_scores(games, "challenger")
family_posterior


def plot_family_shrinkage(result: pd.DataFrame) -> None:
    ordered = result.sort_values("posterior_mean").reset_index(drop=True)
    y = np.arange(len(ordered))
    lower_error = ordered["posterior_mean"] - ordered["credible_low_95"]
    upper_error = ordered["credible_high_95"] - ordered["posterior_mean"]

    fig, ax = plt.subplots(figsize=(9, 6))
    ax.errorbar(
        ordered["posterior_mean"],
        y,
        xerr=np.vstack([lower_error, upper_error]),
        fmt="o",
        capsize=3,
        label="Empirical Bayes estimate",
    )
    ax.scatter(ordered["raw_score"], y, marker="x", label="Raw score")
    ax.axvline(0.50, linewidth=1, linestyle="--")
    ax.set_yticks(y, ordered["family"])
    ax.set_xlabel("Point score")
    ax.set_title("Small family results should look uncertain")
    ax.legend()
    plt.tight_layout()
    plt.show()


plot_family_shrinkage(family_posterior)


def family_allocation_priority(
    frame: pd.DataFrame,
    agent: str,
    decision_boundary: float = 0.50,
    prior_strength: float = 12.0,
) -> pd.DataFrame:
    result = empirical_bayes_family_scores(
        frame,
        agent,
        prior_strength=prior_strength,
        threshold=decision_boundary,
    ).copy()

    probability_above = result["probability_above_threshold"]
    boundary_uncertainty = 1.0 - np.abs(2.0 * probability_above - 1.0)
    result["allocation_priority"] = result["posterior_sd"] * boundary_uncertainty

    total_priority = result["allocation_priority"].sum()
    if total_priority > 0:
        result["suggested_share_of_next_batch"] = (
            result["allocation_priority"] / total_priority
        )
    else:
        result["suggested_share_of_next_batch"] = 1.0 / len(result)

    return result.sort_values("allocation_priority", ascending=False).reset_index(drop=True)


family_allocation_priority(games, "challenger").head(6)


def approximate_seeds_needed(
    paired_frame: pd.DataFrame,
    value: str = "score_delta",
    half_width: float = 0.02,
    confidence: float = 0.95,
) -> dict[str, float]:
    if half_width <= 0:
        raise ValueError("half_width must be positive")

    seed_means = paired_frame.groupby("seed")[value].mean()
    if len(seed_means) < 2:
        raise ValueError("At least two independent seeds are required")

    seed_sd = float(seed_means.std(ddof=1))
    z_value = float(norm.ppf(0.5 + confidence / 2.0))
    required = math.ceil((z_value * seed_sd / half_width) ** 2)

    return {
        "current_seeds": int(len(seed_means)),
        "pilot_seed_sd": seed_sd,
        "target_half_width": half_width,
        "approximate_required_seeds": int(required),
        "approximate_additional_seeds": int(max(0, required - len(seed_means))),
    }


approximate_seeds_needed(paired, half_width=0.02)


def holm_adjust(p_values: dict[str, float]) -> pd.DataFrame:
    ordered = sorted(p_values.items(), key=lambda item: item[1])
    total = len(ordered)
    running_max = 0.0
    rows = []

    for rank, (name, p_value) in enumerate(ordered, start=1):
        adjusted = min(1.0, (total - rank + 1) * p_value)
        running_max = max(running_max, adjusted)
        rows.append(
            {
                "hypothesis": name,
                "raw_p": p_value,
                "holm_p": running_max,
            }
        )

    return pd.DataFrame(rows).sort_values("hypothesis").reset_index(drop=True)


holm_adjust(
    {
        "family_A": 0.004,
        "family_B": 0.020,
        "family_C": 0.041,
        "family_D": 0.40,
    }
)


def promotion_report(
    frame: pd.DataFrame,
    challenger: str,
    baseline: str,
    minimum_effect: float = 0.02,
    required_probability: float = 0.95,
) -> dict[str, object]:
    paired_frame = paired_table(frame, challenger, baseline)
    bayes_result = paired_dirichlet_posterior(
        paired_frame,
        minimum_effect=minimum_effect,
    )
    bootstrap_result = seed_cluster_bootstrap(paired_frame, "score_delta")
    failures = int(
        (
            frame.loc[frame["agent"] == challenger, "status"]
            != "DONE"
        ).sum()
    )

    checks = {
        "posterior_practical_gain": (
            bayes_result["probability_practically_better"] >= required_probability
        ),
        "seed_bootstrap_lcb_positive": bootstrap_result["one_sided_95_lcb"] > 0,
        "no_runtime_failures": failures == 0,
    }

    return {
        "decision": "PROMOTE" if all(checks.values()) else "KEEP TESTING",
        "minimum_effect": minimum_effect,
        "required_probability": required_probability,
        "probability_practically_better": bayes_result[
            "probability_practically_better"
        ],
        "seed_bootstrap_one_sided_95_lcb": bootstrap_result[
            "one_sided_95_lcb"
        ],
        "runtime_failures": failures,
        "checks": checks,
    }


promotion_report(games, "challenger", "baseline")


REAL_EXPERIMENT = {
    "paired_cells": 240,
    "families": 30,
    "shared_seeds": 4,
    "version_1_score": 0.4458,
    "version_2_score": 0.8917,
    "score_uplift": 0.4459,
    "improved_cells": 110,
    "unchanged_cells": 127,
    "regressed_cells": 3,
    "mean_margin_uplift": 4564.7,
    "families_improved": 24,
    "families_unchanged": 5,
    "families_regressed": 1,
    "version_2_worst_family": 0.50,
    "version_2_seat_0": 0.8917,
    "version_2_seat_1": 0.8917,
}

assert (
    REAL_EXPERIMENT["improved_cells"]
    + REAL_EXPERIMENT["unchanged_cells"]
    + REAL_EXPERIMENT["regressed_cells"]
    == REAL_EXPERIMENT["paired_cells"]
)
assert (
    REAL_EXPERIMENT["families_improved"]
    + REAL_EXPERIMENT["families_unchanged"]
    + REAL_EXPERIMENT["families_regressed"]
    == REAL_EXPERIMENT["families"]
)

real_summary = pd.DataFrame(
    [
        {
            "metric": "Point score",
            "Version 1": REAL_EXPERIMENT["version_1_score"],
            "Version 2": REAL_EXPERIMENT["version_2_score"],
            "change": REAL_EXPERIMENT["score_uplift"],
        },
        {
            "metric": "Seat 0 score",
            "Version 1": np.nan,
            "Version 2": REAL_EXPERIMENT["version_2_seat_0"],
            "change": np.nan,
        },
        {
            "metric": "Seat 1 score",
            "Version 1": np.nan,
            "Version 2": REAL_EXPERIMENT["version_2_seat_1"],
            "change": np.nan,
        },
        {
            "metric": "Worst family score",
            "Version 1": np.nan,
            "Version 2": REAL_EXPERIMENT["version_2_worst_family"],
            "change": np.nan,
        },
    ]
)

real_summary.style.format(
    {
        "Version 1": lambda x: "" if pd.isna(x) else f"{100*x:.2f}%",
        "Version 2": lambda x: "" if pd.isna(x) else f"{100*x:.2f}%",
        "change": lambda x: "" if pd.isna(x) else f"{100*x:+.2f} pp",
    }
)


def plot_real_score_comparison(result: dict[str, float]) -> None:
    labels = ["Version 1", "Version 2"]
    values = [result["version_1_score"], result["version_2_score"]]

    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    bars = ax.bar(labels, values, width=0.58)
    ax.axhline(0.50, linewidth=1, linestyle="--")
    ax.set_ylim(0, 1)
    ax.set_ylabel("Point score")
    ax.set_title("Point score on the same evaluation panel")
    ax.yaxis.set_major_formatter(lambda x, pos: f"{100*x:.0f}%")

    for bar, value in zip(bars, values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            value + 0.025,
            f"{100*value:.2f}%",
            ha="center",
            va="bottom",
        )

    ax.text(
        0.5,
        0.08,
        f"paired uplift  {100*result['score_uplift']:+.2f} percentage points",
        transform=ax.transAxes,
        ha="center",
    )
    plt.tight_layout()
    plt.show()


plot_real_score_comparison(REAL_EXPERIMENT)


def plot_real_paired_changes(result: dict[str, float]) -> None:
    labels = ["Improved", "Unchanged", "Regressed"]
    counts = [
        result["improved_cells"],
        result["unchanged_cells"],
        result["regressed_cells"],
    ]

    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    bars = ax.barh(labels, counts)
    ax.set_xlabel("Paired cells")
    ax.set_title("What changed across the 240 paired cells")

    for bar, count in zip(bars, counts):
        ax.text(
            count + 2,
            bar.get_y() + bar.get_height() / 2,
            str(count),
            va="center",
        )

    ax.set_xlim(0, max(counts) * 1.15)
    plt.tight_layout()
    plt.show()


discordant = REAL_EXPERIMENT["improved_cells"] + REAL_EXPERIMENT["regressed_cells"]
share_favoring_v2 = REAL_EXPERIMENT["improved_cells"] / discordant
print(f"Changed cells favoring Version 2: {100*share_favoring_v2:.2f}%")
plot_real_paired_changes(REAL_EXPERIMENT)


def paired_change_direction_posterior(
    improved: int,
    unchanged: int,
    regressed: int,
    prior: tuple[float, float, float] = (0.5, 0.5, 0.5),
    draws: int = 80_000,
    seed: int = RNG_SEED,
) -> tuple[pd.Series, np.ndarray]:
    counts = np.array([improved, unchanged, regressed], dtype=float)
    rng = np.random.default_rng(seed)
    posterior = rng.dirichlet(counts + np.asarray(prior), size=draws)
    net_direction = posterior[:, 0] - posterior[:, 2]

    summary = pd.Series(
        {
            "posterior_mean_improved": posterior[:, 0].mean(),
            "posterior_mean_unchanged": posterior[:, 1].mean(),
            "posterior_mean_regressed": posterior[:, 2].mean(),
            "probability_improve_rate_above_regress_rate": (
                posterior[:, 0] > posterior[:, 2]
            ).mean(),
            "net_direction_low_95": np.quantile(net_direction, 0.025),
            "net_direction_high_95": np.quantile(net_direction, 0.975),
        }
    )
    return summary, posterior


real_direction_summary, real_direction_draws = paired_change_direction_posterior(
    REAL_EXPERIMENT["improved_cells"],
    REAL_EXPERIMENT["unchanged_cells"],
    REAL_EXPERIMENT["regressed_cells"],
)

real_direction_summary


def plot_change_direction_posterior(draws: np.ndarray) -> None:
    names = ["Improved", "Unchanged", "Regressed"]
    means = draws.mean(axis=0)
    lows = np.quantile(draws, 0.025, axis=0)
    highs = np.quantile(draws, 0.975, axis=0)
    positions = np.arange(len(names))

    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    ax.errorbar(
        means,
        positions,
        xerr=np.vstack([means - lows, highs - means]),
        fmt="o",
        capsize=4,
    )
    ax.set_yticks(positions, names)
    ax.set_xlim(0, 0.65)
    ax.set_xlabel("Posterior probability of a cell category")
    ax.set_title("Dirichlet summary of change direction")
    ax.xaxis.set_major_formatter(lambda x, pos: f"{100*x:.0f}%")
    plt.tight_layout()
    plt.show()


plot_change_direction_posterior(real_direction_draws)


def plot_real_family_changes(result: dict[str, float]) -> None:
    labels = ["Improved", "Unchanged", "Regressed"]
    counts = [
        result["families_improved"],
        result["families_unchanged"],
        result["families_regressed"],
    ]

    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    bars = ax.bar(labels, counts)
    ax.set_ylabel("Opponent families")
    ax.set_title("Direction of change across 30 opponent families")

    for bar, count in zip(bars, counts):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            count + 0.45,
            str(count),
            ha="center",
        )

    ax.set_ylim(0, max(counts) * 1.15)
    plt.tight_layout()
    plt.show()


plot_real_family_changes(REAL_EXPERIMENT)


LIVE_SCORE_SNAPSHOT = {
    "date": "2026-08-12",
    "Version 1": 2823.6,
    "Version 2": 3032.5,
}

live_gap = LIVE_SCORE_SNAPSHOT["Version 2"] - LIVE_SCORE_SNAPSHOT["Version 1"]

pd.Series(
    {
        "Version 1 live score": LIVE_SCORE_SNAPSHOT["Version 1"],
        "Version 2 live score": LIVE_SCORE_SNAPSHOT["Version 2"],
        "absolute gap": live_gap,
    }
)

def plot_live_score_snapshot(snapshot: dict[str, float | str]) -> None:
    labels = ["Version 1", "Version 2"]
    values = [float(snapshot[label]) for label in labels]
    gap = values[1] - values[0]

    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    bars = ax.bar(labels, values, width=0.58)
    ax.set_ylabel("Live Kaggriculture score")
    ax.set_title(f"Live score snapshot on {snapshot['date']}")

    ax.set_ylim(0, max(values) * 1.10)

    for bar, value in zip(bars, values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            value + 22,
            f"{value:.1f}",
            ha="center",
            va="bottom",
        )

    ax.text(
        0.5,
        0.08,
        f"observed gap  {gap:+.1f} points",
        transform=ax.transAxes,
        ha="center",
    )
    plt.tight_layout()
    plt.show()


plot_live_score_snapshot(LIVE_SCORE_SNAPSHOT)

# Example Kaggle path
# real_games = pd.read_csv("/kaggle/input/your-agent-evaluation/games.csv")
# print(audit_design(real_games))
# real_paired = paired_table(real_games, "challenger_hash", "baseline_hash")
# print(paired_dirichlet_posterior(real_paired, minimum_effect=0.02))
# print(seed_cluster_bootstrap(real_paired, "score_delta"))
# display(empirical_bayes_family_scores(real_games, "challenger_hash"))
# display(family_allocation_priority(real_games, "challenger_hash"))

EXPECTED_COLUMNS = [
    "agent",
    "family",
    "seed",
    "seat",
    "score",
    "margin",
    "status",
    "latency_ms",
    "data_time",
]

pd.DataFrame(columns=EXPECTED_COLUMNS)
