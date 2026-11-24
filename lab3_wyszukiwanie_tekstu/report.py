"""Build the PDF, the README result table, and the oral-exam notes from saved measurements."""

import json
import math
import os
import re
from html import escape
from pathlib import Path

from reportlab.graphics.shapes import Circle, Drawing, Line, PolyLine, Rect, String
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from generate import ROOT, SIZES

OUTPUT = ROOT / 'output' / 'pdf' / 'Sprawozdanie_LAB3.pdf'
NAVY = colors.HexColor('#12293C')
TEAL = colors.HexColor('#00796F')
BLUE = colors.HexColor('#2B59A2')
ORANGE = colors.HexColor('#AE520F')
TEXT = colors.HexColor('#203648')
MUTED = colors.HexColor('#4D6373')
PALE = colors.HexColor('#EFF5F7')
LINE = colors.HexColor('#D5E2E7')
WIDTH = 491
KEYS = ('Q1', 'Q2', 'Q3')
METHODS = ('like', 'fts', 'solr')
QUERIES = ('restore', '"solar panel"', 'habitat AND (wetland OR marsh) AND NOT invasive')


def read(name):
    return json.loads((ROOT / 'results' / f'{name}.json').read_text(encoding='utf-8'))


def number(value):
    return f'{value:,}'.replace(',', ' ')


def ms(value, digits=2):
    return f'{value:.{digits}f}'.replace('.', ',')


def seconds(value):
    return ms(value / 1000)


def mib(value):
    return ms(value / 1024**2, 1)


def fonts():
    windows = Path(os.environ.get('WINDIR', 'C:/Windows')) / 'Fonts'
    if (windows / 'calibri.ttf').exists():
        regular, bold = windows / 'calibri.ttf', windows / 'calibrib.ttf'
    else:
        dejavu = Path('/usr/share/fonts/truetype/dejavu')
        regular, bold = dejavu / 'DejaVuSans.ttf', dejavu / 'DejaVuSans-Bold.ttf'
    pdfmetrics.registerFont(TTFont('Body', str(regular)))
    pdfmetrics.registerFont(TTFont('Bold', str(bold)))
    pdfmetrics.registerFontFamily('Body', normal='Body', bold='Bold', italic='Body', boldItalic='Bold')


def style(font='Body', size=11, leading=15, color=TEXT, after=8, **options):
    return ParagraphStyle('lab', fontName=font, fontSize=size, leading=leading, textColor=color,
                          spaceAfter=after, **options)


def para(text):
    return Paragraph(text, style())


def small(text):
    return Paragraph(text, style(size=9.5, leading=12.5, color=MUTED))


def sub(text):
    return Paragraph(text, style('Bold', 13.5, 17, NAVY, 6, spaceBefore=9))


def section(title, deck):
    return [
        Paragraph(title, style('Bold', 28, 33, NAVY, 8)),
        Paragraph(deck, style(size=12, leading=16, color=MUTED, after=17)),
    ]


def grid(headers, rows, widths, *, font_size=9.5):
    h_style = style('Bold', font_size, font_size + 2.6, colors.white, 0)
    c_style = style(size=font_size, leading=font_size + 2.6, after=0)
    data = [[Paragraph(str(text), h_style) for text in headers]]
    data.extend([Paragraph(str(text), c_style) for text in row] for row in rows)
    result = Table(data, colWidths=widths, hAlign='LEFT', repeatRows=1)
    result.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), NAVY),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, PALE]),
        ('LINEBELOW', (0, -1), (-1, -1), 0.5, LINE),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 7),
        ('RIGHTPADDING', (0, 0), (-1, -1), 7),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    return result


def panel(values):
    stats = Table([
        [Paragraph(value, style('Bold', 23, 26, TEAL, 0, alignment=TA_CENTER)) for value, _ in values],
        [Paragraph(label, style(size=9.5, leading=12, color=MUTED, after=0, alignment=TA_CENTER))
         for _, label in values],
    ], colWidths=[WIDTH / len(values)] * len(values))
    stats.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), PALE),
        ('TOPPADDING', (0, 0), (-1, 0), 13),
        ('BOTTOMPADDING', (0, -1), (-1, -1), 13),
    ]))
    return stats


