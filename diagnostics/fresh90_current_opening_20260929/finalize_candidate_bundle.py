"""Freeze final candidate manifest and deterministic hash list."""
from __future__ import annotations
import hashlib, json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE_SUMMARY = HERE.parents[0] / 'fresh90_refresh_20260929' / 'routes' / 'development_latest' / 'summary.json'

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main() -> None:
    analysis = json.loads((HERE / 'family_analysis.json').read_text(encoding='utf-8'))
    validation = json.loads((HERE / 'candidate_validation.json').read_text(encoding='utf-8'))
    melon = json.loads((HERE / 'melon_support.json').read_text(encoding='utf-8'))
    plan_sha = sha(HERE / 'PLAN.md')
    source_sha = sha(SOURCE_SUMMARY)
    if plan_sha != (HERE / 'PLAN_SHA256.txt').read_text(encoding='utf-8').split()[0].lower():
        raise RuntimeError('frozen plan hash mismatch')
    if source_sha != analysis['source_summary_sha256'] or source_sha != validation['source_summary_sha256']:
        raise RuntimeError('frozen source summary hash mismatch')
    if validation['checks']['game_runs'] != 0 or validation['checks']['outcome_fields_used']:
        raise RuntimeError('validation receipt has unexpected game or outcome use')

    validated_by_key = {}
    for candidate in validation['candidate_results']:
        for source in candidate['embedded_tapes']:
            key = (int(source['rank']), int(source['episode_id']))
            validated_by_key[key] = source

    all_families = analysis['all_multi_tape_families']
    family_by_rank_set = {tuple(sorted(int(rank) for rank in family['member_ranks'])): family
                          for family in all_families}
    # Keep the count derived from the actual records rather than assuming
    # multi-tape families all have the same size.
    family_histogram = {}
    source_member_count = 0
    for family in all_families:
        size = int(family['member_count'])
        family_histogram[str(size)] = family_histogram.get(str(size), 0) + 1
        source_member_count += size
    singleton_count = int(analysis['source_rows']) - source_member_count
    if singleton_count < 0:
        raise RuntimeError('family member counts exceed source rows')
    if singleton_count:
        family_histogram['1'] = family_histogram.get('1', 0) + singleton_count
    unique_prefix_hash_count = sum(family_histogram.values())
    if unique_prefix_hash_count != int(analysis['source_rows']) - source_member_count + len(all_families):
        raise RuntimeError('prefix family census is inconsistent')

    candidates = []
    for declared in analysis['selected_candidates']:
        candidate_path = Path(declared['candidate_path'])
        if sha(candidate_path) != declared['candidate_sha256']:
            raise RuntimeError(f"candidate hash mismatch: {candidate_path.name}")
        ranks = [int(rank) for rank in declared['family']['member_ranks']]
        family = family_by_rank_set[tuple(sorted(ranks))]
        tapes = []
        for source in declared['embedded_tapes']:
            key = (int(source['rank']), int(source['episode_id']))
            verified = validated_by_key.get(key)
            if verified is None:
                raise RuntimeError(f'input tape was not provenance-verified: {key}')
            tapes.append({
                'frozen_leaderboard_rank': int(source['rank']),
                'team': source['team'],
                'team_id': source.get('team_id'),
                'submission_id': source.get('submission_id'),
                'episode_id': int(source['episode_id']),
                'source_seat': int(source['source_seat']),
                'route_path': verified['route_path'],
                'action_sha256': verified['action_sha256'],
                'replay_path': verified['replay_path'],
                'replay_archive_sha256': verified['replay_archive_sha256'],
                'replay_sha256': verified['replay_sha256'],
                'public_state_index_path': verified['public_state_index_path'],
                'public_state_index_archive_sha256': verified['public_state_index_archive_sha256'],
                'public_state_index_content_sha256': verified['public_state_index_content_sha256'],
                'public_state_index_sha256_from_source_summary': verified['public_state_index_sha256_from_source_summary'],
                'public_state_path': verified['public_state_path'],
                'public_state_archive_sha256': verified['public_state_archive_sha256'],
                'public_state_sha256': verified['public_state_sha256'],
                'shop_history_at_unlocks': declared['family']['shop_histories'][str(source['rank'])],
                'provenance_only_fields_not_embedded_in_candidate': [
                    'team', 'team_id', 'submission_id', 'episode_id', 'source_seat',
                    'route_path', 'replay_path', 'all_sha256_fields',
                ],
            })
        candidates.append({
            'candidate_id': int(declared['candidate_id']),
            'path': str(candidate_path.resolve()),
            'sha256': declared['candidate_sha256'],
            'bytes': int(declared['candidate_bytes']),
            'base_rank': int(declared['base_rank']),
            'family_ranks': ranks,
            'physical_prefix72_sha256': family['physical_prefix72_sha256'],
            'maximum_shared_physical_prefix_checkpoint': int(family['maximum_shared_prefix_checkpoint']),
            'embedded_policy_fields': ['rank', 'shop_history', 'actions'],
            'tapes': tapes,
        })

    multi_family_top20_ranks = sorted({int(rank) for family in all_families
                                       for rank in family['member_ranks'] if int(rank) <= 20})
    manifest = {
        'created_at_utc': datetime.now(timezone.utc).isoformat(),
        'scope': 'Static architecture experiment using development latest-episode tapes only; no policy benchmark.',
        'source': {
            'summary_path': str(SOURCE_SUMMARY.resolve()),
            'summary_sha256': source_sha,
            'leaderboard_snapshot_utc': '2026-09-29T17:04:23Z',
            'development_summary_receipt_utc': analysis['source_snapshot_utc'],
            'source_rows': int(analysis['source_rows']),
            'engine_version': '1.32.7',
            'frames_per_replay': 720,
            'actions_per_tape': 719,
            'development_tier_only': True,
        },
        'frozen_plan': {'path': str((HERE / 'PLAN.md').resolve()), 'sha256': plan_sha},
        'candidate_validation': {
            'path': str((HERE / 'candidate_validation.json').resolve()),
            'sha256': sha(HERE / 'candidate_validation.json'),
            'selected_route_replay_sidecar_provenance_verified': validation['checks']['selected_route_replay_sidecar_provenance_verified'],
            'game_runs': 0,
            'outcome_fields_used': False,
            'reserved_episode_2_or_3_read': False,
        },
        'physical_opening_census': {
            'projection': analysis['physical_projection'],
            'projected_prefix_length': 72,
            'rows': int(analysis['source_rows']),
            'unique_projected_prefixes': unique_prefix_hash_count,
            'cluster_size_histogram': family_histogram,
            'multi_tape_family_count': len(all_families),
            'largest_family_size': max((int(f['member_count']) for f in all_families), default=0),
            'multi_family_ranks_in_top20': multi_family_top20_ranks,
            'selection_order': analysis['family_selection_order'],
            'selected_families': candidates,
            'fourth_tied_size_family_omitted': next(({
                'ranks': family['member_ranks'],
                'maximum_shared_physical_prefix_checkpoint': family['maximum_shared_prefix_checkpoint'],
                'best_rank': family['best_rank'],
            } for family in all_families if tuple(sorted(int(r) for r in family['member_ranks'])) not in {
                tuple(sorted(int(r) for r in c['family_ranks'])) for c in candidates}), None),
        },
        'early_melon_action_scan': {
            'path': str((HERE / 'melon_support.json').resolve()),
            'sha256': sha(HERE / 'melon_support.json'),
            'all_selected_family_tapes': len(melon['records']),
            'first_buy_seed_melon_action_offset': 5,
            'first_plant_melon_action_offset': 7,
            'interpretation': 'Recorded commands in source tapes only; successful execution was not inferred.',
        },
        'router_contract': {
            'checkpoints': list(range(72, 649, 72)),
            'physical_prefix': 'preserve farmer/hands; preserve ordered market commands except remove SELL and BUY_PRODUCT only',
            'switch_only_when': [
                'candidate whole physical prefix matches active whole prefix through checkpoint',
                'candidate historical shop prefix through currently visible unlocks matches observation',
            ],
            'tape_choice': 'lowest frozen leaderboard rank among eligible tapes',
            'fallback': 'retain active tape when no candidate qualifies',
            'observation_fields_used_for_selection': ['step', 'town.unlocked_shops'],
            'runtime_identity_or_outcome_inputs': [],
            'source_team_and_episode_metadata_in_runtime_payload': False,
            'old_cb76_helpers_or_overrides_reused': False,
        },
        'candidate_sources': candidates,
        'source_manifest_provenance_only': {
            'team_names_and_ids_are_for_source_identification_only': True,
            'episode_and_submission_ids_are_not_embedded_in_candidate_policy_payload': True,
            'seed_or_opponent_identity_not_used_for_policy_selection': True,
        },
    }
    manifest_path = HERE / 'candidate_manifest.json'
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps({'manifest_path': str(manifest_path.resolve()),
                      'manifest_sha256': sha(manifest_path),
                      'candidate_count': len(candidates),
                      'unique_projected_prefixes': unique_prefix_hash_count,
                      'cluster_size_histogram': family_histogram}, indent=2))

if __name__ == '__main__':
    main()
