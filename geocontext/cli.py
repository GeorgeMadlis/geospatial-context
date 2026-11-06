"""Offline CLI for source inspection and bounded local fixture operations."""
import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path
from .catalog import sources, describe
from .geometry import measure
from .orthophoto import listing_dates
from .fixtures import query
from .events import record, timestamp


def main(argv=None):
    parser = argparse.ArgumentParser(prog='geocontext')
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('list-sources'); p.add_argument('--format', choices=['json','table'], default='json')
    p = sub.add_parser('describe-layer'); p.add_argument('source_id'); p.add_argument('--format', choices=['json','table'], default='json')
    p = sub.add_parser('orthophoto-dates'); p.add_argument('html')
    p = sub.add_parser('measure'); p.add_argument('geometry_a'); p.add_argument('geometry_b'); p.add_argument('--buffer-m', type=float, default=0); p.add_argument('--angle-tolerance-deg', type=float, default=15)
    p = sub.add_parser('query-layer'); p.add_argument('source_id'); p.add_argument('--fixture', required=True); p.add_argument('--aoi', required=True); p.add_argument('--fixture-crs', choices=['EPSG:4326','EPSG:3301'], required=True); p.add_argument('--max-features', type=int, default=1000)
    for name in ('export-snapshot', 'show-tool-ledger'):
        sub.add_parser(name)
    args = parser.parse_args(argv)
    started, clock = timestamp(), time.monotonic()
    params = vars(args).copy()
    params['input_sha256'] = {}
    for name in ('fixture', 'aoi', 'html', 'geometry_a', 'geometry_b'):
        filename = getattr(args, name, None)
        if filename:
            try:
                h = hashlib.sha256()
                with Path(filename).open('rb') as stream:
                    for block in iter(lambda: stream.read(1024 * 1024), b''):
                        h.update(block)
                params['input_sha256'][name] = h.hexdigest()
            except OSError:
                params['input_sha256'][name] = None
    source_ids = [getattr(args, 'source_id', None) or ('DS-0023' if args.command == 'orthophoto-dates' else 'LOCAL-INPUT')]
    if args.command == 'list-sources':
        source_ids = [s['id'] for s in sources()]
    try:
        if args.command == 'list-sources': result = sources()
        elif args.command == 'describe-layer':
            result = describe(args.source_id)
            if result is None: raise ValueError('unknown source ID')
        elif args.command == 'orthophoto-dates':
            data = Path(args.html).read_bytes()
            result = {'source_sha256':hashlib.sha256(data).hexdigest(), 'dates':listing_dates(data.decode('utf-8')), 'interpretation':'filename observations only'}
        elif args.command == 'measure':
            result = measure(json.loads(Path(args.geometry_a).read_text()), json.loads(Path(args.geometry_b).read_text()), args.buffer_m, args.angle_tolerance_deg)
        elif args.command == 'query-layer':
            result = query(args.source_id, args.fixture, json.loads(Path(args.aoi).read_text()), args.fixture_crs, args.max_features)
        elif args.command == 'show-tool-ledger':
            ledger = Path(os.environ.get('GEOCONTEXT_LEDGER_DIR', '.geocontext')) / 'tool_executions.jsonl'
            data = ledger.read_bytes() if ledger.exists() else b''
            if len(data) > 5_000_000: raise ValueError('ledger exceeds 5 MB; use an external viewer')
            result = {'events':[json.loads(line) for line in data.splitlines()], 'note':'The present invocation is appended after this snapshot.'}
        else:
            raise ValueError('not implemented; no provider calls were made')
        error = None
    except Exception as exc:
        error = str(exc) or type(exc).__name__
        result = {'error':error, 'status':'not_queried'}
    try:
        record(args.command, params, result, started, timestamp(), round((time.monotonic()-clock)*1000, 3), source_ids, error)
    except Exception as exc:
        print(json.dumps({'error':f'could not record execution: {type(exc).__name__}', 'status':'logging_failed'}), file=sys.stderr)
        return 3
    output = sys.stderr if error else sys.stdout
    if getattr(args,'format',None) == 'table' and not error:
        rows = result if isinstance(result,list) else [result]
        print('ID\tDATASET\tPROTOCOL\tSTATUS', file=output)
        for row in rows:
            print(f"{row['id']}\t{row['dataset']}\t{row['protocol']}\t{row['adapter_status']}", file=output)
    else:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(',', ':')), file=output)
    return 2 if error else 0

if __name__ == '__main__':
    sys.exit(main())
