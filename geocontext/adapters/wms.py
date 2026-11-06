"""Extract layer names from bounded local WMS capabilities."""
from xml.etree import ElementTree


def layer_names(xml_bytes):
    if len(xml_bytes) > 10_000_000:
        raise ValueError('capabilities exceeds size limit')
    if b'<!DOCTYPE' in xml_bytes.upper() or b'<!ENTITY' in xml_bytes.upper():
        raise ValueError('DTD and entities are not permitted')
    root = ElementTree.fromstring(xml_bytes)
    return sorted({child.text.strip() for element in root.iter()
                   if element.tag.rsplit('}',1)[-1] == 'Layer'
                   for child in element
                   if child.tag.rsplit('}',1)[-1] == 'Name' and child.text})
