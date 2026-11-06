import contextlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from jsonschema import Draft202012Validator, FormatChecker
from geocontext.cli import main
from geocontext.geometry import measure

class CliTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.env = patch.dict(os.environ, {'GEOCONTEXT_LEDGER_DIR':str(self.root / 'ledger')})
        self.env.start()
        self.addCleanup(self.env.stop)

    def call(self, args):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = main(args)
        return code, out.getvalue(), err.getvalue()

    def test_event_for_success_and_failure(self):
        self.assertEqual(self.call(['describe-layer','DS-0022'])[0], 0)
        self.assertEqual(self.call(['describe-layer','missing'])[0], 2)
        lines = (self.root/'ledger/tool_executions.jsonl').read_text().splitlines()
        self.assertEqual(len(lines), 2)
        schema = json.loads(Path('schemas/tool_execution_event.schema.json').read_text())
        for line in lines:
            event = json.loads(line)
            Draft202012Validator(schema, format_checker=FormatChecker()).validate(event)
            self.assertTrue(Path(event['raw_response_ref']).is_file())
        self.assertEqual(json.loads(lines[1])['outcome'], 'error')

    def test_offline_query_and_empty(self):
        f = self.root/'input.json'
        a = self.root/'aoi.json'
        f.write_text(json.dumps({'type':'FeatureCollection','features':[{'type':'Feature','id':'native.1', 'properties':{'modified':'2026-10-01'},'geometry':{'type':'Point','coordinates':[24.5,58.5]}}]}))
        a.write_text(json.dumps({'type':'Polygon','coordinates':[[[24.49,58.49],[24.51,58.49],[24.51,58.51],[24.49,58.51],[24.49,58.49]]]}))
        code, out, _ = self.call(['query-layer','DS-0016','--fixture',str(f),'--fixture-crs','EPSG:4326','--aoi',str(a)])
        self.assertEqual(code,0)
        result=json.loads(out)
        self.assertEqual(result['features'][0]['id'], 'native.1')
        self.assertEqual(result['status'], 'matched')
        a.write_text(json.dumps({'type':'Point','coordinates':[25.0,58.5]}))
        code, out, _ = self.call(['query-layer','DS-0016','--fixture',str(f),'--fixture-crs','EPSG:4326','--aoi',str(a)])
        self.assertEqual(code,0)
        self.assertEqual(json.loads(out)['status'], 'no_matching_features')

    def test_aligned_length_and_geodesic_area(self):
        line1={'type':'LineString','coordinates':[[24.5,58.5],[24.5,58.501]]}
        line2={'type':'LineString','coordinates':[[24.50001,58.5],[24.50001,58.501]]}
        result=measure(line1,line2,10,10)
        self.assertGreater(result['maximum_aligned_in_buffer_length_m'], 100)
        square={'type':'Polygon','coordinates':[[[24.5,58.5],[24.501,58.5],[24.501,58.501],[24.5,58.501],[24.5,58.5]]]}
        area=measure(square,square)['intersection_area']
        self.assertEqual(area['method'],'WGS84 geodesic')
        self.assertGreater(area['hectares'],0)

if __name__ == '__main__': unittest.main()

class ParserTests(unittest.TestCase):
    def test_capabilities_and_error(self):
        from geocontext.adapters.wfs import feature_types, require_feature_type
        from geocontext.adapters.wms import layer_names
        from geocontext.adapters.arcgis import layers
        wfs=b'<WFS_Capabilities><FeatureTypeList><FeatureType><Name>etak:e_501_tee_j</Name></FeatureType></FeatureTypeList></WFS_Capabilities>'
        self.assertEqual(feature_types(wfs), ['etak:e_501_tee_j'])
        self.assertEqual(require_feature_type(wfs,'etak:e_501_tee_j'), 'etak:e_501_tee_j')
        with self.assertRaises(ValueError): require_feature_type(wfs,'etak:missing')
        with self.assertRaises(ValueError): feature_types(b'<!DOCTYPE x [<!ENTITY a "b">]><x/>')
        self.assertEqual(layer_names(b'<WMS_Capabilities><Layer><Name>of2025aero</Name></Layer></WMS_Capabilities>'), ['of2025aero'])
        self.assertEqual(layers(b'{"layers":[{"id":9,"name":"Roads"}]}')[0]['id'],9)
        with self.assertRaises(ValueError): layers(b'{"error":{"code":500}}')

class HttpPolicyTests(unittest.TestCase):
    def test_exact_hosts_paths_and_no_credentials(self):
        from geocontext.http_policy import validate_endpoint
        allowed={('gsavalik.envir.ee','/geoserver/etak/wfs')}
        url='https://gsavalik.envir.ee/geoserver/etak/wfs?service=WFS'
        self.assertEqual(validate_endpoint(url,allowed), ('gsavalik.envir.ee','/geoserver/etak/wfs'))
        for bad in ('http://gsavalik.envir.ee/geoserver/etak/wfs',
                    'https://user@gsavalik.envir.ee/geoserver/etak/wfs',
                    'https://gsavalik.envir.ee/geoserver/etak/wfs/extra',
                    'https://gsavalik.envir.ee/geoserver/etak/%77fs',
                    'https://gsavalik.envir.ee.evil.example/geoserver/etak/wfs',
                    'https://127.0.0.1/geoserver/etak/wfs',
                    url+'&token=secret'):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                validate_endpoint(bad,allowed)
