"""Reproducible paired-seat benchmark over physical replay files.

Unlike the older route summary helper, this runner never deduplicates on the
action digest alone.  It records every file path and its raw-file digest, and
deduplicates execution only when actions, seed, explicit simulator overrides,
engine version, candidate bytes, and candidate seat are all identical.

Existing route-panel reports can be supplied for resumable coverage.  Their
results are reused only when candidate hash, engine, action digest, seed,
seat, and completion status match; the report records that the old report did
not independently store a configuration hash.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import gzip
import hashlib
import json
from pathlib import Path
from typing import Any

from kaggle_environments import __version__ as ENGINE_VERSION


EPISODE_STEPS = 720


def _json_digest(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _config(seed: int) -> dict[str, int]:
    # These are the explicit overrides passed by paired_benchmark.run_game;
    # all other settings are the defaults belonging to ENGINE_VERSION.
    return {"episodeSteps": EPISODE_STEPS, "seed": int(seed)}


def _execution_key(
    action_sha256: str,
    seed: int,
    configuration_sha256: str,
    engine_version: str,
    candidate_sha256: str,
    candidate_seat: int,
    candidate_settings_sha256: str | None = None,
) -> str:
    identity = [
        action_sha256,
        int(seed),
        configuration_sha256,
        engine_version,
        candidate_sha256,
        int(candidate_seat),
    ]
    # Preserve compatibility with prior baseline manifests (which used this
    # six-field identity); non-default ablations append their settings digest.
    if candidate_settings_sha256:
        identity.append(candidate_settings_sha256)
    return _json_digest(identity)


def _resolved(value: str | Path) -> str:
    return str(Path(value).resolve())


def _read_report_rows(report_path: Path) -> list[dict[str, Any]]:
    try:
        payload = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    rows = payload.get("rows", [])
    return rows if isinstance(rows, list) else []


def _load_prior_reports(
    report_paths: list[Path], candidate_sha256: str, candidate_overrides: dict[str, Any]
) -> tuple[dict[str, int], dict[str, dict[str, Any]], list[str]]:
    """Load seed hints for matching replays and reusable, completed game rows.

    Seeds belong to replay inputs, not agent candidates, so matching path/action
    records may provide seed hints across candidates. Scores remain reusable
    only for the exact same candidate and settings.
    """
    seed_by_path_and_actions: dict[tuple[str, str], int] = {}
    reusable: dict[str, dict[str, Any]] = {}
    used_reports: list[str] = []

    for report_path in report_paths:
        try:
            payload = json.loads(report_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        engine = str(payload.get("engine_version", ""))
        is_same_candidate = payload.get("candidate_sha256") == candidate_sha256
        # Variants/ablations are not reusable as the unmodified candidate.
        settings = payload.get("candidate_settings") or {}
        can_reuse = (
            is_same_candidate
            and engine == ENGINE_VERSION
            and not settings
            and not candidate_overrides
            and not payload.get("candidate_overrides")
        )

        # This runner's own manifest retains the complete execution key and
        # can be resumed without reinterpreting the old route-panel schema.
        manifest_routes = payload.get("routes")
        manifest_executions = payload.get("executions")
        if isinstance(manifest_routes, list) and isinstance(manifest_executions, dict):
            report_used = False
            for route in manifest_routes:
                if route.get("status") != "ready":
                    continue
                path_value = route.get("path")
                action_sha = str(route.get("action_sha256", ""))
                seed_value = route.get("seed")
                if not path_value or not action_sha or seed_value is None:
                    continue

                # A seed is independent of the candidate, but accept it only
                # for the same simulator version and exact path/action pair.
                if engine == ENGINE_VERSION:
                    seed = int(seed_value)
                    seed_by_path_and_actions[(_resolved(path_value), action_sha)] = seed
                    report_used = True

                if not can_reuse:
                    continue
                for seat_text, key in (route.get("execution_keys") or {}).items():
                    result = manifest_executions.get(key)
                    if not isinstance(result, dict):
                        continue
                    if (
                        result.get("candidate_status") != "DONE"
                        or result.get("opponent_status") != "DONE"
                        or int(result.get("frames", 0) or 0) < EPISODE_STEPS
                        or int(result.get("candidate_seat", -1)) != int(seat_text)
                        or result.get("configuration_sha256")
                        != route.get("configuration_sha256")
                    ):
                        continue
                    reusable.setdefault(key, result)
                    report_used = True
            if report_used:
                used_reports.append(_resolved(report_path))
            continue

        report_used = False
        for row in payload.get("rows", []) or []:
            path_value = row.get("opponent_path")
            action_sha = str(row.get("action_sha256", ""))
            seed_value = row.get("seed")
            if not path_value or not action_sha or seed_value is None:
                continue
            try:
                seed = int(seed_value)
                path_key = _resolved(path_value)
            except (TypeError, ValueError, OSError):
                continue
            if engine == ENGINE_VERSION:
                seed_by_path_and_actions[(path_key, action_sha)] = seed
                report_used = True
            if not can_reuse:
                continue
            configuration_sha = _json_digest(_config(seed))
            for game in row.get("games", []) or []:
                try:
                    seat = int(game["candidate_seat"])
                except (KeyError, TypeError, ValueError):
                    continue
                if (
                    int(game.get("frames", 0) or 0) < EPISODE_STEPS
                    or game.get("candidate_status") != "DONE"
                    or game.get("opponent_status") != "DONE"
                ):
                    continue
                key = _execution_key(
                    action_sha,
                    seed,
                    configuration_sha,
                    engine,
                    candidate_sha256,
                    seat,
                )
                reusable.setdefault(
                    key,
                    {
                        "execution_key": key,
                        "seed": seed,
                        "candidate_seat": seat,
                        "candidate_reward": float(game.get("candidate_reward", 0)),
                        "opponent_reward": float(game.get("opponent_reward", 0)),
                        "margin": float(game.get("margin", 0)),
                        "result": str(game.get("result", "UNKNOWN")),
                        "candidate_status": "DONE",
                        "opponent_status": "DONE",
                        "frames": int(game.get("frames", EPISODE_STEPS)),
                        "configuration_sha256": configuration_sha,
                        "evidence_source": "prior_report_inferred_config",
                        "source_report": _resolved(report_path),
                    },
                )
                report_used = True
        if report_used:
            used_reports.append(_resolved(report_path))
    return seed_by_path_and_actions, reusable, used_reports


def _discover_paths(directories: list[Path], explicit_paths: list[Path]) -> list[Path]:
    paths: set[Path] = set()
    for item in explicit_paths:
        paths.add(item.resolve())
    for directory in directories:
        if not directory.exists():
            raise FileNotFoundError(f"Replay directory does not exist: {directory}")
        paths.update(path.resolve() for path in directory.rglob("*.json.gz"))
    return sorted(path for path in paths if path.is_file())


def _make_route(path: Path, seed_hints: dict[tuple[str, str], int]) -> dict[str, Any]:
    raw_bytes = path.read_bytes()
    raw_sha = hashlib.sha256(raw_bytes).hexdigest()
    try:
        with gzip.open(path, "rt", encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, gzip.BadGzipFile, json.JSONDecodeError) as exc:
        return {
            "path": _resolved(path),
            "raw_file_sha256": raw_sha,
            "status": "invalid-file",
            "error": str(exc),
        }

    actions = payload.get("actions")
    metadata = payload.get("metadata") or {}
    if not isinstance(actions, list) or len(actions) != 719:
        return {
            "path": _resolved(path),
            "raw_file_sha256": raw_sha,
            "status": "invalid-action-count",
            "action_count": len(actions) if isinstance(actions, list) else None,
        }

    computed_action_sha = _json_digest(actions)
    metadata_action_sha = metadata.get("action_sha256")
    if metadata_action_sha and str(metadata_action_sha).lower() != computed_action_sha:
        return {
            "path": _resolved(path),
            "raw_file_sha256": raw_sha,
            "action_sha256": computed_action_sha,
            "status": "action-digest-mismatch",
            "metadata_action_sha256": str(metadata_action_sha),
        }

    seed = metadata.get("seed")
    seed_source = "replay_metadata"
    if seed is None:
        hint = seed_hints.get((_resolved(path), computed_action_sha))
        if hint is not None:
            seed = hint
            seed_source = "matching_prior_report"
    if seed is None:
        return {
            "path": _resolved(path),
            "raw_file_sha256": raw_sha,
            "action_sha256": computed_action_sha,
            "status": "unresolved-seed",
            "episode_id": metadata.get("episode_id"),
            "team": metadata.get("team") or metadata.get("opponent_team"),
            "source_engine_version": metadata.get("engine_version"),
        }

    seed = int(seed)
    config = _config(seed)
    config_sha = _json_digest(config)
    return {
        "path": _resolved(path),
        "raw_file_sha256": raw_sha,
        "action_sha256": computed_action_sha,
        "action_count": len(actions),
        "episode_id": metadata.get("episode_id"),
        "team": metadata.get("team") or metadata.get("opponent_team"),
        "source_seat": metadata.get("source_seat", metadata.get("seat")),
        "seed": seed,
        "seed_source": seed_source,
        "source_engine_version": metadata.get("engine_version"),
        "benchmark_engine_version": ENGINE_VERSION,
        "configuration_overrides": config,
        "configuration_sha256": config_sha,
        "status": "ready",
    }


def _play(job: tuple[str, str, str, int, int, str, str, dict[str, Any], str]) -> dict[str, Any]:
    (
        execution_key,
        candidate,
        route_path,
        seed,
        seat,
        config_sha,
        candidate_sha,
        candidate_overrides,
        candidate_settings_sha,
    ) = job
    from paired_benchmark import run_game

    result = run_game(
        candidate=candidate,
        opponent=f"rawroute:{route_path}",
        seed=seed,
        candidate_seat=seat,
        debug=False,
        capture_step=None,
        candidate_overrides=candidate_overrides,
    )
    result.update(
        execution_key=execution_key,
        candidate_sha256=candidate_sha,
        candidate_overrides=candidate_overrides,
        candidate_settings_sha256=candidate_settings_sha,
        engine_version=ENGINE_VERSION,
        configuration_sha256=config_sha,
        evidence_source="executed",
    )
    return result


def _summary(executions: dict[str, dict[str, Any]], routes: list[dict[str, Any]]) -> dict[str, Any]:
    complete = [
        result
        for result in executions.values()
        if result.get("candidate_status") == "DONE"
        and result.get("opponent_status") == "DONE"
        and int(result.get("frames", 0) or 0) >= EPISODE_STEPS
    ]
    route_pairs = 0
    route_pair_results = {"wins": 0, "draws": 0, "losses": 0}
    unresolved = 0
    for route in routes:
        if route.get("status") != "ready":
            unresolved += 1
            continue
        pair = [executions.get(route["execution_keys"][str(seat)]) for seat in (0, 1)]
        if any(
            result is None
            or result.get("candidate_status") != "DONE"
            or result.get("opponent_status") != "DONE"
            or int(result.get("frames", 0) or 0) < EPISODE_STEPS
            for result in pair
        ):
            continue
        route_pairs += 1
        margin = sum(float(result.get("margin", 0)) for result in pair if result)
        route_pair_results["wins" if margin > 0 else "losses" if margin < 0 else "draws"] += 1
    return {
        "physical_paths": len(routes),
        "path_pairs_completed": route_pairs,
        "unresolved_or_invalid_paths": unresolved,
        "unique_seat_executions": len(executions),
        "completed_seat_executions": len(complete),
        "seat_results": {
            "wins": sum(row.get("result") == "win" for row in complete),
            "draws": sum(row.get("result") == "draw" for row in complete),
            "losses": sum(row.get("result") == "loss" for row in complete),
        },
        "unique_route_pair_results": route_pair_results,
        "mean_margin": (
            sum(float(row.get("margin", 0)) for row in complete) / len(complete)
            if complete
            else None
        ),
    }


def _save(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", required=True, type=Path)
    parser.add_argument("--directories", nargs="*", type=Path, default=[])
    parser.add_argument("--paths", nargs="*", type=Path, default=[])
    parser.add_argument("--existing-reports", nargs="*", type=Path, default=[])
    parser.add_argument(
        "--candidate-override",
        action="append",
        default=[],
        metavar="NAME=JSON",
        help="Override a module setting, e.g. _ADV_BOOK=true; include in execution identity.",
    )
    parser.add_argument("--compare-manifests", nargs="*", type=Path, default=[])
    parser.add_argument("--json-out", required=True, type=Path)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--max-executions", type=int, default=0)
    parser.add_argument("--manifest-only", action="store_true")
    args = parser.parse_args()

    candidate_path = args.candidate.resolve()
    candidate_sha = hashlib.sha256(candidate_path.read_bytes()).hexdigest()
    candidate_overrides: dict[str, Any] = {}
    for item in args.candidate_override:
        if "=" not in item:
            parser.error(f"candidate override must be NAME=JSON, got {item!r}")
        name, raw_value = item.split("=", 1)
        try:
            candidate_overrides[name] = json.loads(raw_value)
        except json.JSONDecodeError as exc:
            parser.error(f"invalid JSON in candidate override {item!r}: {exc}")
    candidate_settings_sha = _json_digest(candidate_overrides) if candidate_overrides else ""
    seed_hints, reusable, used_reports = _load_prior_reports(
        [path.resolve() for path in args.existing_reports], candidate_sha, candidate_overrides
    )

    routes = [
        _make_route(path, seed_hints)
        for path in _discover_paths(args.directories, args.paths)
    ]
    for route in routes:
        if route.get("status") != "ready":
            continue
        keys = {}
        for seat in (0, 1):
            keys[str(seat)] = _execution_key(
                route["action_sha256"],
                route["seed"],
                route["configuration_sha256"],
                ENGINE_VERSION,
                candidate_sha,
                seat,
                candidate_settings_sha or None,
            )
        route["execution_keys"] = keys

    execution_aliases: dict[str, list[dict[str, Any]]] = {}
    for route in routes:
        if route.get("status") != "ready":
            continue
        for seat in (0, 1):
            key = route["execution_keys"][str(seat)]
            execution_aliases.setdefault(key, []).append(
                {"path": route["path"], "raw_file_sha256": route["raw_file_sha256"]}
            )

    executions = dict(reusable)
    if args.json_out.exists():
        try:
            prior = json.loads(args.json_out.read_text(encoding="utf-8"))
            if (
                prior.get("candidate_sha256") == candidate_sha
                and prior.get("engine_version") == ENGINE_VERSION
                and (prior.get("candidate_overrides") or {}) == candidate_overrides
            ):
                for key, result in (prior.get("executions") or {}).items():
                    if (
                        result.get("candidate_status") == "DONE"
                        and result.get("opponent_status") == "DONE"
                        and int(result.get("frames", 0) or 0) >= EPISODE_STEPS
                    ):
                        executions[key] = result
        except (OSError, json.JSONDecodeError):
            pass

    pending_keys = sorted(key for key in execution_aliases if key not in executions)
    if args.max_executions > 0:
        pending_keys = pending_keys[: args.max_executions]

    payload: dict[str, Any] = {
        "candidate": _resolved(candidate_path),
        "candidate_sha256": candidate_sha,
        "candidate_overrides": candidate_overrides,
        "candidate_settings_sha256": candidate_settings_sha,
        "engine_version": ENGINE_VERSION,
        "episode_steps": EPISODE_STEPS,
        "execution_identity_fields": [
            "canonical_action_sha256",
            "seed",
            "configuration_sha256",
            "engine_version",
            "candidate_sha256",
            "candidate_seat",
            *( ["candidate_settings_sha256"] if candidate_settings_sha else [] ),
        ],
        "raw_file_sha256_is_retained_per_path": True,
        "prior_reports_used_for_seeds_or_results": used_reports,
        "prior_report_configuration_note": (
            "Prior report results only record engine, seed, candidate hash, and 720 frames; "
            "their explicit configuration hash is inferred from paired_benchmark's "
            "episodeSteps=720 and seed overrides. New runs record the explicit-override hash."
        ),
        "routes": routes,
        "execution_aliases": execution_aliases,
        "executions": executions,
        "summary": _summary(executions, routes),
        "pending_unique_seat_executions": len(pending_keys),
        "manifest_only": bool(args.manifest_only),
        "complete": not pending_keys and all(route.get("status") == "ready" for route in routes),
    }

    if args.manifest_only:
        _save(args.json_out, payload)
        print(json.dumps({"manifest": str(args.json_out.resolve()), **payload["summary"]}, ensure_ascii=True))
        return

    _save(args.json_out, payload)
    jobs = []
    for key in pending_keys:
        route = next(
            route for route in routes
            if route.get("status") == "ready"
            and key in route.get("execution_keys", {}).values()
        )
        seat = int(next(seat for seat, value in route["execution_keys"].items() if value == key))
        jobs.append(
            (
                key,
                str(candidate_path),
                route["path"],
                int(route["seed"]),
                seat,
                route["configuration_sha256"],
                candidate_sha,
                candidate_overrides,
                candidate_settings_sha,
            )
        )

    if jobs:
        with concurrent.futures.ProcessPoolExecutor(max_workers=max(1, args.workers)) as pool:
            future_jobs = {pool.submit(_play, job): job for job in jobs}
            for index, future in enumerate(concurrent.futures.as_completed(future_jobs), start=1):
                result = future.result()
                executions[result["execution_key"]] = result
                payload["executions"] = executions
                payload["summary"] = _summary(executions, routes)
                payload["pending_unique_seat_executions"] = sum(
                    key not in executions for key in execution_aliases
                )
                payload["complete"] = (
                    payload["pending_unique_seat_executions"] == 0
                    and all(route.get("status") == "ready" for route in routes)
                )
                _save(args.json_out, payload)
                aliases = execution_aliases[result["execution_key"]]
                print(
                    f"[{index}/{len(jobs)}] seat={result['candidate_seat']} "
                    f"seed={result['seed']} margin={result['margin']:+.0f} "
                    f"{result['result']} aliases={len(aliases)} "
                    f"route={Path(aliases[0]['path']).name}",
                    flush=True,
                )

    payload["executions"] = executions
    payload["summary"] = _summary(executions, routes)
    payload["pending_unique_seat_executions"] = sum(
        key not in executions for key in execution_aliases
    )
    payload["complete"] = (
        payload["pending_unique_seat_executions"] == 0
        and all(route.get("status") == "ready" for route in routes)
    )
    payload["manifest_only"] = False
    comparisons = []
    for compare_path in args.compare_manifests:
        try:
            baseline = json.loads(compare_path.resolve().read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if (
            baseline.get("candidate_sha256") != candidate_sha
            or baseline.get("engine_version") != ENGINE_VERSION
        ):
            continue
        base_results = baseline.get("executions") or {}
        route_deltas = []
        for route in routes:
            if route.get("status") != "ready":
                continue
            base_pair = []
            alt_pair = []
            for seat in (0, 1):
                base_key = _execution_key(
                    route["action_sha256"], route["seed"], route["configuration_sha256"],
                    ENGINE_VERSION, candidate_sha, seat,
                )
                alt_key = route["execution_keys"][str(seat)]
                base_pair.append(base_results.get(base_key))
                alt_pair.append(executions.get(alt_key))
            if any(x is None for x in base_pair + alt_pair):
                continue
            base_margin = sum(float(x.get("margin", 0)) for x in base_pair)
            alt_margin = sum(float(x.get("margin", 0)) for x in alt_pair)
            route_deltas.append({
                "path": route["path"],
                "team": route.get("team"),
                "seed": route["seed"],
                "baseline_pair_margin": base_margin,
                "variant_pair_margin": alt_margin,
                "improvement": alt_margin - base_margin,
                "baseline_seat_results": [x.get("result") for x in base_pair],
                "variant_seat_results": [x.get("result") for x in alt_pair],
            })
        comparisons.append({
            "baseline_manifest": _resolved(compare_path),
            "routes_compared": len(route_deltas),
            "mean_pair_margin_improvement": (
                sum(row["improvement"] for row in route_deltas) / len(route_deltas)
                if route_deltas else None
            ),
            "routes_improved": sum(row["improvement"] > 0 for row in route_deltas),
            "routes_regressed": sum(row["improvement"] < 0 for row in route_deltas),
            "routes_tied": sum(row["improvement"] == 0 for row in route_deltas),
            "route_deltas": route_deltas,
        })
    payload["comparisons"] = comparisons
    _save(args.json_out, payload)
    print("SUMMARY " + json.dumps(payload["summary"], sort_keys=True))
    print(f"manifest={args.json_out.resolve()} complete={payload['complete']}")


if __name__ == "__main__":
    main()
