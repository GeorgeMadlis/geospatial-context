"""Extract exact-day filename observations from saved listing HTML, offline."""
from datetime import date
from html.parser import HTMLParser
from urllib.parse import parse_qs, unquote, urlsplit
import re

class _Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.names = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() == 'a':
            self.names.extend(v for k, v in attrs if k.lower() == 'href' and v)


def listing_dates(html):
    """Return exact full dates in filenames, not retrieval or acquisition claims.

    Ambiguous ranges and year-only entries are omitted, rather than inventing a day.
    """
    parser = _Links()
    parser.feed(html)
    results = set()
    for link in parser.names:
        parts = urlsplit(link)
        candidates = parse_qs(parts.query).get('f', [])
        if not candidates:
            candidates = [unquote(parts.path.rsplit('/', 1)[-1])]
        for filename in candidates:
            # A range like 2002_08_07-08_10 is not one exact observation.
            if re.search(r'\d{4}[_-]\d{2}[_-]\d{2}[-_]\d{2}[_-]\d{2}', filename):
                continue
            for match in re.findall(r'(?<!\d)(\d{4})[_-](\d{2})[_-](\d{2})(?!\d)', filename):
                try:
                    results.add(date(*(int(v) for v in match)).isoformat())
                except ValueError:
                    pass
    return sorted(results)