def page_art(canvas, document):
    page_width, page_height = A4
    canvas.setFillColor(TEAL)
    canvas.rect(0, page_height - 5, page_width, 5, stroke=0, fill=1)
    canvas.setFont('Bold', 9)
    canvas.setFillColor(MUTED)
    canvas.drawString(52, page_height - 34, 'LABORATORIUM 3  /  POSTGRESQL I APACHE SOLR')
    canvas.setStrokeColor(LINE)
    canvas.line(52, 44, page_width - 52, 44)
    canvas.setFont('Body', 9)
    canvas.drawString(52, 28, 'Wyszukiwanie pełnotekstowe · poziom 5.0')
    canvas.drawRightString(page_width - 52, 28, str(document.page))


def scale_chart(counts):
    drawing = Drawing(WIDTH, 203)
    draw_title = ('Q1 · słowo', 'Q2 · fraza', 'Q3 · logika')
    color_for = {'like': ORANGE, 'fts': BLUE, 'solr': TEAL}
    largest = max(counts[str(n)][q][method]['median_ms'] for n in SIZES for q in KEYS for method in METHODS)
    upper = max(100, 10 ** math.ceil(math.log10(largest)))
    ticks = [value for value in (0, 1, 10, 100, 1000, 10_000) if value <= upper]
    bottom, top = 40, 161

    def y(value):
        return bottom + (top - bottom) * math.log10(1 + value) / math.log10(1 + upper)

    for index, q in enumerate(KEYS):
        left = 33 + index * 155
        xs = [left + dx for dx in (6, 62, 118)]
        drawing.add(String(left + 62, 177, draw_title[index], fontName='Bold', fontSize=11,
                           fillColor=NAVY, textAnchor='middle'))
        for tick in ticks:
            zp = y(tick)
            drawing.add(Line(left, zp, left + 128, zp, strokeColor=LINE, strokeWidth=0.6))
            if index == 0:
                drawing.add(String(left - 5, zp - 3, str(tick), fontName='Body', fontSize=8,
                                   fillColor=MUTED, textAnchor='end'))
        for x, caption in zip(xs, ('50 tys.', '250 tys.', '500 tys.')):
            drawing.add(String(x, 25, caption, fontName='Body', fontSize=8, fillColor=MUTED, textAnchor='middle'))
        for method in METHODS:
            points = [(x, y(counts[str(n)][q][method]['median_ms'])) for x, n in zip(xs, SIZES)]
            drawing.add(PolyLine([v for point in points for v in point], strokeWidth=1.7, strokeColor=color_for[method]))
            for x, position in points:
                drawing.add(Circle(x, position, 2.7, fillColor=color_for[method], strokeColor=colors.white, strokeWidth=0.5))
    drawing.add(String(3, 180, 'ms', fontName='Body', fontSize=9, fillColor=MUTED))
    for x, method, name in zip((65, 180, 340), METHODS, ('LIKE', 'PostgreSQL FTS', 'Solr QTime')):
        drawing.add(Rect(x, 3, 12, 3, fillColor=color_for[method], strokeColor=None))
        drawing.add(String(x + 18, 1, name, fontName='Body', fontSize=9, fillColor=TEXT))
    return drawing


def scan_nodes(plan):
    names = {plan['Node Type']}
    for child in plan.get('Plans', []):
        names.update(scan_nodes(child))
    return names


