"""Equivalent query definitions and repeatable Solr request parameters."""

SEARCH = {
    'Q1': ('restore', "to_tsquery('english', 'restore')"),
    'Q2': ('"solar panel"', "phraseto_tsquery('english', 'solar panel')"),
    'Q3': ('habitat AND (wetland OR marsh) AND NOT invasive',
           "to_tsquery('english', 'habitat & (wetland | marsh) & !invasive')"),
}


def contains(fragment):
    return f"(lower(title) LIKE '%{fragment}%' OR lower(body) LIKE '%{fragment}%')"


LIKE = {
    'Q1': contains('restore'),
    'Q2': contains('solar panel'),
    'Q3': f"{contains('habitat')} AND ({contains('wetland')} OR {contains('marsh')}) AND NOT {contains('invasive')}",
}
YEAR_SQL = 'year BETWEEN 2000 AND 2024'
YEAR_SOLR = 'year:[2000 TO 2024]'


def fulltext(key):
    return f'search_vector @@ {SEARCH[key][1]}'


def solr_params(key, rows=0):
    return {'q': SEARCH[key][0], 'fq': YEAR_SOLR, 'defType': 'edismax', 'qf': 'title^3 body',
            'fl': 'id,title,category,region,year,score', 'sort': 'score desc,id asc',
            'rows': rows, 'wt': 'json'}
