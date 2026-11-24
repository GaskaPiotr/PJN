"""Save exact queries, raw timings and raw plans for all measured runs."""

import argparse
import html
import json
import statistics
import time

from psycopg.rows import dict_row

from common import RESULTS, ROOT, SIZES, Solr, collection, elapsed_ms, pg_connect, solr_doc, table, write_json
from queries import LIKE, SEARCH, YEAR_SQL, contains, fulltext, solr_params

RUNS = 6
EXPLAIN = 'EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, FORMAT JSON) '


class Measurements:
    def __init__(self, cursor, solr, stream):
        self.cursor = cursor
        self.solr = solr
        self.stream = stream

    def log(self, sample):
        self.stream.write(json.dumps(sample, ensure_ascii=False) + '\n')
        self.stream.flush()

    def sql(self, label, query, count_results=None):
        sql = query.strip()
        plans = []
        for index in range(RUNS):
            self.cursor.execute(EXPLAIN + sql)
            plans.append(self.cursor.fetchone()['QUERY PLAN'][0])
        started = time.perf_counter()
        self.cursor.execute(sql)
        result = self.cursor.fetchall()
        result_ms = elapsed_ms(started)
        num_found = count_results(result) if count_results else len(result)
        samples = []
        for index, plan in enumerate(plans):
            sample = {'label': label, 'system': 'PostgreSQL', 'run': index + 1, 'warmup': index == 0,
                      'query': EXPLAIN + sql, 'count': num_found, 'server_ms': plan['Execution Time'],
                      'plan': plan}
            self.log(sample)
            samples.append(sample['server_ms'])
        return {'count': num_found, 'rows': result, 'query': sql, 'result_client_ms': result_ms,
                'server_ms': samples, 'second_ms': samples[1], 'median_ms': statistics.median(samples[1:])}

    def http(self, label, endpoint, params):
        samples, client = [], []
        for index in range(RUNS):
            result, elapsed = self.solr.request(endpoint, params)
            header = result['responseHeader']
            count = result['response']['numFound']
            samples.append(header['QTime'])
            client.append(elapsed)
            self.log({'label': label, 'system': 'Solr', 'run': index + 1, 'warmup': index == 0,
                      'query': self.solr.url(endpoint, params), 'count': count,
                      'server_ms': header['QTime'], 'client_ms': elapsed})
        return {'count': count, 'result': result, 'query': self.solr.url(endpoint, params),
                'server_ms': samples, 'client_ms': client, 'second_ms': samples[1],
                'median_ms': statistics.median(samples[1:]), 'median_client_ms': statistics.median(client[1:])}


def counts(measure):
    raw = {}
    for size in SIZES:
        name = table(size)
        endpoint = f'{collection(size)}/select'
        raw[size] = {}
        for key in SEARCH:
            subgroup = {}
            for method, predicate in (('like', LIKE[key]), ('fts', fulltext(key))):
                statement = f'SELECT count(*) FROM {name} WHERE {YEAR_SQL} AND ({predicate})'
                subgroup[method] = measure.sql(f'{size}.{key}.{method}', statement, extract_count)
            subgroup['solr'] = measure.http(f'{size}.{key}.solr', endpoint, solr_params(key))
            raw[size][key] = subgroup
            print(f'{size} {key}: ' +
                  ', '.join(f'{method} {value["count"]:,} / {value["median_ms"]:.2f} ms'
                            for method, value in subgroup.items()), flush=True)
        write_json(RESULTS / 'counts.json', raw)


def extract_count(rows):
    return rows[0]['count']


def rank(measure):
    size = SIZES[-1]
    ranks = {}
    for key, (_, tsquery) in SEARCH.items():
        statement = f"""
SELECT id, title, category, region, year, ts_rank_cd(search_vector, {tsquery}) AS score
FROM {table(size)}
WHERE {YEAR_SQL} AND {fulltext(key)}
ORDER BY score DESC, id ASC LIMIT 10
"""
        params = solr_params(key, rows=10)
        params.update({'hl': 'true', 'hl.fl': 'body', 'hl.method': 'unified', 'hl.snippets': 1})
        sql = measure.sql(f'rank.{key}.sql', statement)
        solr = measure.http(f'rank.{key}.solr', f'{collection(size)}/select', params)
        ids_sql = {row['id'] for row in sql['rows']}
        ids_solr = {int(row['id']) for row in solr['result']['response']['docs']}
        overlap = sorted(ids_sql & ids_solr)
        if len(ids_sql) != 10 or len(ids_solr) != 10 or not solr['result'].get('highlighting'):
            raise ValueError(f'{key}: incomplete ranking or highlighting')
        ranks[key] = {'sql': sql, 'solr': solr, 'overlap': overlap}
    write_json(RESULTS / 'rankings.json', ranks)
    return ranks


