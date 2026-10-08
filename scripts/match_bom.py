#!/usr/bin/env python3
"""Reproduce documented candidate matches, never invent missing processes."""
import csv
import hashlib
import json
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from kettle_lca.ilcd import Archive
from kettle_lca.project import validate_bom

# IDs were read from the retrieved official process records, not generated.
DECISIONS = {
 'BOM01': ('USLCI', '49f5324b-fc33-36e9-b5af-3c80d73492bd', ['stainless'],
           '304 flat rolled coil is a grade/form proxy; kettle grade and forming route unknown. Coil production includes rolling; do not add rolling again.'),
 'BOM02': (None, None, ['brass'], 'No brass production candidate found. Do not invent Cu/Zn composition or substitute pure copper.'),
 'BOM03': ('TianGong', '084b5b59-c7f8-4eb3-ae1a-5ebc1ab64a08', ['cathode copper', 'copper'],
           'Cathode copper is a raw-metal candidate; wire/terminal drawing and fabrication remain separate. USLCI copper bridge is monetary, not an interchangeable kg inventory.'),
 'BOM04': ('USLCI', '2e8facf6-46aa-4ddb-95de-a4e2a00eb2bb', ['polypropylene'],
           'Virgin PP resin candidate; grade/recycled share unknown. Injection-molded-part alternative includes resin and must not be added to resin as a separate full material burden.'),
 'BOM05': ('USLCI', '3dbccdda-2014-4239-ad1f-4e15c034942b', ['polyvinyl chloride'],
           'Suspension PVC resin is a formulation proxy. Cable-grade plasticizers/additives and conversion are not confirmed.'),
 'BOM06': (None, None, ['nylon', 'polyamide'],
           'Nylon grade unspecified. TianGong filament/yarn and inks consuming polyamide are not resin datasets; do not equate them to molded nylon components.'),
 'BOM07': (None, None, ['polyoxymethylene', 'polyformal', 'acetal'],
           'No appropriate POM production candidate found in searched catalogs. No unsupported polymer substitution.'),
 'BOM08': (None, None, ['polycarbonate'],
           'TianGong luggage records consume PC/other resins and reference pieces; they do not produce kg PC resin. Rejected.'),
 'BOM09': ('USLCI', '0e42a306-ee2d-362e-8bc3-580000096459', ['acrylonitrile-butadiene-styrene'],
           'ABS copolymer resin candidate; specific heat-resistant grade and molding inputs remain unknown.'),
 'BOM10': (None, None, ['silicone'],
           'TianGong organic-silicon monomer synthesis is not cured silicone elastomer. Polymerization, formulation and cure are missing; rejected as direct substitute.'),
 'BOM11': ('USLCI', '6a12cba1-889d-4515-90f8-89feb8d662f2', ['low-density', 'low density'],
           'LDPE virgin resin candidate; foil extrusion/conversion is additional, and LLDPE is not assumed equivalent.'),
 'BOM12': ('USLCI', '226ed3c2-e020-4c95-b1fc-4559fc2d18ac', ['corrugated', 'cardboard'],
           'Corrugated product proxy for unspecified cardboard; verify board type. Converting is included in this record; do not add corrugating again.'),
}


