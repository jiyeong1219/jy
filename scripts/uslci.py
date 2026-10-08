#!/usr/bin/env python3
"""Retrieve checksum-pinned official USLCI packages; catalog JSON-LD inventories."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def fetch(destination):
    dest = Path(destination)
    dest.mkdir(parents=True, exist_ok=True)
    entries = json.loads((ROOT / 'data/source_manifest.json').read_text())['uslci']['archives']
    for record in entries:
        target = dest / record['path']
        if not target.exists():
            temporary = target.with_suffix(target.suffix + '.part')
            try:
                with urllib.request.urlopen(record['url'], timeout=60) as response:
                    temporary.write_bytes(response.read())
                if hashlib.sha256(temporary.read_bytes()).hexdigest() != record['sha256']:
                    raise ValueError('Downloaded archive checksum mismatch')
                temporary.replace(target)
            finally:
                temporary.unlink(missing_ok=True)
        if target.stat().st_size != record['byte_size'] or hashlib.sha256(target.read_bytes()).hexdigest() != record['sha256']:
            raise ValueError('Cached archive does not match pinned source')
        with zipfile.ZipFile(target) as archive:
            bad = archive.testzip()
            if bad:
                raise ValueError(f'ZIP integrity failure: {bad}')
            if record['format'] == 'ILCD':
                extracted = dest / 'ilcd-2019'
                for name in archive.namelist():
                    if not (extracted / name).resolve().is_relative_to(extracted.resolve()):
                        raise ValueError('Unsafe ZIP path')
                if not extracted.exists():
                    archive.extractall(extracted)
        print(f"Verified {record['format']} {record['release']}: {target}")


def catalog(package, output):
    fields = ['database', 'database_release', 'dataset_id', 'dataset_version', 'name', 'geography',
              'process_type', 'allocation_method', 'reference_flow_id', 'reference_amount',
              'reference_unit', 'reference_count', 'exchange_count', 'elementary_exchange_count',
              'missing_default_provider_count', 'external_provider_count', 'sha256', 'status']
    manifest = json.loads((ROOT / 'data/source_manifest.json').read_text())
    source = next(x for x in manifest['uslci']['archives'] if x['format'] == 'JSON-LD')
    if hashlib.sha256(Path(package).read_bytes()).hexdigest() != source['sha256']:
        raise ValueError('Package hash not recorded in source manifest')
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(package) as archive, open(output, 'w', newline='', encoding='utf-8') as stream:
        names = sorted(n for n in archive.namelist() if n.startswith('processes/') and n.endswith('.json'))
        process_ids = {Path(n).stem for n in names}
        writer = csv.DictWriter(stream, fieldnames=fields); writer.writeheader()
        for name in names:
            raw = archive.read(name); p = json.loads(raw)
            exchanges = p.get('exchanges', [])
            refs = [x for x in exchanges if x.get('isQuantitativeReference')]
            ref = refs[0] if len(refs) == 1 else {}
            elementary = [x for x in exchanges if x.get('flow', {}).get('flowType') == 'ELEMENTARY_FLOW']
            upstream = [x for x in exchanges if x.get('isInput') and x.get('flow', {}).get('flowType') == 'PRODUCT_FLOW']
            writer.writerow(dict(database='USLCI', database_release=source['release'], dataset_id=p['@id'],
                dataset_version=p.get('version', ''), name=p['name'], geography=p.get('location', {}).get('name', ''),
                process_type=p.get('processType', ''), allocation_method=p.get('defaultAllocationMethod', ''),
                reference_flow_id=ref.get('flow', {}).get('@id', ''), reference_amount=ref.get('amount', ''),
                reference_unit=ref.get('unit', {}).get('name', ''), reference_count=len(refs), exchange_count=len(exchanges),
                elementary_exchange_count=len(elementary), missing_default_provider_count=sum(not x.get('defaultProvider') for x in upstream),
                external_provider_count=sum(bool(x.get('defaultProvider')) and x['defaultProvider']['@id'] not in process_ids for x in upstream),
                sha256=hashlib.sha256(raw).hexdigest(), status='retrieved_not_selected'))
        print(f'Cataloged {len(names)} USLCI JSON-LD processes')


def extract(package, process_id, output):
    import uuid
    uuid.UUID(process_id)
    with zipfile.ZipFile(package) as archive:
        name = 'processes/' + process_id + '.json'
        raw = archive.read(name)
        # Original byte-preserving inventory, including formulas, allocation and provider refs.
        Path(output).parent.mkdir(parents=True, exist_ok=True)
        if Path(output).exists():
            raise ValueError('Refusing to overwrite existing extraction')
        Path(output).write_bytes(raw)
        print(f'Extracted process {process_id}, sha256={hashlib.sha256(raw).hexdigest()}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    f = sub.add_parser('fetch'); f.add_argument('--destination', default=str(ROOT / 'data/raw/uslci'))
    c = sub.add_parser('catalog'); c.add_argument('--package', required=True); c.add_argument('--output', default=str(ROOT / 'data/uslci_jsonld_catalog.csv'))
    e = sub.add_parser('extract'); e.add_argument('--package', required=True); e.add_argument('--process-id', required=True); e.add_argument('--output', required=True)
    args = parser.parse_args()
    if args.command == 'fetch': fetch(args.destination)
    elif args.command == 'catalog': catalog(args.package, args.output)
    elif args.command == 'extract': extract(args.package, args.process_id, args.output)