def facet_counts(measure):
    size = SIZES[-1]
    params = solr_params('Q3')
    params.update({'facet': 'true', 'facet.field': ['category', 'region'], 'facet.range': 'year',
                   'facet.range.start': 2000, 'facet.range.end': 2025, 'facet.range.gap': 5,
                   'facet.range.hardend': 'true', 'facet.mincount': 1, 'facet.sort': 'index'})
    solr = measure.http('facet.solr', f'{collection(size)}/select', params)
    result = solr['result']['facet_counts']
    solr_buckets = {name: dict(zip(values[::2], values[1::2]))
                    for name, values in result['facet_fields'].items()}
    years = result['facet_ranges']['year']['counts']
    solr_buckets['year'] = dict(zip(years[::2], years[1::2]))
    match = f'FROM {table(size)} WHERE {YEAR_SQL} AND {fulltext("Q3")}'
    sql = {}
    buckets = {'category': 'category', 'region': 'region', 'year': '2000 + 5 * ((year - 2000) / 5)'}
    for label, expression in buckets.items():
        statement = f'SELECT {expression} AS bucket, count(*) {match} GROUP BY 1 ORDER BY 1'
        sql[label] = measure.sql(f'facet.{label}', statement, sum_buckets)
        postgres_buckets = {str(row['bucket']): row['count'] for row in sql[label]['rows']}
        if postgres_buckets != solr_buckets[label]:
            raise ValueError((label, postgres_buckets, solr_buckets[label]))
    combined = f"""
SELECT CASE WHEN GROUPING(category) = 0 THEN 'category'
            WHEN GROUPING(region) = 0 THEN 'region' ELSE 'year' END AS dimension,
       COALESCE(category, region, (2000 + 5 * ((year - 2000) / 5))::text) AS bucket,
       count(*)
{match}
GROUP BY GROUPING SETS ((category), (region), (2000 + 5 * ((year - 2000) / 5)))
ORDER BY 1, 2
"""
    group_sets = measure.sql('facet.grouping_sets', combined,
                             lambda rows: sum(row['count'] for row in rows if row['dimension'] == 'category'))
    for label in buckets:
        observed = {row['bucket']: row['count'] for row in group_sets['rows'] if row['dimension'] == label}
        if observed != solr_buckets[label]:
            raise ValueError((label, observed, solr_buckets[label]))
    summed = [sum(times) for times in zip(*(group['server_ms'] for group in sql.values()))]
    write_json(RESULTS / 'facets.json', {'buckets': solr_buckets, 'sql': sql, 'grouping_sets': group_sets,
                                      'sql_sum_ms': summed, 'sql_sum_median_ms': statistics.median(summed[1:]),
                                      'solr': solr})


def sum_buckets(rows):
    return sum(row['count'] for row in rows)


def fuzzy(measure):
    size = SIZES[-1]
    endpoint = f'{collection(size)}/select'
    measured = {}
    for label, value in (('correct', 'solar'), ('typo', 'soalr'), ('fuzzy', 'soalr~1')):
        params = solr_params('Q1', rows=10)
        params['q'] = value
        measured[label] = measure.http(f'fuzzy.{label}', endpoint, params)
    for name, term in (('sql_correct', 'solar'), ('sql_typo', 'soalr')):
        statement = f'SELECT count(*) FROM {table(size)} WHERE {YEAR_SQL} AND {contains(term)}'
        measured[name] = measure.sql(f'fuzzy.{name}', statement, extract_count)
    if not (measured['typo']['count'] == measured['sql_typo']['count'] == 0 < measured['fuzzy']['count']):
        raise ValueError('Unexpected spelling experiment results')
    write_json(RESULTS / 'fuzzy.json', measured)


def verify_schema(solr):
    name = collection(SIZES[-1])
    overlay, _ = solr.request(f'{name}/config/overlay')
    if overlay['overlay']['userProps'].get('update.autoCreateFields') is not False:
        raise ValueError(overlay)
    example = json.loads((RESULTS / 'dataset.json').read_text(encoding='utf-8'))['example']
    example = solr_doc(example)
    example['lab3_unknown_field'] = 'test'
    try:
        solr.request(f'{name}/update', payload=[example])
    except RuntimeError as error:
        if 'unknown field' not in str(error).lower():
            raise
        write_json(RESULTS / 'schema_check.json', {
            'autoCreateFields': False,
            'url': solr.url(f'{name}/update'),
            'unknown_field': 'lab3_unknown_field',
            'unknown_field_error': str(error),
        })
    else:
        raise ValueError('Unexpectedly accepted a field outside the schema')


def write_browser_links(ranks, facets):
    rows = [(f'{key} {SEARCH[key][0]}', ranks[key]['solr']['query']) for key in SEARCH]
    rows.append(('Q3 – trzy facety', facets['solr']['query']))
    items = '\n'.join(f'<li><a href="{html.escape(url)}">{html.escape(label)}</a></li>' for label, url in rows)
    (ROOT / 'zapytania.html').write_text(
        '<!doctype html>\n<html lang="pl"><meta charset="utf-8"><title>Zapytania Solra</title>\n'
        '<h1>Laboratorium 3 – zapytania do Solra</h1>\n'
        '<p>Po uruchomieniu Solra i załadowaniu 500 000 dokumentów kliknij odnośnik, aby otworzyć odpowiedź JSON.</p>\n'
        f'<ol>\n{items}\n</ol>\n</html>\n', encoding='utf-8')
    write_json(RESULTS / 'browser_urls.json', dict(rows))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=('counts', 'features', 'all'), default='all', nargs='?')
    stage = parser.parse_args().stage
    solr = Solr()
    with pg_connect() as db, db.cursor(row_factory=dict_row) as cursor:
        if stage in ('counts', 'all'):
            with (RESULTS / 'measurements_counts.jsonl').open('w', encoding='utf-8') as stream:
                counts(Measurements(cursor, solr, stream))
        if stage in ('features', 'all'):
            verify_schema(solr)
            with (RESULTS / 'measurements_features.jsonl').open('w', encoding='utf-8') as stream:
                measure = Measurements(cursor, solr, stream)
                ranks = rank(measure)
                facet_counts(measure)
                fuzzy(measure)
            facets = json.loads((RESULTS / 'facets.json').read_text(encoding='utf-8'))
            write_browser_links(ranks, facets)