def run(tiangong_archive, package):
    bom = validate_bom(ROOT / 'data/bom.csv')
    manifest = json.loads((ROOT / 'data/source_manifest.json').read_text())
    us_source = next(x for x in manifest['uslci']['archives'] if x['format'] == 'JSON-LD')
    catalogs = {}
    for db, filename in [('TianGong', 'process_catalog.csv'), ('USLCI', 'uslci_jsonld_catalog.csv')]:
        with (ROOT / 'data' / filename).open(newline='', encoding='utf-8') as stream:
            catalogs[db] = list(csv.DictReader(stream))
    fields = ['material_id', 'material_name', 'finished_mass_g', 'finished_mass_kg',
              'database', 'database_release', 'dataset_name', 'dataset_id', 'dataset_version',
              'geography', 'reference_year', 'reference_flow', 'reference_amount', 'reference_unit',
              'source_url', 'retrieval_date', 'sha256', 'inventory_path', 'selection_rationale',
              'proxy_justification', 'status']
    searches, matches, inventory_audits = [], [], []
    archive = Archive(tiangong_archive)
    with zipfile.ZipFile(package) as us:
        for row in bom:
            ident = row['material_id']
            database, dataset_id, queries, rationale = DECISIONS[ident]
            alternatives = []
            for db, catalog in catalogs.items():
                found = {r['dataset_id']: r for r in catalog if any(q in r['name'].casefold() for q in queries)}
                alternatives.extend({'database': db, **r} for r in found.values())
            searches.append({'material_id': ident, 'queries': queries, 'search_type': 'case-insensitive local process-name substring',
                             'limitation': 'Historical snapshots, English catalog names; absence is not proof of absence in current platform',
                             'alternatives': alternatives, 'decision': rationale})
            match = {k: '' for k in fields}
            match.update(material_id=ident, material_name=row['material_name'], finished_mass_g=row['mass_g'],
                         finished_mass_kg=row['mass_kg'], selection_rationale=rationale,
                         status='missing_suitable_process')
            if database:
                catalog_row = next(x for x in catalogs[database] if x['dataset_id'] == dataset_id)
                for key in ['database', 'dataset_version', 'geography', 'reference_amount', 'reference_unit', 'sha256']:
                    match[key] = catalog_row[key]
                match.update(dataset_id=dataset_id, database_release=catalog_row['database_release'],
                             dataset_name=catalog_row['name'], reference_flow=catalog_row['reference_flow_id'],
                             retrieval_date='2026-10-08', proxy_justification=rationale,
                             status='inventory_verified_match_review_pending')
                out = ROOT / 'data/raw/candidate_inventories' / (dataset_id + '.json')
                out.parent.mkdir(parents=True, exist_ok=True)
                if database == 'USLCI':
                    raw = us.read('processes/' + dataset_id + '.json'); process = json.loads(raw)
                    out.write_bytes(raw)
                    docs = process.get('processDocumentation', {})
                    match['reference_year'] = '; '.join(str(docs.get(x, 'unknown')) for x in ['validFrom', 'validUntil'])
                    match['source_url'] = us_source['url'] + '#processes/' + dataset_id + '.json'
                    upstream = [e for e in process['exchanges'] if e.get('isInput') and e.get('flow', {}).get('flowType') == 'PRODUCT_FLOW']
                    inventory_audits.append({'material_id': ident, 'dataset_id': dataset_id,
                        'reference_amount': match['reference_amount'], 'reference_unit': match['reference_unit'],
                        'elementary_exchange_count': sum(e.get('flow', {}).get('flowType') == 'ELEMENTARY_FLOW' for e in process['exchanges']),
                        'unlinked_product_inputs': [{'flow': e['flow'], 'amount': e['amount'], 'unit': e.get('unit')} for e in upstream if not e.get('defaultProvider')],
                        'cutoff_policy': 'Not approved: unlinked or CUTOFF flows are not automatically zero',
                        'allocation_metadata': process.get('defaultAllocationMethod'),
                        'allocation_documentation': docs.get('modelingConstantsDescription', ''),
                        'sources': docs.get('sources', [])})
                else:
                    process = archive.process(archive.root / 'processes' / (dataset_id + '.xml'))
                    out.write_text(json.dumps(process, indent=2) + '\n')
                    match['reference_year'] = catalog_row['reference_year']; match['source_url'] = catalog_row['source_url']
                    inventory_audits.append({'material_id': ident, 'dataset_id': dataset_id,
                        'reference_exchanges': process['reference_exchanges'],
                        'flow_resolution_issues': [e for e in process['exchanges'] if e.get('error')],
                        'sources': process['sources'], 'supplier_links': 'ILCD product flow references do not identify providers'})
                match['inventory_path'] = str(out.relative_to(ROOT))
            matches.append(match)
    with (ROOT / 'data/dataset_matching.csv').open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields); writer.writeheader(); writer.writerows(matches)
    (ROOT / 'data/matching_search_log.json').write_text(json.dumps(searches, indent=2, ensure_ascii=False) + '\n')
    (ROOT / 'data/candidate_inventory_audit.json').write_text(json.dumps(inventory_audits, indent=2, ensure_ascii=False) + '\n')
    print(f"Retrieved inventory for {sum(bool(x['dataset_id']) for x in matches)} of 12 material candidates; no matches approved for calculation")


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tiangong-archive', required=True); parser.add_argument('--uslci-package', required=True)
    args = parser.parse_args(); run(args.tiangong_archive, args.uslci_package)
