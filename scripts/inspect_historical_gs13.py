"""Offline integrity check of a local GS-13 capture; no downloads or mutations."""
import argparse, hashlib, json
from pathlib import Path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('round_directory', type=Path)
    args = parser.parse_args()
    raw = args.round_directory / 'artifacts/geo-01/raw/etak'
    log = json.loads((raw / 'etak_fetch_log.json').read_text())
    results = []
    for item in log:
        # Historical absolute paths point at round-0002; use filename only after hash verification.
        path = raw / Path(item['file']).name
        data = path.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        count = len(json.loads(data).get('features', []))
        results.append({'roi':item['roi'], 'layer':item['layer'], 'retrieved_utc':item['retrieved_utc'],
                        'expected_sha256':item['sha256'], 'actual_sha256':digest,
                        'expected_bbox_count':item['n_features_bbox'], 'actual_bbox_count':count,
                        'match':digest == item['sha256'] and count == item['n_features_bbox']})
    print(json.dumps(results, sort_keys=True, indent=2))
    return 0 if all(item['match'] for item in results) else 1

if __name__ == '__main__':
    raise SystemExit(main())
