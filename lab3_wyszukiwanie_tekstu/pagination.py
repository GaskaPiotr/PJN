"""Compare deep offsets with sequential cursors on the same stable sort."""

import hashlib
import json
from statistics import median

from common import RESULTS, SIZES, Solr, collection, write_json

SIZE = 1000
OFFSETS = (1_000, 50_000, 250_000)


def ids(result):
    return [doc['id'] for doc in result['response']['docs']]


def experiment(solr, stream):
    endpoint = f'{collection(SIZES[-1])}/select'
    params = {'q': '*:*', 'fl': 'id,year', 'rows': SIZE, 'sort': 'year asc,id asc', 'wt': 'json'}

    def page(label, pagination, run=None):
        request_params = params | pagination
        result, client_ms = solr.request(endpoint, request_params)
        records = ids(result)
        sample = {'approach': label, 'run': run, 'warmup': run == 1,
                  'url': solr.url(endpoint, request_params), 'count': result['response']['numFound'],
                  'page_count': len(records), 'first': records[0], 'last': records[-1],
                  'qtime_ms': result['responseHeader']['QTime'], 'client_ms': client_ms}
        stream.write(json.dumps(sample) + '\n')
        stream.flush()
        return result, sample

    previous_mark = '*'
    preceding_client = []
    previous_sort_key = None
    targets = {}
    for offset in range(0, OFFSETS[-1] + SIZE, SIZE):
        mark = previous_mark
        answer, sequential = page('cursor_walk', {'cursorMark': mark})
        previous_mark = answer['nextCursorMark']
        if mark == previous_mark:
            raise ValueError(f'Cursor stopped at {offset}')
        for document in answer['response']['docs']:
            sort_key = (document['year'], document['id'])
            if previous_sort_key is not None and sort_key <= previous_sort_key:
                raise ValueError(f'Cursor skipped ordering at {offset}')
            previous_sort_key = sort_key
        if offset in OFFSETS:
            timings = {}
            for label, position in (('start', {'start': offset}), ('cursor', {'cursorMark': mark})):
                samples = []
                for run in range(1, 7):
                    result, sample = page(label, position, run)
                    if ids(result) != ids(answer):
                        raise ValueError(f'Pages differ at offset {offset}')
                    samples.append(sample)
                timings[label] = {'samples': samples, 'qtime_ms': median(s['qtime_ms'] for s in samples[1:]),
                                  'client_ms': median(s['client_ms'] for s in samples[1:])}
            targets[offset] = {'offset': offset, 'rows': SIZE, 'ids_equal': True,
                               'page_id_sha256': hashlib.sha256(','.join(ids(answer)).encode()).hexdigest(),
                               'earlier_requests': len(preceding_client),
                               'earlier_client_ms': sum(preceding_client), **timings}
            print(f'Odstęp {offset:,}: start = {timings["start"]["qtime_ms"]} ms, '
                  f'cursor = {timings["cursor"]["qtime_ms"]} ms', flush=True)
            write_json(RESULTS / 'pagination.json', targets)
        preceding_client.append(sequential['client_ms'])


if __name__ == '__main__':
    with (RESULTS / 'measurements_pagination.jsonl').open('w', encoding='utf-8') as stream:
        experiment(Solr(), stream)
