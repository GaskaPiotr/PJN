"""Change two demo notes and delete one in PostgreSQL, mirror Solr, then restore."""

import argparse
import json
import time

from psycopg.rows import dict_row

from common import RESULTS, ROOT, SIZES, Solr, collection, elapsed_ms, pg_connect, solr_doc, table, write_json

SIZE = SIZES[-1]
TABLE = table(SIZE)
COLLECTION = collection(SIZE)
CHANGE = (13, 37)
REMOVE = 81
IDS = [*CHANGE, REMOVE]
FIELDS = 'id,title,body,category,region,year'
TOKEN = 'calibration'
SENTENCE = ' The calibration was repeated before the instrument was packed away.'
BACKUP = ROOT / '.runtime' / 'sync_backup.json'


def select_rows(cursor):
    cursor.execute(f'SELECT {FIELDS} FROM {TABLE} WHERE id = ANY(%s) ORDER BY id', (IDS,))
    return cursor.fetchall()


def snapshot(cursor, solr):
    query = f"""
SELECT id FROM {TABLE}
WHERE search_vector @@ to_tsquery('english', '{TOKEN}') ORDER BY id
""".strip()
    now = time.perf_counter()
    cursor.execute(query)
    sql_hit_ids = [row['id'] for row in cursor.fetchall()]
    sql_client_ms = elapsed_ms(now)
    count_query = f'SELECT count(*) AS records FROM {TABLE}'
    cursor.execute(count_query)
    sql_total = cursor.fetchone()['records']
    sql_rows = select_rows(cursor)
    select = f'{COLLECTION}/select'
    search = {'q': TOKEN, 'defType': 'edismax', 'qf': 'title^3 body', 'fl': 'id', 'sort': 'id asc', 'rows': 10}
    matches, client_ms = solr.request(select, search)
    solr_total, _ = solr.request(select, {'q': '*:*', 'rows': 0})
    lookup = {'q': 'id:(' + ' OR '.join(f'{value:06}' for value in IDS) + ')',
              'fl': FIELDS, 'sort': 'id asc', 'rows': len(IDS)}
    solr_rows, _ = solr.request(select, lookup)
    solr_hit_ids = [int(doc['id']) for doc in matches['response']['docs']]
    if matches['response']['numFound'] != len(sql_hit_ids) or sql_hit_ids != solr_hit_ids:
        raise ValueError((sql_hit_ids, solr_hit_ids))
    if sql_total != solr_total['response']['numFound'] or [solr_doc(row) for row in sql_rows] != solr_rows['response']['docs']:
        raise ValueError('Stored data differs between systems')
    return {'postgres': {'total': sql_total, 'hits': sql_hit_ids, 'query': query,
                         'count_query': count_query, 'client_ms': sql_client_ms},
            'solr': {'total': solr_total['response']['numFound'], 'hits': solr_hit_ids,
                     'url': solr.url(select, search), 'lookup_url': solr.url(select, lookup),
                     'qtime_ms': matches['responseHeader']['QTime'], 'client_ms': client_ms},
            'present_ids': [row['id'] for row in sql_rows], 'fields_equal': True}


def mirror(solr, rows, absent=()):
    endpoint = f'{COLLECTION}/update'
    writes = []
    if rows:
        result, client = solr.request(endpoint, payload=[solr_doc(row) for row in rows])
        writes.append({'add_or_replace': [row['id'] for row in rows], 'qtime_ms': result['responseHeader']['QTime'],
                       'client_ms': client})
    if absent:
        result, client = solr.request(endpoint, payload={'delete': [f'{value:06}' for value in absent]})
        writes.append({'delete': list(absent), 'qtime_ms': result['responseHeader']['QTime'], 'client_ms': client})
    result, client = solr.request(endpoint, payload={'commit': {'waitSearcher': True}})
    writes.append({'commit': True, 'qtime_ms': result['responseHeader']['QTime'], 'client_ms': client})
    return {'url': solr.url(endpoint), 'actions': writes}


def restore(db, cursor, solr, backup):
    insert = f"""
INSERT INTO {TABLE} ({FIELDS}) VALUES (%(id)s,%(title)s,%(body)s,%(category)s,%(region)s,%(year)s)
ON CONFLICT (id) DO UPDATE SET title=excluded.title, body=excluded.body, category=excluded.category,
                               region=excluded.region, year=excluded.year
""".strip()
    with db.transaction():
        cursor.executemany(insert, backup)
    writes = mirror(solr, backup)
    restored = snapshot(cursor, solr)
    if restored['present_ids'] != IDS or restored['postgres']['total'] != SIZE or restored['postgres']['hits']:
        raise ValueError('Lab dataset not restored')
    BACKUP.unlink()
    return {'sql': insert, 'solr': writes, 'snapshot': restored}


def demo(db, cursor, solr):
    if BACKUP.exists():
        raise ValueError('Existing backup: run sync_demo.py --restore first')
    before = snapshot(cursor, solr)
    if before['postgres']['hits'] or before['present_ids'] != IDS or before['postgres']['total'] != SIZE:
        raise ValueError('Run on the complete baseline corpus')
    backup = select_rows(cursor)
    write_json(BACKUP, backup)
    update = f'UPDATE {TABLE} SET body = body || %s WHERE id = ANY(%s)'
    delete = f'DELETE FROM {TABLE} WHERE id = %s'
    try:
        with db.transaction():
            cursor.execute(update, (SENTENCE, list(CHANGE)))
            if cursor.rowcount != len(CHANGE):
                raise ValueError('Unexpected update count')
            cursor.execute(delete, (REMOVE,))
            if cursor.rowcount != 1:
                raise ValueError('Unexpected delete count')
        writes = mirror(solr, select_rows(cursor), (REMOVE,))
        after = snapshot(cursor, solr)
        if after['postgres']['hits'] != list(CHANGE) or after['postgres']['total'] != SIZE - 1:
            raise ValueError('Unexpected result after synchronization')
    finally:
        restored = restore(db, cursor, solr, backup)
    write_json(RESULTS / 'sync.json', {
        'before': before, 'mutation': {'sql': [update, delete], 'update_parameters': [SENTENCE, list(CHANGE)],
                                       'delete_parameters': [REMOVE], 'solr': writes},
        'after': after, 'restore': restored,
    })
    print(f'Zgodność SQL i Solr: {after["postgres"]["hits"]}; usunięty {REMOVE}. Korpus przywrócony.', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--restore', action='store_true', help='Complete recovery from the local backup.')
    args = parser.parse_args()
    with pg_connect() as db, db.cursor(row_factory=dict_row) as cursor:
        if args.restore:
            restore(db, cursor, Solr(), json.loads(BACKUP.read_text(encoding='utf-8')))
        else:
            demo(db, cursor, Solr())
