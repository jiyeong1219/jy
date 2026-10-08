#!/usr/bin/env python3
"""Pinned archive retrieval, catalog, extraction and project readiness report."""
import argparse
import csv
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from kettle_lca.ilcd import Archive
from kettle_lca.project import validate_bom


def write_json(path, value):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')


def fetch(destination):
    manifest = json.loads((ROOT / 'data/source_manifest.json').read_text())
    source = manifest['repositories']['data']
    dest = Path(destination).resolve()
    if not dest.exists():
        subprocess.run(['git', 'init', str(dest)], check=True)
        subprocess.run(['git', '-C', str(dest), 'remote', 'add', 'origin', source['url'] + '.git'], check=True)
        subprocess.run(['git', '-C', str(dest), 'fetch', '--depth', '1', 'origin', source['commit']], check=True)
        subprocess.run(['git', '-C', str(dest), 'checkout', '--detach', source['commit']], check=True)
    # Preserve existing directories; refuse unexpected revisions or local changes.
    actual = subprocess.check_output(['git', '-C', str(dest), 'rev-parse', 'HEAD'], text=True).strip()
    if actual != source['commit']:
        raise ValueError('Existing checkout does not match pinned archive commit')
    dirty = subprocess.check_output(['git', '-C', str(dest), 'status', '--porcelain', '--untracked-files=all'], text=True)
    if dirty:
        raise ValueError('Archive has local changes; use a fresh directory')
    print(f'Verified archive commit {actual}')


