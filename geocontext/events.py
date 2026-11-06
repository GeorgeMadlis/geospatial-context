"""Private append-only observations of actual offline CLI calls."""
import hashlib
import json
import os
from pathlib import Path
from importlib.resources import files
from datetime import datetime, timezone
from uuid import uuid4
import jsonschema
from . import __version__


def encoded(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode('utf-8')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def timestamp():
    return datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')


def record(command, params, result, started, ended, elapsed, source_ids, error=None):
    """Write request, response and an event only after validating pinned schema.

    The private directory includes argument paths and output; the caller must choose a
    protected directory. Fixture mode means local input, never a provider invocation.
    """
    root = Path(os.environ.get('GEOCONTEXT_LEDGER_DIR', '.geocontext')).expanduser()
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    ident = str(uuid4())
    call_dir = root / 'calls' / ident
    call_dir.mkdir(mode=0o700, parents=True)
    request = encoded(params)
    response = encoded(result)
    request_file = call_dir / 'request.json'
    response_file = call_dir / 'response.json'
    for path, data in ((request_file, request), (response_file, response)):
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, 'wb') as stream:
            stream.write(data)
    event = {
        'schema_version':'1.0', 'call_id':ident, 'tool_id':'geocontext.' + command,
        'implementation_version_or_commit':__version__, 'agent_instance_id':os.environ.get('GEOCONTEXT_INSTANCE_ID','unassigned-local'),
        'source_ids':source_ids, 'availability':'available',
        'availability_observation_ref':str(response_file), 'invocation_observation_ref':str(response_file),
        'timing':{'measurement':'measured', 'started_utc':started, 'ended_utc':ended, 'elapsed_ms':elapsed},
        'parameters':{'kind':'retained_input_hash', 'canonicalization':'json-sort-keys-utf8-v1',
                      'retained_input_ref':str(request_file), 'sha256':sha(request)},
        'mode':'offline_fixture', 'cache_or_fixture_ref':str(params.get('fixture') or params.get('html') or params.get('geometry_a') or files('geocontext').joinpath('sources.yaml')), 'request_sha256':sha(request),
        'response_sha256':sha(response), 'raw_response_ref':str(response_file),
        'outcome':'error' if error else 'success', 'error':error,
        'provenance_refs':[str(request_file),str(response_file)],
        'limitations':['Local CLI observation; no provider request or independent proof of execution.',
                       'Input paths are retained; preserve referenced files separately for full replay.']}
    schema = json.loads(files('geocontext').joinpath('schemas/tool_execution_event.schema.json').read_text())
    jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker()).validate(event)
    line = encoded(event) + b'\n'
    fd = os.open(root / 'tool_executions.jsonl', os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    try:
        import fcntl
        fcntl.flock(fd, fcntl.LOCK_EX)
        with os.fdopen(fd, 'ab', closefd=False) as stream:
            stream.write(line)
            stream.flush()
            os.fsync(stream.fileno())
        fcntl.flock(fd, fcntl.LOCK_UN)
    finally:
        os.close(fd)
    return event
