#!/usr/bin/env python3
"""Calculate only a complete, explicitly reviewed normalized kettle model.

There is deliberately no default network or fallback emission factor. A reviewer
must supply reviewed-network.json after resolving the documented data gaps.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from kettle_lca.project import validate_bom
from kettle_lca.matrices import construct, calculate, contributions


def run(model_path, output):
    bom = validate_bom(ROOT / 'data/bom.csv')
    model = json.loads(Path(model_path).read_text())
    required = ['bom_matching', 'foreground_complete', 'supplier_closure', 'allocation',
                'reference_normalization', 'flow_units_and_identity', 'cf_coverage',
                'method_provenance', 'biogenic_carbon', 'double_counting', 'boundary']
    for key in required:
        decision = model.get('review', {}).get(key, {})
        if decision.get('status') != 'approved' or not decision.get('evidence'):
            raise ValueError(f'Missing reviewed evidence: {key}')
    with (ROOT / 'data/dataset_matching.csv').open(newline='', encoding='utf-8') as stream:
        matching = list(csv.DictReader(stream))
    if {r['material_id'] for r in matching} != {r['material_id'] for r in bom} or len(matching) != 12:
        raise ValueError('Matching table must contain each BOM row exactly once')
    for r in matching:
        if r['status'] not in ['approved_exact_match', 'approved_proxy']:
            raise ValueError('Unapproved BOM match')
        if any(not r[k] for k in ['dataset_id', 'dataset_version', 'database_release', 'reference_unit', 'source_url', 'sha256']):
            raise ValueError('Incomplete matching provenance')
        if r['status'] == 'approved_proxy' and not r['proxy_justification']:
            raise ValueError('Proxy requires explicit justification')
    if model.get('declared_unit') != 'one_manufactured_packaged_kettle':
        raise ValueError('Wrong declared unit')
    method = model.get('method', {})
    if method.get('time_horizon_years') != 100 or method.get('impact_unit') != 'kg CO2-eq':
        raise ValueError('Reviewed GWP100 method required')
    records = model.get('source_records', [])
    if not records:
        raise ValueError('Original inventory and CF source records required')
    for record in records:
        path = (ROOT / record['path']).resolve()
        if not path.is_relative_to(ROOT) or hashlib.sha256(path.read_bytes()).hexdigest() != record['sha256']:
            raise ValueError('Invalid source path or source checksum mismatch')
    a, b, c = construct(model['processes'], model['flow_keys'], model['characterization'])
    f = np.asarray(model['demand'], dtype=float)
    groups = model['contribution_demands']
    needed = {r['material_id'] for r in bom} | {'component_manufacturing', 'assembly'}
    if not needed.issubset(groups):
        raise ValueError('Contribution groups must cover 12 materials, component manufacturing and assembly')
    result = calculate(a, b, c, f)
    parts = contributions(a, b, c, groups, f)
    dest = Path(output)
    if dest.exists():
        raise ValueError('Use a new output directory to preserve independent runs')
    dest.mkdir(parents=True)
    np.savez_compressed(dest / 'matrices.npz', A=a.toarray(), B=b.toarray(), C=c,
                        f=f, s=result['s'], g=result['g'], h=result['h'])
    with (dest / 'contributions.csv').open('w', newline='') as stream:
        writer = csv.writer(stream); writer.writerow(['group', 'gwp100_kg_co2_eq'])
        writer.writerows((k, float(v[0])) for k, v in parts.items())
    report = {'status': 'calculated_from_reviewed_model', 'gwp100_kg_co2_eq': float(result['h'][0]),
              'method': method, 'model_sha256': hashlib.sha256(Path(model_path).read_bytes()).hexdigest(),
              'review': model['review'], 'top_three_groups': sorted(parts, key=lambda k: float(parts[k][0]), reverse=True)[:3]}
    (dest / 'results.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    try:
        run(args.model, args.output)
    except (ValueError, KeyError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(2)
