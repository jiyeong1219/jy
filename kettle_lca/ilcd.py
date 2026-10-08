"""Extract ILCD records without guessing providers, allocations or factors."""
from functools import lru_cache
import hashlib
from pathlib import Path
import xml.etree.ElementTree as ET

NS = {k: 'http://lca.jrc.it/ILCD/' + v for k, v in {
    'p': 'Process', 'c': 'Common', 'f': 'Flow', 'fp': 'FlowProperty',
    'u': 'UnitGroup', 'l': 'LCIAMethod'}.items()}
LANG = '{http://www.w3.org/XML/1998/namespace}lang'


def text(root, path):
    return root.findtext(path, default='', namespaces=NS).strip()


def english(root, path):
    nodes = root.findall(path, NS)
    return next((n.text or '' for n in nodes if n.get(LANG) == 'en'),
                nodes[0].text or '' if nodes else '').strip()


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class Archive:
    def __init__(self, root):
        self.root = Path(root)

    @lru_cache(maxsize=8192)
    def record(self, kind, uuid):
        # IDs are filenames, never paths from an untrusted XML URI.
        import uuid as uuid_module
        if not isinstance(uuid, str):
            raise ValueError('Missing referenced UUID')
        uuid_module.UUID(uuid)
        return ET.parse(self.root / kind / (uuid + '.xml')).getroot()

    def version(self, root):
        return text(root, './/c:dataSetVersion')

    def flow(self, uuid):
        root = self.record('flows', uuid)
        rid = text(root, 'f:flowInformation/f:quantitativeReference/f:referenceToReferenceFlowProperty')
        props = root.findall('f:flowProperties/f:flowProperty', NS)
        prop = next((x for x in props if x.get('dataSetInternalID') == rid), None)
        if prop is None:
            raise ValueError(f'{uuid}: unresolved reference flow property')
        ref = prop.find('f:referenceToFlowPropertyDataSet', NS)
        if ref is None:
            raise ValueError(f'{uuid}: missing property reference')
        pr = self.record('flowproperties', ref.get('refObjectId'))
        ur = pr.find('fp:flowPropertiesInformation/fp:quantitativeReference/fp:referenceToReferenceUnitGroup', NS)
        if ur is None:
            raise ValueError(f'{uuid}: missing unit group')
        group = self.record('unitgroups', ur.get('refObjectId'))
        unit_id = text(group, 'u:unitGroupInformation/u:quantitativeReference/u:referenceToReferenceUnit')
        unit = next(x for x in group.findall('u:units/u:unit', NS)
                    if x.get('dataSetInternalID') == unit_id)
        categories = [x.text or '' for x in root.findall('.//c:class', NS)]
        return {
            'flow_id': uuid, 'flow_version': self.version(root),
            'name': english(root, 'f:flowInformation/f:dataSetInformation/f:name/f:baseName'),
            'flow_type': text(root, 'f:modellingAndValidation/f:LCIMethod/f:typeOfDataSet'),
            'reference_unit': text(unit, 'u:name'), 'categories': categories,
            'flow_property_id': ref.get('refObjectId'), 'unit_group_id': ur.get('refObjectId'),
        }

    def process(self, path):
        path = Path(path)
        root = ET.parse(path).getroot()
        refs = [n.text for n in root.findall(
            'p:processInformation/p:quantitativeReference/p:referenceToReferenceFlow', NS)]
        exchanges = []
        for x in root.findall('p:exchanges/p:exchange', NS):
            ref = x.find('p:referenceToFlowDataSet', NS)
            row = {'exchange_id': x.get('dataSetInternalID'),
                   'direction': text(x, 'p:exchangeDirection'),
                   'amount': text(x, 'p:resultingAmount') or text(x, 'p:meanAmount'),
                   'requested_flow_version': ref.get('version', '') if ref is not None else ''}
            if ref is None:
                row['error'] = 'missing flow reference'
            else:
                row['flow_id'] = ref.get('refObjectId')
                try:
                    row.update(self.flow(row['flow_id']))
                    if row['requested_flow_version'] and row['requested_flow_version'] != row['flow_version']:
                        row['error'] = 'requested/resolved flow version mismatch'
                except (OSError, ValueError, ET.ParseError, StopIteration) as exc:
                    row['error'] = str(exc)
            exchanges.append(row)
        loc = root.find('p:processInformation/p:geography/p:locationOfOperationSupplyOrProduction', NS)
        uuid = text(root, 'p:processInformation/p:dataSetInformation/c:UUID')
        return {
            'dataset_id': uuid, 'dataset_version': self.version(root),
            'name': english(root, 'p:processInformation/p:dataSetInformation/p:name/p:baseName'),
            'geography': loc.get('location', '') if loc is not None else '',
            'reference_year': text(root, 'p:processInformation/p:time/c:referenceYear'),
            'process_type': text(root, 'p:modellingAndValidation/p:LCIMethodAndAllocation/p:typeOfDataSet'),
            'reference_exchange_ids': refs,
            'reference_exchanges': [x for x in exchanges if x['exchange_id'] in refs],
            'exchanges': exchanges, 'sha256': digest(path),
            'sources': [dict(x.attrib) for x in root.findall('.//p:referenceToDataSource', NS)],
            'license': text(root, './/c:licenseType'),
        }

    def method(self, uuid):
        root = self.record('lciamethods', uuid)
        factors = []
        for x in root.findall('l:characterisationFactors/l:factor', NS):
            ref = x.find('l:referenceToFlowDataSet', NS)
            row = {'flow_id': ref.get('refObjectId'), 'requested_flow_version': ref.get('version', ''),
                   'factor': text(x, 'l:meanValue'), 'direction': text(x, 'l:exchangeDirection'),
                   'location': text(x, 'l:location')}
            try:
                row.update(self.flow(row['flow_id']))
                if row['requested_flow_version'] and row['requested_flow_version'] != row['flow_version']:
                    row['error'] = 'requested/resolved flow version mismatch'
            except (OSError, ValueError, ET.ParseError, StopIteration) as exc:
                row['error'] = str(exc)
            factors.append(row)
        return {'dataset_id': uuid, 'dataset_version': self.version(root),
                'name': english(root, 'l:LCIAMethodInformation/l:dataSetInformation/c:name'),
                'indicator': text(root, 'l:LCIAMethodInformation/l:dataSetInformation/l:impactIndicator'),
                'factors': factors,
                'sha256': digest(self.root / 'lciamethods' / (uuid + '.xml')),
                'approved_for_kettle': False}
