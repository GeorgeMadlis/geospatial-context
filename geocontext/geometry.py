"""Geometry operations without identity or causal classification."""
import math
from pyproj import Transformer, Geod
from shapely.geometry import shape, mapping, LineString
from shapely.ops import transform, unary_union, linemerge


def project(geojson):
    geom = shape(geojson)
    if geom.is_empty or not geom.is_valid:
        raise ValueError('geometry must be nonempty and valid')
    bounds = geom.bounds
    if not all(math.isfinite(n) for n in bounds) or not (-180 <= bounds[0] <= bounds[2] <= 180 and -90 <= bounds[1] <= bounds[3] <= 90):
        raise ValueError('AOI must use finite EPSG:4326 longitude/latitude')
    return transform(Transformer.from_crs(4326, 3301, always_xy=True).transform, geom)


def parts(geom):
    if geom.geom_type in ('LineString', 'LinearRing'):
        yield geom
    elif hasattr(geom, 'geoms'):
        for component in geom.geoms:
            yield from parts(component)


def bearing(line):
    first, last = line.coords[0], line.coords[-1]
    if first[:2] == last[:2]:
        return None
    return math.degrees(math.atan2(last[0]-first[0], last[1]-first[1])) % 180


def measure(a, b, buffer_m=0.0, angle_tolerance_deg=15.0):
    if not math.isfinite(buffer_m) or buffer_m < 0:
        raise ValueError('buffer must be nonnegative and finite')
    if not math.isfinite(angle_tolerance_deg) or not 0 <= angle_tolerance_deg <= 90:
        raise ValueError('angle tolerance must be between 0 and 90 degrees')
    x, y = project(a), project(b)
    overlap = x.intersection(y)
    buffered = y.intersection(x.buffer(buffer_m)) if buffer_m else overlap
    xlines = list(parts(x))
    reference = max(xlines, key=lambda g:g.length, default=None)
    ref_angle = bearing(reference) if reference is not None else None
    aligned, angles = [], []
    if ref_angle is not None:
        for line in parts(buffered):
            for start, end in zip(line.coords, list(line.coords)[1:]):
                segment = LineString([start, end])
                angle = bearing(segment)
                if angle is None:
                    continue
                difference = abs(angle - ref_angle)
                difference = min(difference, 180-difference)
                angles.append({'bearing_deg':angle,'difference_deg':difference,'length_m':segment.length})
                if difference <= angle_tolerance_deg:
                    aligned.append(segment)
    merged = None
    if aligned:
        union = unary_union(aligned)
        merged = union if union.geom_type == 'LineString' else linemerge(union)
    lengths = [line.length for line in parts(merged)] if merged is not None else []
    area = None
    if overlap.geom_type in ('Polygon','MultiPolygon') and not overlap.is_empty:
        geographic = transform(Transformer.from_crs(3301, 4326, always_xy=True).transform, overlap)
        from shapely.geometry.polygon import orient
        if geographic.geom_type == 'Polygon': geographic = orient(geographic, sign=1.0)
        else:
            from shapely.geometry import MultiPolygon
            geographic = MultiPolygon([orient(g, sign=1.0) for g in geographic.geoms])
        square_m, _ = Geod(ellps='WGS84').geometry_area_perimeter(geographic)
        area = {'hectares':abs(square_m)/10000, 'method':'WGS84 geodesic', 'crs':'EPSG:4326'}
    return {'crs':'EPSG:3301', 'precision':'double', 'buffer_m':buffer_m,
            'angle_tolerance_deg':angle_tolerance_deg, 'distance_m':x.distance(y),
            'intersection':mapping(overlap), 'in_buffer':mapping(buffered),
            'in_buffer_length_m':buffered.length, 'intersection_area':area,
            'reference_bearing_deg':ref_angle, 'segment_angles':angles,
            'maximum_aligned_in_buffer_length_m':max(lengths, default=0.0) if ref_angle is not None else None,
            'aligned_in_buffer_geometry':mapping(merged) if merged is not None else None,
            'limitations':['Alignment uses the endpoint bearing of the longest reference line; curved or branched references require review.',
                           'No identity or causal inference is produced.']}
