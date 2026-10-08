"""Project input checks; unavailable data is never interpreted as zero."""
import csv
from decimal import Decimal


def validate_bom(path):
    with open(path, newline='', encoding='utf-8') as stream:
        rows = list(csv.DictReader(stream))
    if len(rows) != 12:
        raise ValueError('BOM requires exactly 12 material rows')
    if len({r['material_id'] for r in rows}) != 12:
        raise ValueError('BOM material IDs must be unique')
    total = Decimal(0)
    groups = {'product': Decimal(0), 'packaging': Decimal(0)}
    for row in rows:
        if not row['material_name'].strip() or not row['mass_g'].strip():
            raise ValueError(f"Missing BOM name/mass: {row['material_id']}")
        mass = Decimal(row['mass_g'])
        if not mass.is_finite() or mass <= 0 or row['group'] not in groups:
            raise ValueError('BOM mass/group invalid')
        total += mass
        groups[row['group']] += mass
        row['mass_kg'] = float(mass / 1000)
    tolerance = Decimal('0.000001')
    for actual, expected in [(total, '860.8'), (groups['product'], '723'),
                             (groups['packaging'], '137.8')]:
        if abs(actual - Decimal(expected)) > tolerance:
            raise ValueError(f'BOM mass mismatch: {actual} g, expected {expected} g')
    return rows
