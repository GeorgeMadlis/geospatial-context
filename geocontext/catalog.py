"""Candidate source descriptions; loading these never accesses providers."""
from importlib.resources import files
import yaml

def sources():
    data = yaml.safe_load(files('geocontext').joinpath('sources.yaml').read_text())
    for source in data['sources']:
        source.setdefault('licence', 'unknown; review required')
        source.setdefault('crs', 'unverified')
        source.setdefault('historical_verification_utc', None)
        source['current_verification_utc'] = None
        source['live_access'] = 'not authorized; source review pending'
        source['adapter_status'] = 'not implemented'
    return data['sources']

def describe(source_id):
    return next((item for item in sources() if item['id'] == source_id), None)
