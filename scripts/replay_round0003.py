"""Read-only inspection of local historical captures; no network or source-file writes.

This is an incremental replay, not a complete implementation of the planned replay.
"""
import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from geocontext.orthophoto import listing_dates


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('round_directory', type=Path)
    args = parser.parse_args()
    root = args.round_directory
    geo = root / 'artifacts/geo-01'
    works = root / 'artifacts/works-01'
    output = {'mode': 'offline_local_originals', 'checks': [], 'limitations': []}
    def check(name, passed, detail):
        output['checks'].append({'name': name, 'passed': passed, 'detail': detail})
    gs13 = json.loads((geo / 'raw/etak/etak_fetch_log.json').read_text())
    for record in gs13:
        path = geo / 'raw/etak' / Path(record['file']).name
        raw = path.read_bytes()
        actual = hashlib.sha256(raw).hexdigest()
        count = len(json.loads(raw).get('features', []))
        check('GS-13 ' + record['roi'] + ' ' + record['layer'],
              actual == record['sha256'] and count == record['n_features_bbox'],
              {'path': str(path), 'sha256': actual, 'count': count,
               'expected_sha256': record['sha256'], 'expected_count': record['n_features_bbox'],
               'retrieved_utc': record['retrieved_utc']})
    with (works / 'works_ledger.csv').open(newline='', encoding='utf-8') as f:
        ledger = {r['evidence_id']: r for r in csv.DictReader(f)}
    for number in (1, 2, 4, 5, 6, 7, 8, 9, 10):
        ident = f'E{number:02d}'
        row = ledger[ident]
        paths = [x.strip() for x in row['local_path'].split(';')]
        hashes = [x.strip() for x in row['sha256'].split(';')]
        if len(paths) != len(hashes):
            raise ValueError(f'{ident}: mismatched path and hash counts')
        for rel, expected in zip(paths, hashes):
            path = works / rel
            actual = digest(path)
            check(ident, actual == expected, {'path': str(path), 'sha256': actual,
                  'expected_sha256': expected, 'retrieved_utc': row['retrieval_utc']})
    # E03 lists wildcard paths; match individual original manifest entries, not basenames.
    manifest = json.loads((works / 'works_primary_evidence.json').read_text())
    files = [x for x in manifest['files'] if x['path'].startswith(('downloads/etak/e_503_siht_j_', 'downloads/etak/e_601_elektriliin_j_', 'downloads/etak/e_603_torujuhe_j_'))]
    if not files:
        raise ValueError('E03 original manifest has no matching files')
    for item in files:
        path = works / item['path']
        actual = digest(path)
        check('E03', actual == item['sha256'], {'path': str(path), 'sha256': actual,
              'expected_sha256': item['sha256']})
    sheet = geo / 'raw/sheets/sheet_53734_ortofoto_eesti_rgb.html'
    dates = listing_dates(sheet.read_text(encoding='utf-8'))
    points = json.loads((geo / 'raw/metainfo_points.json').read_text())
    observations = [p for p in points if p.get('NR_10000') == '53734' and p.get('LENNUAEG') == '09.06.2023']
    check('GS-04/GS-05 date discrepancy', '2025-04-03' in dates and bool(observations),
          {'sheet_sha256': digest(sheet), 'sheet': '53734', 'listing_dates': dates,
           'metadata_values': sorted({p['LENNUAEG'] for p in observations}),
           'metadata_sha256': digest(geo / 'raw/metainfo_points.json'),
           'note': 'Filename dates and WMS metadata differ; WMS layer to flight association was inferred.'})
    for layer in (1, 9, 12):
        path = works / f'downloads/teeregister/road4_layer{layer}.geojson'
        data = json.loads(path.read_text())
        check(f'S08 layer {layer} present', True, {'path': str(path), 'sha256': digest(path),
              'feature_count': len(data.get('features', [])),
              'note': 'Integrity hash observed now; historical expected hash not established.'})
    # Recompute two recorded linear measurements from the original inputs.
    from pyproj import Transformer
    from shapely.geometry import shape
    from shapely.ops import transform
    roi_path = root / 'inputs/prior_rois.geojson'
    projection = Transformer.from_crs(4326, 3301, always_xy=True).transform
    rois = {f['properties']['id']: transform(projection, shape(f['geometry']))
            for f in json.loads(roi_path.read_text())['features']}
    rail_path = works / 'downloads/etak/e_502_roobastee_j_roi01.json'
    rails = json.loads(rail_path.read_text())['features']
    matching = [f for f in rails if f['properties'].get('etak_id') == 4076351]
    rail_length = sum(shape(f['geometry']).intersection(rois['ROI-01']).length for f in matching)
    check('E02 rail intersection', len(matching) == 1 and round(rail_length) == 143,
          {'feature_id': 4076351, 'length_m': rail_length, 'expected_rounded_m': 143,
           'crs': 'EPSG:3301', 'roi_sha256': digest(roi_path), 'source_sha256': digest(rail_path)})
    road_path = works / 'downloads/teeregister/road4_layer9.geojson'
    roads = [shape(f['geometry']) for f in json.loads(road_path.read_text())['features']
             if f['properties'].get('soiduteenr') == 1 and f.get('geometry')]
    road_distance = min(g.distance(rois['ROI-02']) for g in roads)
    road_length = sum(g.intersection(rois['ROI-02']).length for g in roads)
    check('S08 road section distance', round(road_distance) == 24 and round(road_length) == 0,
          {'distance_m': road_distance, 'intersection_length_m': road_length,
           'expected_rounded_distance_m': 24, 'expected_rounded_length_m': 0,
           'crs': 'EPSG:3301', 'roi_sha256': digest(roi_path), 'source_sha256': digest(road_path)})
    # Reproduce historical grouping while retaining the underlying distinction: these
    # are line intersections and an administrative planning polygon, not identities.
    powers = []
    for suffix in ('roi01', 'roi02'):
        path = works / f'downloads/etak/e_601_elektriliin_j_{suffix}.json'
        powers.extend(json.loads(path.read_text())['features'])
    seen = set()
    length = 0.0
    for feature in powers:
        if feature['id'] in seen:
            continue
        seen.add(feature['id'])
        if str(feature['properties'].get('nimipinge')) == '10':
            segment = shape(feature['geometry']).intersection(rois['ROI-02'])
            if segment.length >= 1:
                length += segment.length
    check('E03 power-line intersection', round(length, 1) == 232.7,
          {'length_m': length, 'expected_rounded_m': 232.7, 'crs': 'EPSG:3301',
           'note': 'Grouped 10 kV intersections in historical ROI; does not resolve a different feature.'})
    from pyproj import Geod
    from shapely.geometry.polygon import orient
    from shapely.geometry import MultiPolygon
    planning_path = works / 'downloads/plan/rb_planeeringutrass.json'
    planning = json.loads(planning_path.read_text())['features']
    corridor = shape(planning[0]['geometry'])
    inverse = Transformer.from_crs(3301, 4326, always_xy=True).transform
    def geodesic_area(geom):
        g = transform(inverse, geom)
        if g.geom_type == 'Polygon': g = orient(g, sign=1)
        elif g.geom_type == 'MultiPolygon': g = MultiPolygon([orient(x, sign=1) for x in g.geoms])
        else: raise ValueError('unexpected planning geometry')
        return abs(Geod(ellps='WGS84').geometry_area_perimeter(g)[0])
    pct = 100 * geodesic_area(corridor.intersection(rois['ROI-01'])) / geodesic_area(rois['ROI-01'])
    check('E04 planning corridor fraction', round(pct, 1) == 46.0,
          {'percentage': pct, 'expected_rounded_percentage': 46.0, 'area_method': 'WGS84 geodesic',
           'area_crs': 'EPSG:4326', 'source_sha256': digest(planning_path),
           'note': 'Planning polygon overlap is not an as-built alignment.'})
    notice_path = works / 'downloads/metsaregister/teatis_roi01.json'
    notices = json.loads(notice_path.read_text())['features']
    dated = sum(bool(f.get('properties', {}).get('otsus_kinnitatud_kp')) for f in notices)
    check('E09 approval-date field present', dated > 0,
          {'features_with_approval_date': dated, 'total_features': len(notices),
           'source_sha256': digest(notice_path), 'note': 'Approval is not a felling date.'})
    output['limitations'] = ['No network calls. This checks local historical bytes, not current data or geographic conclusions.',
      'Not yet a complete fixture replay: other measurements, independent expected S08 hashes and all schema checks remain outstanding.',
      'Sheet listing names are not embedded image metadata; notice approval dates are not felling dates.',
      'No raw files or images were copied or redistributed.']
    print(json.dumps(output, indent=2, ensure_ascii=False))
    return 0 if all(item['passed'] for item in output['checks']) else 1

if __name__ == '__main__':
    raise SystemExit(main())