def build():
    fonts()
    dataset, environment, counts = (read(name) for name in ('dataset', 'environment', 'counts'))
    ranking, facet, fuzzy, pagination, sync = (read(name) for name in ('rankings', 'facets', 'fuzzy', 'pagination', 'sync'))
    full = counts[str(SIZES[-1])]
    hardware, pg, solr = (environment[name] for name in ('hardware', 'postgres', 'solr'))
    example = dataset['example']
    q1, q3 = full['Q1'], full['Q3']
    doc = []

    doc += section('Wyszukiwanie pełnotekstowe', 'Porównanie LIKE, PostgreSQL FTS i Apache Solr · eksperyment na 500 000 rekordów')
    doc += [panel([(number(dataset['records']), 'rekordów w korpusie'),
                   (ms(dataset['body_chars_mean'], 1), 'znaków średnio w opisie'),
                   (f'{mib(dataset["bytes"])} MiB', 'rozmiar pliku UTF-8')]), Spacer(1, 16),
            para(f'Badanie wykonano {environment["date"][:10]}. Porównano wyszukiwanie słowa z odmianami, '
                 'sąsiednią frazę i warunek logiczny z negacją. Do pomiaru skalowania zbudowano osobne indeksy '
                 'dla 50 000, 250 000 i 500 000 rekordów.'),
            sub('Korpus'),
            para(f'Generator <b>generate.py</b> tworzy angielskie, fikcyjne notatki z inspekcji terenowych. '
                 f'Składa je z wariantów zdań, obserwacji i pomiarów, z ziarnem <b>{dataset["seed"]}</b>. '
                 f'Opisy mają {dataset["body_chars_min"]}-{dataset["body_chars_max"]} znaków. '
                 f'Liczba powtórzonych treści według skrótu BLAKE2b wyniosła {dataset["duplicate_bodies"]}. '
                 f'Źródło własne, licencja <b>{dataset["license"]}</b>.'),
            para('Jedna notatka ma identyfikator, tytuł, opis, kategorię stanowiska, fikcyjny region i rok. '
                 'Kategoria przyjmuje sześć wartości, region pięć, a lata obejmują okres 1995-2024. '
                 'Identyfikatory są unikalne i odpowiadają kolejności w pliku. Rozkłady i SHA-256 zapisano w dataset.json.'),
            sub('Przykładowy rekord'),
            grid(['ID', 'Tytuł', 'Kategoria', 'Region', 'Rok'],
                 [[example['id'], escape(example['title']), example['category'], example['region'], example['year']]],
                 [44, 235, 74, 74, 64]), Spacer(1, 10),
            Paragraph(escape(example['body']), style(size=10.5, leading=14, color=TEXT, after=8)),
            small('Tekst generatora celowo zawiera różne odmiany i bliskie warianty fraz, aby sprawdzić zachowanie analizatorów. '
                  'Powtarzające się konstrukcje zdań ograniczają reprezentatywność dla korpusów redagowanych przez ludzi.')]

    doc += [PageBreak(), *section('Konfiguracja i pomiar', 'Wspólne dane wejściowe, wspólny filtr lat i niezależne indeksy dla każdego rozmiaru.'),
            sub('PostgreSQL'),
            para('Tabele field_notes_N zawierają id integer PRIMARY KEY, title i body text, category i region text oraz year smallint. '
                 'Kolumna search_vector to generowany, przechowywany tsvector. Angielska konfiguracja sprowadza wyrazy do leksemów. '
                 'Tytuł ma wagę A, a opis D. Leksem rozdzielający uniemożliwia przejście badanej dwuwyrazowej frazy przez granicę pól. '
                 'GIN indeksuje search_vector. Filtrowanie rocznika odbywa się tym samym warunkiem BETWEEN w każdym zapytaniu.'),
            sub('SolrCloud'),
            grid(['Pole', 'indexed / stored / docValues / multiValued', 'Uzasadnienie'], [
                ('id', 'tak / tak / tak / nie', 'uniqueKey, odczyt i stabilna kolejność.'),
                ('title, body', 'tak / tak / nie / nie', 'Analiza i odczyt. body zapisuje offsety podświetlenia.'),
                ('category, region', 'tak / tak / tak / nie', 'Dokładny filtr, zwrot pola i facety.'),
                ('year', 'tak / tak / tak / nie', 'Filtr punktowy, sortowanie i przedziały.'),
                ('_version_', 'nie / nie / tak / nie', 'Wewnętrzne wersjonowanie aktualizacji.'),
            ], [112, 196, 183]),
            Spacer(1, 8),
            para('Analiza tytułu i opisu działa tak samo przy indeksowaniu i przy zapytaniu. Łańcuch to StandardTokenizer, '
                 'zamiana na małe litery, własna lista stop-słów i angielski Snowball. '
                 'eDisMax używa qf=title^3 body, a BM25 jest domyślną funkcją podobieństwa. '
                 'Schemat jest niezmienny. update.autoCreateFields=false zweryfikowano próbą odrzucenia nieznanego pola.'),
            sub('Warunki eksperymentu'),
            para(f'{escape(hardware["cpu"])} ({hardware.get("cores", "?")} rdzenie, {hardware.get("threads", "?")} wątków), '
                 f'{hardware.get("ram_bytes", 0) // 1024**3} GiB RAM, dysk {escape(hardware.get("media", ""))} '
                 f'{escape(hardware.get("disk", ""))} ({escape(hardware.get("drive", ""))}). '
                 f'{escape(hardware["system"])}. PostgreSQL {pg["version"]}, shared_buffers {pg["shared_buffers"]}, '
                 f'maintenance_work_mem {pg["maintenance_work_mem"]}. Solr {solr["version"]}, Lucene {solr["lucene"]}, '
                 f'Java {solr["java"]}, SOLR_HEAP=2g, po jednym shardzie i replice.'),
            small('Serie liczenia trafień i facetów obejmują jedno rozgrzanie oraz pięć prób. Dla PostgreSQL zapisano '
                  'Execution Time z EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, FORMAT JSON). Dla Solra zapisano QTime '
                  'w całych ms i czas HTTP wraz z odczytem oraz dekodowaniem JSON. Po serii EXPLAIN pobrano osobnym SELECT-em '
                  'wartości zwracane przez SQL. Plany i pełne żądania są w results/.')]

    doc += [PageBreak(), *section('Trafienia i czasy', 'Wszystkie zapytania dotyczą lat 2000-2024 i szukają w tytule oraz opisie.')]
    for q, query, explanation in zip(KEYS, QUERIES, (
            'to_tsquery/angielski stemming obejmuje m.in. restored, restoring i restoration.',
            'phraseto_tsquery i cudzysłów w Solrze wymagają sąsiedztwa i właściwej kolejności.',
            'Warunek wymaga habitat i co najmniej jednego z wetland lub marsh oraz wyklucza invasive.')):
        doc.append(para(f'<b>{q}</b> · {escape(query)}<br/>{explanation}'))
    doc += [sub('500 000 dokumentów · wyniki i drugie uruchomienie'),
            grid(['Zap.', 'LIKE<br/>liczba', 'SQL FTS<br/>liczba', 'Solr<br/>numFound',
                  'LIKE<br/>ms', 'SQL FTS<br/>ms', 'Solr<br/>QTime', 'Solr<br/>HTTP ms'],
                 [[q, *[number(full[q][m]['count']) for m in METHODS],
                   *[ms(full[q][m]['second_ms']) for m in METHODS], ms(full[q]['solr']['client_ms'][1])]
                  for q in KEYS], [40, 62, 66, 65, 63, 64, 63, 68]),
            Spacer(1, 9),
            small('LIKE sprawdza podciągi w tekście zamienionym na małe litery. Dla Q2 sprawdza dosłowny ciąg '
                  'solar panel, a dla Q3 łączy cztery wzorce tą samą logiką. Wzorce mogą dopasować fragment wyrazu.'),
            small('Trzy adresy żądań z top-10 otwarto również w przeglądarce. Odpowiedzi i czasy tego sprawdzenia '
                  'są udokumentowane w results/browser_check.json.'),
            sub('Analiza liczności'),
            para(f'W Q1 LIKE odnalazł {number(q1["like"]["count"])} dokumentów, a PostgreSQL FTS '
                 f'{number(q1["fts"]["count"])}. Wzorzec %restore% obejmuje np. restored, lecz nie zawiera się w restoring '
                 'ani restoration. Oba pełnotekstowe analizatory sprowadzają te formy do wspólnego rdzenia.'),
            para('Zbieżność wyników pełnotekstowych dla testowanych fraz i operatorów zależy od użytych słów i korpusu. '
                 'Testowane terminy nie są stop-słowami. Na odmienne teksty wpływają reguły tokenizacji, '
                 'lista stop-słów oraz pozycje po ich odfiltrowaniu.'),
            sub('Import i indeksowanie · pełny zbiór')]
    load_pg = read('load_pg_500000')
    load_solr = read('load_solr_500000')
    doc += [grid(['System', 'Etap', 'Czas [s]'], [
        ('PostgreSQL', 'COPY, obliczenie tsvector, utrzymanie PK', seconds(load_pg['copy_ms'])),
        ('PostgreSQL', 'CREATE INDEX GIN', seconds(load_pg['gin_ms'])),
        ('PostgreSQL', 'ANALYZE', seconds(load_pg['analyze_ms'])),
        ('Solr', f'Wysłanie {len(load_solr["batches"])} paczek, analiza i zapis online', seconds(load_solr['upload_ms'])),
        ('Solr', 'Jeden końcowy hard commit i otwarcie searchera', seconds(load_solr['commit_ms'])),
    ], [101, 304, 86]),
            Spacer(1, 8),
            small(f'W PostgreSQL pełny rozmiar relacji z indeksami to {mib(load_pg["total_bytes"])} MiB, '
                  f'w tym {mib(load_pg["gin_bytes"])} MiB dla GIN. W Solrze analiza odbywa się podczas wysyłania, '
                  'więc sama faza commit nie stanowi odpowiednika CREATE INDEX.')]

    doc += [PageBreak(), *section('Ranking i podświetlanie', 'Pierwsze dziesięć dokumentów w każdym silniku, w kolejności trafności.')]
    rows = []
    for i in range(10):
        row = [i + 1]
        for q in KEYS:
            pg_doc = ranking[q]['sql']['rows'][i]
            solr_doc = ranking[q]['solr']['result']['response']['docs'][i]
            row.extend((f'{pg_doc["id"]:06}<br/>{ms(pg_doc["score"], 3)}',
                        f'{solr_doc["id"]}<br/>{ms(solr_doc["score"], 3)}'))
        rows.append(row)
    doc += [grid(['Lp.', *[f'{q}<br/>{engine}' for q in KEYS for engine in ('SQL', 'Solr')]], rows,
                 [34, 76, 76, 76, 76, 76, 77], font_size=9),
            Spacer(1, 9),
            para('Komórki pokazują ID i wynik punktowy. Część wspólna top-10 wynosi '
                 + ', '.join(f'<b>{q} {len(ranking[q]["overlap"])}/10</b>' for q in KEYS) + '.'),
            para('ts_rank_cd ocenia gęstość i pozycje trafień z wagami A/D. BM25 uwzględnia częstość terminu '
                 'w dokumentach, długość pola oraz eDisMax z tytułem ważonym trzykrotnie. '
                 'Remisy rozstrzygano według ID. Wyniki punktowe mają odrębne skale.'),
            sub('Fragmenty opisu z Unified Highlighter')]
    for q in KEYS:
        data = ranking[q]['solr']['result']
        doc_id, highlight = next((key, value['body'][0]) for key, value in data['highlighting'].items() if value.get('body'))
        formatted = escape(highlight).replace('&lt;em&gt;', '<font color="#00796F"><b>').replace('&lt;/em&gt;', '</b></font>')
        doc.append(small(f'<b>{q} · ID {doc_id}</b> &nbsp; {formatted}'))

    doc += [PageBreak(), *section('Skalowanie', 'Mediany z pięciu prób dla trzech niezależnie zbudowanych rozmiarów indeksu.'),
            scale_chart(counts), Spacer(1, 8),
            small('Oś pionowa ma skalę log10(1 + ms). Wspólna skala obejmuje wszystkie panele, także ewentualne 0 ms QTime. '
                  'Oś pozioma pokazuje trzy zmierzone rozmiary.'),
            grid(['Rekordy', 'Zap.', 'LIKE ms', 'SQL FTS ms', 'Solr QTime ms', 'Solr HTTP ms'],
                 [[number(n), q, *[ms(counts[str(n)][q][m]['median_ms']) for m in METHODS],
                   ms(counts[str(n)][q]['solr']['median_client_ms'])] for n in SIZES for q in KEYS],
                 [81, 46, 84, 92, 92, 96]),
            sub('Próg 100 ms po stronie serwera')]
    crossings = {
        m: [next((n for n in SIZES if counts[str(n)][q][m]['median_ms'] > 100), None) for q in KEYS]
        for m in METHODS
    }
    names = ('LIKE', 'SQL FTS', 'Solr')
    doc += [para('Pierwszy zmierzony rozmiar ponad przyjętym progiem. '
                 + ' '.join(f'<b>{name}</b> ' + ', '.join(
                     f'{q} {number(n) if n else "w limicie"}' for q, n in zip(KEYS, crossings[m])) + '.'
                            for name, m in zip(names, METHODS))),
            small('Pomiar dotyczy rozgrzanego odczytu na jednym komputerze i żądań liczących trafienia. '
                  'Top-10, podświetlenie i facety stanowią osobne żądania. Czas odpytywania nie obejmuje importu.')]

    buckets = facet['buckets']
    bucket_rows = []
    for name in ('category', 'region', 'year'):
        for bucket, observed in sorted(buckets[name].items()):
            sql_observed = next(row['count'] for row in facet['sql'][name]['rows'] if str(row['bucket']) == bucket)
            label = f'{bucket}-{int(bucket) + 4}' if name == 'year' else bucket
            bucket_rows.append([name, escape(label), number(sql_observed), number(observed)])
    doc += [PageBreak(), *section('Facety a GROUP BY', f'Jedno żądanie Solra dla Q3 agreguje {number(q3["solr"]["count"])} trafień na trzy sposoby.'),
            grid(['Pole', 'Wartość lub lata', 'PostgreSQL', 'Solr'], bucket_rows, [91, 162, 119, 119]),
            Spacer(1, 9),
            sub('Czasy serwera [ms]'),
            grid(['Operacja', 'Mediana', 'Drugie uruch.'], [
                *[(f'GROUP BY · {name}', ms(facet['sql'][name]['median_ms']), ms(facet['sql'][name]['second_ms']))
                  for name in ('category', 'region', 'year')],
                ('Suma 3 GROUP BY w obrębie próby', ms(facet['sql_sum_median_ms']), ms(facet['sql_sum_ms'][1])),
                ('Jedno SQL · GROUPING SETS', ms(facet['grouping_sets']['median_ms']), ms(facet['grouping_sets']['second_ms'])),
                ('Jedno HTTP · 2 × facet.field + facet.range', ms(facet['solr']['median_ms']), ms(facet['solr']['second_ms'])),
            ], [296, 94, 101]),
            Spacer(1, 8),
            small(f'Mediana HTTP dla facetów wyniosła {ms(facet["solr"]["median_client_ms"])} ms. '
                  'Facet roczny ma przedziały lewostronnie domknięte, od 2000 do 2025 z krokiem 5. '
                  'SQL grupuje 2000 + 5 × część całkowita z (year - 2000) / 5. Wszystkie 16 kubełków porównano automatycznie.')]

    doc += [PageBreak(), *section('Trzy rozszerzenia', 'Literówka w zapytaniu, dostęp do późnych stron i zgodność po zmianach danych.'),
            sub('1. Tolerancja literówki'),
            grid(['Zapytanie', 'Metoda', 'Trafienia', 'Mediana [ms]'], [
                (query, method, number(fuzzy[key]['count']), ms(fuzzy[key]['median_ms']))
                for key, query, method in (
                    ('correct', 'solar', 'Solr · dokładne'), ('typo', 'soalr', 'Solr · dokładne'),
                    ('fuzzy', 'soalr~1', 'Solr · fuzzy'), ('sql_correct', '%solar%', 'SQL · LIKE'),
                    ('sql_typo', '%soalr%', 'SQL · LIKE'))], [117, 151, 108, 115]),
            Spacer(1, 7),
            para('W zapytaniu soalr zamieniono miejscami litery l i a. Fuzzy z odległością jeden '
                 'dopuszcza taką transpozycję. Zwykły LIKE i dokładne wyszukiwanie leksemu wymagają formy pasującej do zapytania.'),
            sub('2. Głębokie stronicowanie'),
            grid(['Offset', 'start QTime', 'cursor QTime', 'start HTTP', 'cursor HTTP', 'Dojście kursorem [s]'],
                 [[number(item['offset']), ms(item['start']['qtime_ms']), ms(item['cursor']['qtime_ms']),
                   ms(item['start']['client_ms']), ms(item['cursor']['client_ms']), seconds(item['earlier_client_ms'])]
                  for item in pagination.values()], [66, 78, 83, 71, 76, 117]),
            Spacer(1, 7),
            para('Rozmiar strony to 1000, kolejność year asc, id asc. Obie metody dały identyczne listy ID na każdej '
                 'badanej stronie. Kolumny czasu pojedynczej strony podają mediany w ms. Czas dojścia sumuje poprzednie '
                 'żądania HTTP potrzebne do wyznaczenia kursora. Skok z samym numerem strony obsługuje start.'),
            sub('3. Synchronizacja zmian'),
            grid(['Stan', 'Rekordy w każdym silniku', 'Trafienia calibration', 'Obecne ID z próby'], [
                ['Przed zmianą', number(sync['before']['postgres']['total']), '0', '13, 37, 81'],
                ['Po synchronizacji', number(sync['after']['postgres']['total']), '13, 37', '13, 37'],
                ['Po przywróceniu', number(sync['restore']['snapshot']['postgres']['total']), '0', '13, 37, 81'],
            ], [109, 129, 127, 126]),
            Spacer(1, 7),
            small('Skrypt aktualizuje dwa wiersze i usuwa jeden w PostgreSQL, ponownie czyta zmienione wiersze i wysyła '
                  'je do /update razem z komendą usunięcia w osobnym żądaniu. Po commit porównuje dane i liczności. '
                  'Kopia trzech rekordów umożliwia przywrócenie obu indeksów po eksperymencie.')]

    like_plans = scan_nodes(plan_for_q1('like'))
    fts_plan = plan_for_q1('fts')
    fts_plans = scan_nodes(fts_plan)
    doc += [PageBreak(), *section('Wnioski', 'Wybór narzędzia zależy od rodzaju zapytań i funkcji potrzebnych użytkownikowi.'),
            sub('LIKE i indeks w PostgreSQL'),
            para(f'Przy 500 tys. rekordów Q1 kosztowało medianowo {ms(q1["like"]["median_ms"])} ms w LIKE '
                 f'i {ms(q1["fts"]["median_ms"])} ms w PostgreSQL FTS. Plan LIKE zawierał '
                 f'{escape(", ".join(sorted(like_plans)))}. Plan FTS zawierał {escape(", ".join(sorted(fts_plans)))}. '
                 'Przeszukiwanie podciągów z początkowym % bez indeksu trójgramowego wymaga przejrzenia tekstu. '
                 'PostgreSQL FTS daje dodatkowo odmiany, sąsiedztwo frazy i ranking w tej samej bazie co dane.'),
            small(f'W PostgreSQL FTS przy 500 tys. rekordów plan Q1 raportował {number(fts_plan["Shared Read Blocks"])} '
                  'bloków odczytanych poza współdzielonymi buforami PostgreSQL podczas drugiej próby. Przy szerokim dopasowaniu '
                  'GIN wskazuje wiersze, po czym skan tabeli kosztuje więcej. Licznik buforów nie rozróżnia odczytu z cache '
                  'systemu operacyjnego i fizycznego nośnika.'),
            sub('Kiedy rozważyć Solra'),
            para(f'Q1 w Solrze miało medianę QTime {ms(q1["solr"]["median_ms"])} ms. Trzy facety Q3 miały '
                 f'{ms(facet["solr"]["median_ms"])} ms QTime i {ms(facet["solr"]["median_client_ms"])} ms po stronie klienta. '
                 f'Jedno zapytanie SQL z GROUPING SETS miało {ms(facet["grouping_sets"]["median_ms"])} ms. '
                 'W aplikacji wyszukiwawczej Solr może zwrócić ranking wraz z krótkimi fragmentami i filtrami nawigacji. '
                 'Dochodzi koszt utrzymania i synchronizacji osobnego indeksu.'),
            sub('Granice porównania'),
            para('Wyniki opisują jeden korpus, jedną maszynę i rozgrzane wykonania. Pozycje w top-10 nie stanowią oceny '
                 'trafności przez człowieka. QTime jest kwantowane do ms, podczas gdy Execution Time z EXPLAIN '
                 'ma większą rozdzielczość. Użycie cache filtrów, selektywność zapytania i aktywność systemu '
                 'mogą zmienić proporcje czasów.'),
            sub('Dokumentacja'),
            *[small(f'<link href="{url}" color="#2B59A2"><u>{label}</u></link>') for label, url in (
                ('PostgreSQL 17 · analiza, zapytania i ranking', 'https://www.postgresql.org/docs/17/textsearch-controls.html'),
                ('PostgreSQL 17 · parametry EXPLAIN', 'https://www.postgresql.org/docs/17/sql-explain.html'),
                ('Solr 10.1 · eDisMax', 'https://solr.apache.org/guide/solr/10_1/query-guide/edismax-query-parser.html'),
                ('Solr 10.1 · dokumentacja facetów', 'https://solr.apache.org/guide/solr/10_1/query-guide/faceting.html'),
                ('Solr 10.1 · stronicowanie i cursorMark', 'https://solr.apache.org/guide/solr/10_1/query-guide/pagination-of-results.html'),
                ('Creative Commons · CC0 1.0 Universal', 'https://creativecommons.org/publicdomain/zero/1.0/'))]]

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    pdf = SimpleDocTemplate(str(OUTPUT), pagesize=A4, leftMargin=46, rightMargin=46, topMargin=63, bottomMargin=57,
                            title='Laboratorium 3 - Wyszukiwanie pełnotekstowe', subject='PostgreSQL kontra Apache Solr')
    pdf.build(doc, onFirstPage=page_art, onLaterPages=page_art)
    write_markdown(full, ranking, facet, fuzzy, pagination, sync)