def catalog(archive, output, database='TianGong'):
    manifest = json.loads((ROOT / 'data/source_manifest.json').read_text())
    commit = manifest['repositories']['data']['commit']
    fields = ['database', 'dataset_id', 'dataset_version', 'name', 'geography', 'reference_year',
              'process_type', 'reference_flow_id', 'reference_amount', 'reference_unit',
              'reference_count', 'exchange_count', 'unresolved_exchange_count',
              'sha256', 'source_url', 'database_release', 'retrieved_date', 'status']
    issues = []
    issue_count = 0
    issue_ids = []
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with open(output, 'w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for path in sorted((archive.root / 'processes').glob('*.xml')):
            p = archive.process(path)
            refs = p['reference_exchanges']
            ref = refs[0] if len(refs) == 1 else {}
            errors = [x for x in p['exchanges'] if 'error' in x]
            if errors:
                issue_count += 1
                issue_ids.append(p['dataset_id'])
                if len(issues) < 10:
                    issues.append({'dataset_id': p['dataset_id'], 'exchanges': errors[:5]})
            row = {k: p[k] for k in fields if k in p}
            row.update(database=database, reference_flow_id=ref.get('flow_id', ''), reference_amount=ref.get('amount', ''),
                       reference_unit=ref.get('reference_unit', ''), reference_count=len(refs),
                       exchange_count=len(p['exchanges']), unresolved_exchange_count=len(errors),
                       source_url=f'https://github.com/tiangong-lca/data/blob/{commit}/tiangong_lca_data/processes/{path.name}',
                       database_release='historical label 0.2.0; commit pinned', retrieved_date='2026-10-08',
                       status='retrieved_not_selected')
            if database == 'USLCI':
                record = next(x for x in manifest['uslci']['archives'] if x['format'] == 'ILCD')
                row['source_url'] = record['url'] + '#ILCD/processes/' + path.name
                row['database_release'] = record['release']
            writer.writerow(row)
            count += 1
    if not count:
        raise ValueError('No process records: wrong or empty archive')
    write_json(Path(output).with_suffix('.audit.json'), {'process_count': count,
               'processes_with_exchange_resolution_issues': issue_count,
               'affected_process_ids': issue_ids, 'issue_examples': issues,
               'note': 'Examples capped at ten processes/five exchanges; counts and affected IDs are complete'})
    print(f'Cataloged {count} real process records; {issue_count} have flow resolution issues')


def status(output):
    blockers = []
    try:
        validate_bom(ROOT / 'data/bom.csv')
        bom_status = 'passed'
    except (ValueError, ArithmeticError) as exc:
        bom_status = 'failed'
        blockers.append(str(exc))
    # Until there is a reviewed foreground/network/method, report all missing items.
    with (ROOT / 'data/dataset_matching.csv').open(newline='', encoding='utf-8') as stream:
        matching = list(csv.DictReader(stream))
    missing = [r['material_name'] for r in matching if not r['dataset_id']]
    if missing:
        blockers.append('Missing suitable processes: ' + ', '.join(missing))
    blockers.extend(['Manufacturing yields, conversion services and assembly electricity not supplied',
                     'Seven retrieved candidate inventories require matching/proxy review and full upstream supplier closure',
                     'Characterization method provenance/version discrepancy and cross-database flow mapping require review'])
    report = {'run_id': 'bc1-access-assessment-2026-10-08', 'status': 'blocked',
              'declared_unit': 'One manufactured and packaged BC1 1 L plastic kettle',
              'gwp100_kg_co2_eq': None, 'material_contributions': None,
              'top_three_contributors': None, 'uncertainty': 'not calculated',
              'checks': {'bom': bom_status, 'supplier_closure': 'not run',
                         'characterization_coverage': 'not run', 'matrix_residual': 'not run',
                         'contribution_reconciliation': 'not run', 'double_counting': 'not run'},
              'blockers': blockers,
              'verified_inputs': {'bom_material_count': 12, 'product_mass_g': 723,
                                 'packaging_mass_g': 137.8, 'total_mass_g': 860.8,
                                 'retrieved_material_candidate_inventories': sum(bool(r['dataset_id']) for r in matching)},
              'note': 'Synthetic algorithm tests are not a kettle calculation.'}
    write_json(output, report)
    print(json.dumps(report, indent=2))
    return 2


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    fetch_p = sub.add_parser('fetch'); fetch_p.add_argument('--destination', default=str(ROOT / 'data/raw/tiangong'))
    cat = sub.add_parser('catalog'); cat.add_argument('--archive', required=True); cat.add_argument('--output', default=str(ROOT / 'data/process_catalog.csv')); cat.add_argument('--database', choices=['TianGong', 'USLCI'], default='TianGong')
    ex = sub.add_parser('extract'); ex.add_argument('--archive', required=True); ex.add_argument('--process-id', required=True); ex.add_argument('--output', required=True)
    met = sub.add_parser('method'); met.add_argument('--archive', required=True); met.add_argument('--method-id', required=True); met.add_argument('--output', required=True)
    sea = sub.add_parser('search'); sea.add_argument('--query', required=True); sea.add_argument('--catalog', default=str(ROOT / 'data/process_catalog.csv')); sea.add_argument('--output', required=True)
    st = sub.add_parser('status'); st.add_argument('--output', default=str(ROOT / 'results/status.json'))
    args = parser.parse_args()
    if args.command == 'fetch': fetch(args.destination)
    elif args.command == 'catalog': catalog(Archive(args.archive), args.output, args.database)
    elif args.command == 'extract':
        archive = Archive(args.archive)
        # Validation prevents traversal from command-line identifiers.
        import uuid
        uuid.UUID(args.process_id)
        write_json(args.output, archive.process(archive.root / 'processes' / (args.process_id + '.xml')))
    elif args.command == 'method': write_json(args.output, Archive(args.archive).method(args.method_id))
    elif args.command == 'search':
        with open(args.catalog, encoding='utf-8', newline='') as stream:
            candidates = [r for r in csv.DictReader(stream) if args.query.casefold() in r['name'].casefold()]
        write_json(args.output, {'query': args.query, 'status': 'candidates_not_approved_matches', 'candidates': candidates})
        print(f'{len(candidates)} candidates; manual review required')
    elif args.command == 'status': return status(args.output)
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
