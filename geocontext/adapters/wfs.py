"""Bounded offline parsing of WFS capabilities; no network or expansion."""
from xml.etree import ElementTree


def feature_types(xml_bytes):
    if len(xml_bytes) > 10_000_000:
        raise ValueError('capabilities exceeds size limit')
    if b'<!DOCTYPE' in xml_bytes.upper() or b'<!ENTITY' in xml_bytes.upper():
        raise ValueError('DTD and entities are not permitted')
    root = ElementTree.fromstring(xml_bytes)
    values = set()
    for element in root.iter():
        if element.tag.rsplit('}', 1)[-1] == 'FeatureType':
            for child in element:
                if child.tag.rsplit('}', 1)[-1] == 'Name' and child.text:
                    values.add(child.text.strip())
    return sorted(values)


def require_feature_type(xml_bytes, requested):
    names = feature_types(xml_bytes)
    if requested not in names:
        raise ValueError(f'feature type absent from capabilities: {requested}')
    return requested
