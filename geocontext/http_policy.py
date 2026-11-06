"""Validation helpers for future requests; this module performs no network access.

These checks alone do not defend against DNS rebinding. No live transport is enabled.
"""
from urllib.parse import urlsplit, parse_qsl
import ipaddress

FORBIDDEN_KEYS = {'token', 'key', 'api_key', 'apikey', 'access_token', 'authorization', 'password'}


def validate_endpoint(url, allowed_paths):
    """Require an explicitly authorized HTTPS host and exact, unescaped path."""
    if not isinstance(url, str) or any(ord(c) < 33 or ord(c) == 127 for c in url):
        raise ValueError('URL contains invalid characters')
    value = urlsplit(url)
    if value.scheme != 'https' or not value.hostname or value.username or value.password or value.fragment:
        raise ValueError('only credential-free HTTPS URLs are permitted')
    try:
        port = value.port
    except ValueError as exc:
        raise ValueError('invalid URL port') from exc
    if port not in (None, 443):
        raise ValueError('nonstandard ports are not permitted')
    host = value.hostname.lower()
    try:
        ipaddress.ip_address(host)
    except ValueError:
        pass
    else:
        raise ValueError('IP literals are not permitted')
    if '%' in value.path or not value.path.startswith('/') or (host, value.path) not in allowed_paths:
        raise ValueError('host or exact path is not permitted')
    if any(k.lower() in FORBIDDEN_KEYS for k, _ in parse_qsl(value.query, keep_blank_values=True)):
        raise ValueError('credentials in query strings are not permitted')
    return host, value.path
