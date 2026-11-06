import socket
import unittest
from unittest.mock import patch
from geocontext.catalog import sources, describe
from geocontext.geometry import measure
from geocontext.orthophoto import listing_dates

class OfflineTests(unittest.TestCase):
    def test_catalog_no_network(self):
        with patch.object(socket, 'create_connection', side_effect=AssertionError('network access')):
            self.assertEqual(len(sources()), 10)
            self.assertEqual(describe('DS-0022')['protocol'], 'ArcGIS REST')
            self.assertTrue(all(s['current_verification_utc'] is None for s in sources()))

    def test_filename_dates(self):
        html = '<a href="abc_2025_04_03.tif">x</a><a href="abc_2023_06_09.tif">x</a><a href="abc_2025_02_30.tif">x</a>'
        self.assertEqual(listing_dates(html), ['2023-06-09', '2025-04-03'])

    def test_listing_ignores_ranges_and_non_filename_query_dates(self):
        html = '<a href="?f=abc_2002_08_07-08_10.zip">range</a><a href="?page_id=610&amp;x=2025_04_03">link</a>'
        self.assertEqual(listing_dates(html), [])

    def test_distance_and_validation(self):
        p = {'type':'Point','coordinates':[24.5,58.5]}
        q = {'type':'Point','coordinates':[24.501,58.5]}
        output = measure(p,q,100)
        self.assertEqual(output['crs'], 'EPSG:3301')
        self.assertTrue(55 < output['distance_m'] < 65)
        with self.assertRaises(ValueError): measure({'type':'Point','coordinates':[200,58]}, q)
        with self.assertRaises(ValueError): measure(p,q,-1)

if __name__ == '__main__': unittest.main()
