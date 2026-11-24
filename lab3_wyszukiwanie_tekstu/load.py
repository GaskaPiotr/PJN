"""Create and load three independent sample sizes; never reset data without --replace."""

import argparse
import csv
import hashlib
import io
import itertools
import time
import zipfile

from common import DATASET, RESULTS, ROOT, SIZES, Solr, collection, elapsed_ms, pg_connect, solr_doc, table, write_json

BATCH = 2000
FIELDS = 'id,title,body,category,region,year'


def load_pg(size, replace):
    name = table(size)
    schema = (ROOT / 'sql' / 'schema.sql').read_text().format(table=name)
    index = (ROOT / 'sql' / 'index.sql').read_text().format(table=name, index=f'{name}_gin')
    copy = f'COPY {name} ({FIELDS}) FROM STDIN WITH (FORMAT CSV, HEADER TRUE)'
    analyze = f'ANALYZE {name}'
    with pg_connect() as db, db.cursor() as cursor:
        if replace:
            cursor.execute(f'DROP TABLE IF EXISTS {name}')
        cursor.execute(schema)
        start = time.perf_counter()
        with DATASET.open('rb') as source, cursor.copy(copy) as sink:
            sink.write(source.readline())
            rows = itertools.islice(source, size)
            for chunk in itertools.batched(rows, BATCH):
                sink.write(b''.join(chunk))
        copy_ms = elapsed_ms(start)
        print(f'{name}: COPY {copy_ms / 1000:.2f} s', flush=True)
        start = time.perf_counter()
        cursor.execute(index)
        index_ms = elapsed_ms(start)
        start = time.perf_counter()
        cursor.execute(analyze)
        analyze_ms = elapsed_ms(start)
        cursor.execute(f"""
            SELECT count(*), min(id), max(id), pg_relation_size('{name}'),
                   pg_relation_size('{name}_gin'), pg_total_relation_size('{name}')
            FROM {name}
        """)
        count, min_id, max_id, heap_bytes, gin_bytes, total_bytes = cursor.fetchone()
    if (count, min_id, max_id) != (size, 1, size):
        raise ValueError(f'{name}: wrong ids or count: {count}, {min_id}, {max_id}')
    print(f'{name}: GIN {index_ms / 1000:.2f} s', flush=True)
    return {'records': count, 'copy_ms': copy_ms, 'gin_ms': index_ms, 'analyze_ms': analyze_ms,
            'heap_bytes': heap_bytes, 'gin_bytes': gin_bytes, 'total_bytes': total_bytes,
            'copy': copy, 'index': index.strip(), 'analyze': analyze}


def ensure_config(solr):
    files = [(path.name, path.read_bytes()) for path in sorted((ROOT / 'solr').iterdir())]
    digest = hashlib.sha256()
    for name, data in files:
        digest.update(name.encode() + b'\0' + data + b'\0')
    config = f'lab3_field_notes_{digest.hexdigest()[:12]}'
    listed, _ = solr.request('admin/configs', {'action': 'LIST', 'wt': 'json'})
    if config in listed['configSets']:
        return config
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in files:
            archive.writestr(name, data)
    solr.request('admin/configs', {'action': 'UPLOAD', 'name': config, 'wt': 'json'}, archive=buffer.getvalue())
    return config


def load_solr(size, replace):
    solr = Solr()
    config = ensure_config(solr)
    name = collection(size)
    existing, _ = solr.request('admin/collections', {'action': 'LIST', 'wt': 'json'})
    if name in existing['collections']:
        if not replace:
            raise ValueError(f'{name} already exists; use --replace to rebuild it')
        solr.request('admin/collections', {'action': 'DELETE', 'name': name, 'wt': 'json'})
    solr.request('admin/collections', {'action': 'CREATE', 'name': name, 'numShards': 1,
                                      'replicationFactor': 1, 'collection.configName': config, 'wt': 'json'})
    endpoint = f'{name}/update'
    params = {'wt': 'json'}
    durations = []
    start = time.perf_counter()
    with DATASET.open(encoding='utf-8', newline='') as source:
        rows = itertools.islice(csv.DictReader(source), size)
        for batch_index, chunk in enumerate(itertools.batched(rows, BATCH), 1):
            result, client_ms = solr.request(endpoint, params, payload=[solr_doc(row) for row in chunk])
            durations.append({'batch': batch_index, 'docs': len(chunk), 'server_ms': result['responseHeader']['QTime'],
                              'client_ms': client_ms})
            if batch_index % 25 == 0:
                print(f'{name}: {batch_index * BATCH:,}/{size:,} wysłanych', flush=True)
    upload_ms = elapsed_ms(start)
    start = time.perf_counter()
    commit, commit_client_ms = solr.request(endpoint, params, payload={'commit': {'waitSearcher': True}})
    commit_ms = elapsed_ms(start)
    check, _ = solr.request(f'{name}/select', {'q': '*:*', 'rows': 0})
    count = check['response']['numFound']
    if count != size:
        raise ValueError(f'{name}: indexed {count} instead of {size}')
    print(f'{name}: batch {upload_ms / 1000:.2f} s + commit {commit_ms / 1000:.2f} s', flush=True)
    return {'records': count, 'batch_size': BATCH, 'upload_ms': upload_ms, 'commit_ms': commit_ms,
            'commit_client_ms': commit_client_ms, 'commit_qtime_ms': commit['responseHeader']['QTime'],
            'url': solr.url(endpoint, params), 'batches': durations}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('system', choices=('pg', 'solr'))
    parser.add_argument('sizes', nargs='*', type=int, choices=SIZES, default=[])
    parser.add_argument('--replace', action='store_true')
    args = parser.parse_args()
    loader = load_pg if args.system == 'pg' else load_solr
    for size in args.sizes or SIZES:
        write_json(RESULTS / f'load_{args.system}_{size}.json', loader(size, args.replace))
