# Laboratorium 3 · wyszukiwanie pełnotekstowe

Zakres na 5.0. PostgreSQL 17.12 i Apache Solr 10.1.0 porównano na 500 000 angielskich notatek terenowych. Osobne tabele i kolekcje zawierają 50 000, 250 000 i 500 000 pierwszych rekordów ze wspólnego CSV.

Rozszerzenia obejmują fuzzy dla literówki, porównanie głębokiego stronicowania i synchronizację zmian z PostgreSQL do Solra. Sprawozdanie jest w [Sprawozdanie_LAB3.pdf](../Sprawozdanie_LAB3.pdf). [OBRONA.md](OBRONA.md) zawiera materiał do odpowiedzi ustnej.

## Uruchomienie na Windows

Potrzebne są Python 3.12 lub nowszy, Java 21 lub nowsza, PowerShell, tar i curl oraz kilka GB wolnego miejsca. Użyj zwykłej sesji użytkownika. Jeśli Java nie jest wykrywana, ustaw `$env:LAB3_JAVA_HOME` na katalog JDK w tej sesji.

```powershell
.\local.ps1 -Action Install
.\local.ps1 -Action Start
python -m venv .runtime/venv
$labPython = '.\.runtime\venv\Scripts\python.exe'
& $labPython -m pip install --no-cache-dir -r requirements.txt
& $labPython generate.py
& $labPython -u load.py pg 50000 250000 500000
& $labPython -u load.py solr 50000 250000 500000
& $labPython environment.py
& $labPython -u benchmark.py all
& $labPython -u pagination.py
& $labPython -u sync_demo.py
& $labPython report.py
.\local.ps1 -Action Stop
```

Serwery uruchamiają się z archiwów binarnych w `.runtime/`. PostgreSQL słucha na `127.0.0.1:15436`, a Solr na `127.0.0.1:18983`. Jednowęzłowy SolrCloud ma osadzony ZooKeeper i po jednym shardzie oraz jednej replice na kolekcję. Ustawienia dotyczą lokalnych danych laboratoryjnych. W PostgreSQL uwierzytelnianie `trust` obejmuje połączenia lokalne, a Solr jest dostępny wyłącznie na adresie loopback.

Polecenia `load.py` na czystym środowisku uruchamia się raz. Aby celowo przebudować konkretną tabelę lub kolekcję laboratoryjną, podaj jej rozmiar i `--replace`. Po zatrzymaniu serwerów poleceniem `local.ps1 -Action Stop` indeksy są nadal dostępne po ponownym uruchomieniu. Generator odtwarza cały CSV z ziarna 732391. Dane są na licencji [CC0 1.0](DATA-LICENSE.md).

## Zapytania i dowody

- SQL zawiera [DDL](sql/schema.sql), [indeks GIN](sql/index.sql) i [przykładowe zapytania](sql/queries.sql). `queries.py` zawiera definicje wspólne dla klienta.
- Konfiguracja Solra znajduje się w [solr/](solr/). Loader wysyła plik tej konfiguracji przez Configsets API, następnie wysyła JSON do `/update` po 2000 dokumentów i zatwierdza pojedynczym `commit` po serii.
- Otwórz [zapytania.html](zapytania.html) przy uruchomionym Solrze. Linki Q1–Q3 pokazują pełne odpowiedzi z top-10 i podświetlaniem. Zapis wykonanej próby jest w [results/browser_check.json](results/browser_check.json). Można też odtworzyć parametry w widoku Query w [Solr Admin UI](http://127.0.0.1:18983/solr/).
- `results/counts.json` zawiera liczności i próbki dla trzech rozmiarów. `results/measurements_*.jsonl` zawierają dokładny SQL lub URL, liczność i czas każdej próby. Dla PostgreSQL zachowano także plany z buforami.
- `results/rankings.json`, `facets.json`, `fuzzy.json`, `pagination.json` i `sync.json` zawierają wyniki funkcjonalne. `sync_demo.py` przywraca trzy testowe dokumenty w obu silnikach. Gdy przerwie go awaria, `sync_demo.py --restore` odtwarza stan z lokalnej kopii.

## Wyniki

<!-- RESULTS BEGIN -->
Drugie uruchomienie przy 500 000 rekordów. SQL to Execution Time, a HTTP to pełny czas klienta Solra.

| Zapytanie | LIKE liczba | SQL liczba | Solr numFound | LIKE ms | SQL ms | QTime ms | HTTP ms |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Q1 `restore` | 37 674 | 62 565 | 62 565 | 1043,60 | 601,86 | 9,00 | 11,82 |
| Q2 `"solar panel"` | 27 169 | 27 169 | 27 169 | 943,86 | 622,63 | 18,00 | 21,31 |
| Q3 `habitat AND (wetland OR marsh) AND NOT invasive` | 44 514 | 44 514 | 44 514 | 1679,41 | 543,37 | 19,00 | 21,76 |

W tabeli LIKE porównuje fragmenty znaków, a analizatory pełnotekstowe redukują angielskie odmiany do rdzeni. W Q1 do różnicy przyczyniają się formy `restoring` i `restoration`, których podciąg `restore` nie obejmuje. Tokenizacja i stoplisty mogą zmienić wyniki dla tekstu o innej strukturze.
<!-- RESULTS END -->

## Oddanie

W nazwie `LAB3_Nazwisko_Imie_Nazwisko_Imie.zip` podstaw dane obu osób. ZIP zawiera kod, skrypty SQL, konfigurację Solra, README, sprawozdanie i wyniki. CSV, archiwa dystrybucji i pliki indeksów zostają poza ZIP-em.
