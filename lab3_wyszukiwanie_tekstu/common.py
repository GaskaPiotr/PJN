"""Local clients and paths used by the loaders and experiments."""

import http.client
import json
import os
import time
from pathlib import Path
from urllib.parse import urlencode, urlsplit

import psycopg

from generate import ROOT, SIZES

RESULTS = ROOT / 'results'
DATASET = ROOT / 'data' / 'field_notes.csv'
SOLR = os.environ.get('LAB3_SOLR', 'http://127.0.0.1:18983/solr').rstrip('/')
PG = os.environ.get('LAB3_PG', 'host=127.0.0.1 port=15436 dbname=postgres user=lab3')


def table(size):
    if size not in SIZES:
        raise ValueError(size)
    return f'field_notes_{size}'


def collection(size):
    return f'lab3_{size}'


def pg_connect(*, autocommit=True):
    return psycopg.connect(PG, autocommit=autocommit, connect_timeout=10)


def elapsed_ms(start):
    return (time.perf_counter() - start) * 1000


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    temporary.replace(path)


class Solr:
    def __init__(self, base=SOLR):
        self.base = base
        parsed = urlsplit(base)
        connection = http.client.HTTPSConnection if parsed.scheme == 'https' else http.client.HTTPConnection
        self.connection = connection(parsed.netloc, timeout=180)
        self.path = parsed.path

    def url(self, endpoint, params=()):
        return f'{self.base}/{endpoint}?{urlencode(params, doseq=True)}'

    def request(self, endpoint, params=(), *, payload=None, archive=None):
        headers = {}
        body = None
        if payload is not None:
            headers['Content-Type'] = 'application/json; charset=utf-8'
            body = json.dumps(payload, ensure_ascii=False, separators=(',', ':')).encode()
        if archive is not None:
            headers['Content-Type'] = 'application/octet-stream'
            body = archive
        target = f'{self.path}/{endpoint}?{urlencode(params, doseq=True)}'
        started = time.perf_counter()
        self.connection.request('POST' if body is not None else 'GET', target, body, headers)
        response = self.connection.getresponse()
        raw = response.read()
        if response.status != 200:
            raise RuntimeError(f'Solr HTTP {response.status} {target}: {raw[:5000].decode(errors="replace")}')
        result = json.loads(raw)
        if result.get('responseHeader', {}).get('status', 0):
            raise RuntimeError(result)
        return result, elapsed_ms(started)


def solr_doc(row):
    document = dict(row)
    document['id'] = f'{int(row["id"]):06}'
    document['year'] = int(row['year'])
    return document
