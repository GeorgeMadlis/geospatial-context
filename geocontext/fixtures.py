"""Query locally retained vector responses; never calls a provider."""
import hashlib
import json
import math
from pathlib import Path
from shapely.geometry import shape, mapping
from shapely.ops import transform
from pyproj import Transformer
from .catalog import describe
from .geometry import project


def query(source_id, fixture, aoi, source_crs, max_features=1000):
    if describe(source_id) is None:
        raise ValueError('unknown source ID')
    if max_features < 1 or max_features > 5000:
        raise ValueError('feature limit must be 1–5000')
    raw = Path(fixture).read_bytes()
    if len(raw) > 25_000_000:
        raise ValueError('fixture exceeds 25 MB limit')
    collection = json.loads(raw)
    if collection.get('type') != 'FeatureCollection' or not isinstance(collection.get('features'), list):
        raise ValueError('fixture must be a GeoJSON FeatureCollection')
    declared = collection.get('crs', {}).get('properties', {}).get('name', '')
    if declared and not (declared.endswith('::' + source_crs[5:]) or declared.endswith(source_crs)):
        raise ValueError('fixture CRS declaration conflicts with selected CRS')
    footprint = project(aoi)
    transform_4326 = Transformer.from_crs(4326, 3301, always_xy=True).transform
    transform_back = Transformer.from_crs(3301, 4326, always_xy=True).transform
    matches = []
    count = 0
    for feature in collection['features']:
        if feature.get('type') != 'Feature' or not feature.get('geometry'):
            raise ValueError('fixture has invalid or missing feature geometry')
        geom = shape(feature['geometry'])
        if geom.is_empty or not geom.is_valid:
            raise ValueError('fixture has invalid or empty feature geometry')
        if not all(math.isfinite(v) for v in geom.bounds):
            raise ValueError('fixture contains non-finite coordinates')
        if source_crs == 'EPSG:4326':
            minx, miny, maxx, maxy = geom.bounds
            if not (-180 <= minx <= maxx <= 180 and -90 <= miny <= maxy <= 90):
                raise ValueError('fixture has coordinates outside EPSG:4326')
            geom = transform(transform_4326, geom)
        elif source_crs != 'EPSG:3301':
            raise ValueError('supported fixture CRS: EPSG:4326 or EPSG:3301')
        if geom.intersects(footprint):
            count += 1
            if len(matches) < max_features:
                item = dict(feature)
                item['geometry'] = mapping(transform(transform_back, geom))
                matches.append(item)
    return {'type':'FeatureCollection', 'features':matches, 'source_id':source_id,
            'fixture_sha256':hashlib.sha256(raw).hexdigest(), 'fixture_crs':source_crs,
            'output_crs':'EPSG:4326', 'status':'matched' if count else 'no_matching_features',
            'total_matching_features':count, 'returned_features':len(matches), 'truncated':count > len(matches),
            'limitations':['Local response subset only; no provider request or coverage assessment.']}