def plan_for_q1(method):
    with (ROOT / 'results' / 'measurements_counts.jsonl').open(encoding='utf-8') as stream:
        for line in stream:
            sample = json.loads(line)
            if sample['label'] == f'500000.Q1.{method}' and sample['run'] == 2:
                return sample['plan']['Plan']
    raise ValueError(f'Missing Q1 plan for {method}')


def write_markdown(full, ranking, facet, fuzzy, pagination, sync):
    columns = ['Zapytanie', 'LIKE liczba', 'SQL liczba', 'Solr numFound', 'LIKE ms', 'SQL ms', 'QTime ms', 'HTTP ms']
    lines = ['Drugie uruchomienie przy 500 000 rekordów. SQL to Execution Time, a HTTP to pełny czas klienta Solra.', '',
             '| ' + ' | '.join(columns) + ' |', '| --- |' + ' ---: |' * (len(columns) - 1)]
    for q, query in zip(KEYS, QUERIES):
        row = [f'{q} `{query}`', *[number(full[q][m]['count']) for m in METHODS],
               *[ms(full[q][m]['second_ms']) for m in METHODS], ms(full[q]['solr']['client_ms'][1])]
        lines.append('| ' + ' | '.join(row) + ' |')
    lines += ['', 'W tabeli LIKE porównuje fragmenty znaków, a analizatory pełnotekstowe redukują angielskie odmiany do rdzeni. '
              'W Q1 do różnicy przyczyniają się formy `restoring` i `restoration`, których podciąg `restore` nie obejmuje. '
              'Tokenizacja i stoplisty mogą zmienić wyniki dla tekstu o innej strukturze.']
    path = ROOT / 'README.md'
    text = path.read_text(encoding='utf-8')
    text = re.sub(r'<!-- RESULTS BEGIN -->.*?<!-- RESULTS END -->',
                  '<!-- RESULTS BEGIN -->\n' + '\n'.join(lines) + '\n<!-- RESULTS END -->', text, flags=re.DOTALL)
    path.write_text(text, encoding='utf-8')

    q1 = full['Q1']
    deep = pagination['250000']
    oral = f"""# Przygotowanie do odpowiedzi ustnej

## Przebieg krótkiej demonstracji

1. Pokaż `generate.py` i `results/dataset.json`. Wyjaśnij, że pierwsze 50 tys., 250 tys. i 500 tys. wierszy zostały zaindeksowane w niezależnych tabelach i kolekcjach. Każda para dostaje te same rekordy.
2. W `sql/queries.sql` pokaż Q1, Q2 i Q3. W przeglądarce otwórz te same zapytania z `zapytania.html` i wskaż `numFound`, `score` oraz `highlighting`.
3. Pokaż wykres skalowania i porównanie 16 kubełków z PDF. Przejdź do literówki, stronicowania i synchronizacji.

## Pytania, które warto przećwiczyć

- **Czemu Q1 daje różne liczności?** LIKE znalazł {number(q1['like']['count'])}, a SQL FTS {number(q1['fts']['count'])} i Solr {number(q1['solr']['count'])}. `restoring` i `restoration` mają ten sam rdzeń co `restore`, lecz nie zawierają go jako podciągu.
- **Skąd różnice w rankingu?** PostgreSQL `ts_rank_cd` bierze pod uwagę pozycje i wagi A/D. eDisMax z BM25 uwzględnia statystykę terminu i długość pola oraz używa `qf=title^3 body`. Wspólne dokumenty w top-10: {', '.join(q + ' ' + str(len(ranking[q]['overlap'])) + '/10' for q in KEYS)}.
- **Jak czytać czasy?** Drugie uruchomienie to pierwsza próba po rozgrzaniu. Mediana liczy pięć takich prób. SQL ma `Execution Time`. Solr ma `QTime` i dodatkowo pełny czas HTTP. Przy 500 tys. mediany Q1 to LIKE {ms(q1['like']['median_ms'])} ms, SQL FTS {ms(q1['fts']['median_ms'])} ms, Solr QTime {ms(q1['solr']['median_ms'])} ms.
- **Czy facety zgadzają się z SQL?** Tak, wszystkie 16 kubełków. Jedno żądanie facetów miało medianę QTime {ms(facet['solr']['median_ms'])} ms, a `GROUPING SETS` {ms(facet['grouping_sets']['median_ms'])} ms po stronie PostgreSQL.
- **Co pokazała literówka?** Dokładne `soalr` i LIKE `%soalr%` zwróciły 0. `soalr~1` dopuściło transpozycję i zwróciło {number(fuzzy['fuzzy']['count'])} dokumentów.
- **Czy kursor od razu skacze do dalekiej strony?** Na offsecie 250 tys. pojedyncza strona miała medianę QTime {ms(deep['cursor']['qtime_ms'])} ms z kursorem i {ms(deep['start']['qtime_ms'])} ms z `start`. Uzyskanie tej pozycji kursora wymagało {deep['earlier_requests']} poprzednich żądań.
- **Jak zweryfikowano synchronizację?** Po dwóch aktualizacjach i jednym usunięciu obie strony miały {number(sync['after']['postgres']['total'])} rekordów, a `calibration` dało te same ID 13 i 37. Skrypt odtworzył pierwotny korpus.
"""
    (ROOT / 'OBRONA.md').write_text(oral, encoding='utf-8')


if __name__ == '__main__':
    build()
