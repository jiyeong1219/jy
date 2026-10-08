import csv
from pathlib import Path
import tempfile
import unittest
from kettle_lca.project import validate_bom


class BomTests(unittest.TestCase):
    def write(self, rows):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        p = Path(directory.name) / 'bom.csv'
        with p.open('w', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=['material_id', 'material_name', 'group', 'mass_g'])
            writer.writeheader(); writer.writerows(rows)
        return p

    def rows(self):
        # Arbitrary synthetic partitions for validator tests, never a kettle BOM.
        return [{'material_id': str(i), 'material_name': 'synthetic',
                 'group': 'product' if i < 10 else 'packaging',
                 'mass_g': '72.3' if i < 10 else '68.9'} for i in range(12)]

    def test_mass_and_conversion(self):
        rows = validate_bom(self.write(self.rows()))
        self.assertAlmostEqual(sum(r['mass_kg'] for r in rows), .8608)

    def test_incomplete(self):
        rows = self.rows(); rows[0]['mass_g'] = ''
        with self.assertRaises(ValueError): validate_bom(self.write(rows))

    def test_total(self):
        rows = self.rows(); rows[0]['mass_g'] = '72.4'
        with self.assertRaises(ValueError): validate_bom(self.write(rows))

    def test_split(self):
        rows = self.rows(); rows[0]['group'] = 'packaging'
        with self.assertRaises(ValueError): validate_bom(self.write(rows))

    def test_nan(self):
        rows = self.rows(); rows[0]['mass_g'] = 'NaN'
        with self.assertRaises(ValueError): validate_bom(self.write(rows))
