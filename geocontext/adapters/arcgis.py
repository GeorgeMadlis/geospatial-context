"""Inspect local ArcGIS layer metadata; do not infer endpoint equivalence."""
import json


def layers(payload):
    if len(payload) > 10_000_000:
        raise ValueError('metadata exceeds size limit')
    doc = json.loads(payload)
    if 'error' in doc:
        raise ValueError('ArcGIS returned an error')
    rows = doc.get('layers')
    if not isinstance(rows, list):
        raise ValueError('ArcGIS layers missing')
    return [{'id':r['id'], 'name':r['name']} for r in rows]
