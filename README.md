# geospatial-context

An early offline prototype for inspectable geospatial context, not yet an operational retrieval service. Forest Cover Lab remains the scientific authority. Its proposed contracts are temporarily pinned in [docs/lab-pin.md](docs/lab-pin.md); Hansen annual loss is weak supervision, not monthly ground truth.

On a Mac mini with Python 3.11 or later:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/python scripts/offline_tests.py
.venv/bin/geocontext list-sources
.venv/bin/geocontext describe-layer DS-0022 --format table
```

Catalogue entries are candidates, not claims that an adapter exists or a provider has been queried. `query-layer DS-0016 --fixture /private/path/features.geojson --fixture-crs EPSG:3301 --aoi /private/path/aoi-geometry.json` filters a **local** GeoJSON response against an EPSG:4326 GeoJSON geometry. It retains native feature properties and IDs; it does not establish coverage or absence outside that response. `orthophoto-dates /private/path/listing.html` extracts exact dates from local filenames, not verified image acquisition dates. `measure /private/path/a.json /private/path/b.json --buffer-m 20` reports EPSG:3301 distances, geometries and alignment diagnostics; any area is calculated geodesically in hectares. Alignment compares segments with the endpoint bearing of the longest reference line, so curved or branched features need review. None of these commands classifies a feature or determines cause.

Calls write a local append-only JSONL ledger and protected request/response files under `.geocontext/`; set `GEOCONTEXT_LEDGER_DIR` to another private directory and `GEOCONTEXT_INSTANCE_ID` to the actual round instance. `show-tool-ledger` shows previous events and then records its own invocation. Each event is checked against the pinned candidate Lab event schema. The locally retained tool response is not a provider raw response, and file paths in requests must remain available for replay. `LOCAL-INPUT` denotes locally supplied geometries and is not a Lab dataset identifier. Ledger validation does not prove that an event occurred or enforce append-only history against outside modification.

Source names, retained-request paths and tool output can be sensitive. Do not commit `.geocontext/`, case images or third-party files to a public repository without checking their terms. The [offline replay progress report](docs/offline-replay-progress.md) documents checks against local October records. No provider connection is implemented. Live calls, URL allowlisting, retry/cache policy, full WFS/WMS/ArcGIS adapters, complete fixture replay, snapshot export, cross-record validation and an independent challenge remain outstanding. `export-snapshot` currently returns an error. Passing local tests is not scientific validation.
