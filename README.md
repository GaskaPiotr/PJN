# Sprawozdanie z Laboratorium nr 1: Parser strony WWW

**Przedmiot:** Przetwarzanie Języka Naturalnego
**Poziom docelowy:** 5.0 (Parser i Web)
**Skład zespołu:** [Gąska Piotr - Rola PARSER], [Ciesielczyk Michał - Rola AUTOR]

---

## 1. Użyte technologie i uzasadnienie wyboru

Do realizacji projektu po stronie parsera oraz analizy danych wybrano środowisko **Python 3.11+**:
* **Selenium WebDriver (`selenium`):** Narzędzie do automatyzacji przeglądarki Chrome. Umożliwiło realizację wymogów poziomu 5.0, gdzie zawartość katalogu jest wstrzykiwana dynamicznie do drzewa DOM za pomocą asynchronicznego zapytania `fetch()`, a kolejne partie rekordów wymagają interakcji z przyciskiem doładowywania.
* **BeautifulSoup4 z parserem lxml (`bs4`, `lxml`):** Wykorzystany do parsowania kodu HTML wyrenderowanego przez przeglądarkę (`driver.page_source`). Połączenie Selenium (do renderowania DOM) z BeautifulSoup (do ekstrakcji danych w pamięci podręcznej) drastycznie skróciło czas parsowania w stosunku do bezpośrednich zapytań DOM przez WebDrivera.
* **Requests (`requests`):** Biblioteka HTTP użyta do pobrania surowego kodu strony bez uruchamiania silnika JavaScript, co pozwoliło na formalne porównanie surowego HTML z wyrenderowanym drzewem DOM.
* **Pandas & NumPy (`pandas`, `numpy`):** Zastosowane do transformacji danych, czyszczenia typów zmiennych, obsługi braków, deduplikacji, obliczenia statystyk opisowych oraz kontroli jakości zbioru.
* **Matplotlib (`matplotlib`):** Zastosowany do wygenerowania histogramu cen oraz wykresu pudełkowego (box-plot).

---

## 2. Opis zbudowanego serwisu (Rola: AUTOR)

Serwis *Nova Market* został przygotowany z wykorzystaniem generatora skryptowego (`Node.js`) oraz technologii HTML5, CSS3 i Vanilla JavaScript:
* **Struktura katalogu:** Serwis składa się z 5 stron katalogu (`mock.html`, `catalog-page-2.html` – `catalog-page-5.html`) połączonych nawigacją oraz 400 indywidualnych, statycznych podstron produktowych umieszczonych w katalogu `details/`.
* **Mechanizm dynamiczny (Poziom 5.0):** Pliki HTML katalogu nie zawierają produktów w kodzie źródłowym (posiadają puste znaczniki `<tbody>` oraz `#products-container`). Rekordy są pobierane w locie z pliku `data/products.json` za pomocą `fetch()` i wstrzykiwane do drzewa DOM.
* **Doładowywanie porcjami:** Katalog ładuje dane w partiach po 20 rekordów za pomocą przycisku `#load-more`. Skrypt symuluje sztuczne opóźnienie w przedziale 300–2000 ms, blokując przycisk w trakcie żądania i ukrywając go po wyczerpaniu puli dla danej strony.

### Zrealizowane utrudnienia:
1. **Dwie odmienne struktury prezentacji:** Połowa rekordów generowana jest w formie tabeli (`tr.product-row`), a druga połowa w postaci kafelków (`article.product-card`).
2. **Niespójne formaty cen i waluty:** Ceny zapisano ze spacjami niełamliwymi (`&nbsp;`, `\xa0`) w trzech walutach (`zł`, `EUR`, `USD`) z różnymi separatorami dziesiętnymi.
3. **Kontrolowane braki danych (>15%):** Wprowadzono celowe braki w polach `category` (16.50%) oraz `availability` (16.75%).
4. **Zduplikowane rekordy:** Do katalogu wprowadzono 12 kontrolowanych duplikatów produktów rozrzuconych na różnych podstronach.
5. **Losowa kolejność atrybutów w kartach:** Kolejność elementów wewnątrz kafelków produktów jest zmienna, co wymusiło na parserze selekcję opartą o klasy semantyczne, a nie pozycję w drzewie.
6. **Atrybut widoczny po interakcji:** Opis produktu umieszczono wewnątrz rozwijanego elementu `<details><summary>`.

---

## 3. Opis parsera (Rola: PARSER)

Parser zaimplementowano w postaci modularnego programu w języku Python (`cleaners.py`, `scraper.py`, `analysis.py`):
* **Paginacja i nawigacja:** Parser automatycznie iteruje przez wszystkie 5 podstron katalogu.
* **Jawne oczekiwania (`WebDriverWait`):** Obsługę doczytywania partii zrealizowano za pomocą warunku `EC.element_to_be_clickable((By.ID, "load-more"))`, co eliminuje sztywne opóźnienia wątku przy oczekiwaniu na DOM.
* **Opóźnienie między żądaniami:** Przy przechodzeniu do 400 stron szczegółów parser stosuje stałe opóźnienie 0.5 s (`time.sleep(0.5)`), realizując zasady kulturalnego scrapingu.
* **Ponawianie prób (Exponential Backoff):** W przypadku błędu ładowania strony głównej parser ponawia próbę 3-krotnie z wykładniczo rosnącym czasem oczekiwania ($2^{\text{próba}}$ s).

### Wybrane rozszerzenia:
1. **Eksport do dwóch formatów jednocześnie (Poziom 4.0):** Zapis zbioru do plików `products_output.csv` (UTF-8) oraz `products_output.xlsx`.
2. **Logowanie przebiegu z pełnym podsumowaniem (Poziom 4.0):** Moduł `logging` zapisuje do `scraping.log` liczbę odwiedzonych stron, zebranych rekordów, błędów oraz łączny czas pracy.
3. **Tryb Headless z pomiarem czasu w obu trybach (Poziom 5.0):** Program wykonuje zadanie w trybie bezokienkowym (`headless=True`) oraz w widocznym oknie (`headless=False`), mierząc i porównując czasy wykonania.
4. **Automatyczny zrzut ekranu i zapis źródła strony przy błędzie (Poziom 5.0):** Funkcja `save_error_diagnostic` tworzy pliki `.png` oraz zrzut DOM `.html` ze stemplem czasowym w razie wystąpienia wyjątku.

---

## 4. Ocena odporności selektorów

W parserze zastosowano selektory CSS bazujące na klasach semantycznych i identyfikatorach ID:

| Element | Selektor | Ocena odporności | Uzasadnienie |
| :--- | :--- | :--- | :--- |
| Wiersz tabeli | `table#products-table tbody tr.product-row` | **Wysoka** | Opiera się na semantyce tabeli; odporny na zmiany styli i układu strony. |
| Karta produktu | `#products-container article.product-card` | **Wysoka** | Standardowy znacznik HTML5; niezależny od siatki CSS (Grid/Flexbox). |
| Pola w karcie | `.name`, `.price`, `.brand`, `.stock`, `.rating` | **Wysoka** | W pełni odporne na losową kolejność pól zastosowaną przez autora; wyszukiwanie odbywa się po klasie, a nie indeksie elementu. |
| Metadane ID/magazynu | `[data-id]`, `[data-warehouse]` | **Bardzo wysoka** | Atrybuty `data-*` są niezależne od warstwy prezentacyjnej CSS. |
| Cechy w szczegółach | `#spec-ean`, `#spec-weight`, `#spec-shipping-days` | **Wysoka** | Unikalne identyfikatory gwarantują precyzyjną ekstrakcję wartości. |
| Opis produktu | `.description-text`, `details p` | **Wysoka** | Selektory alternatywne pozwalają odczytać treść opisu bez względu na stan zwinięcia elementu `<details>`. |

W parserze świadomie zrezygnowano ze ścieżek bezwzględnych XPath (np. `/html/body/div[1]/...`), które są podatne na najmniejsze zmiany w szablonie strony.

---

## 5. Wyniki kontroli jakości danych

Kontrola jakości została zrealizowana skryptem `analysis.py`:
* **Pozyskane rekordy surowe:** 412.
* **Deduplikacja:** Przed usunięciem: 412 rekordów; po usunięciu: **400 unikalnych rekordów** (usunięto dokładnie 12 zduplikowanych wpisów na podstawie klucza `id` i `name`).
* **Liczba atrybutów:** Zgromadzono 24 atrybuty (wymóg: minimum 22).

### Analiza braków danych:

| Kolumna | Liczba braków | Procent braków (%) | Interpretacja |
| :--- | :--- | :--- | :--- |
| `id`, `name`, `price`, `currency`, `details_url` | 0 | 0.00% | Podstawowe dane katalogowe są w pełni kompletne. |
| `category` | 66 | 16.50% | Zamierzone utrudnienie autora (wymóg $\ge 15\%$). |
| `availability` | 67 | 16.75% | Zamierzone utrudnienie autora (wymóg $\ge 15\%$). |
| `brand` | 23 | 5.75% | Częściowy brak danych o marce. |
| `warranty_months` | 40 | 10.00% | Brak informacji o gwarancji dla części produktów. |
| `color` | 50 | 12.50% | Brak specyfikacji koloru dla części produktów. |
| `delivery` | 0 | 0.00% | Czas dostawy poprawnie sparsowany do liczby dni (`int64`). |
| Pozostałe 16 kolumn | 0 | 0.00% | Pełna kompletność parametrów technicznych. |

### Weryfikacja typów danych:
* Pola liczbowe (`price`, `rating`, `reviews_count`, `warranty_months`, `delivery`) zostały poprawnie skonwertowane do typów `float64` oraz `int64`.
* Waluty zostały odseparowane do kolumny `currency`, a ceny oczyszczone ze spacji niełamliwych.

### Wartości odstające (Outliers):
Zastosowano metodę rozstępu ćwiartkowego (IQR) dla kolumny `price`:
* $Q_1 = 1113.04$ zł, $Q_3 = 3250.91$ zł, $IQR = 2137.87$ zł
* Dolna granica odcięcia: $-2103.89$ zł; Górna granica odcięcia: $6467.85$ zł.
* **Wykryte outliery:** **0**.
* **Wniosek:** Brak wartości odstających potwierdza, że funkcja czyszcząca ceny nie spowodowała błędów rzędu wielkości (np. błędnego przesunięcia przecinka dziesiętnego).

---

## 6. Statystyki opisowe i analiza korelacji

### Tabela statystyk cech liczbowych ($N=400$):

| Cecha | Średnia | Mediana | Moda | Q1 (25%) | Q3 (75%) | Min | Max | Odch. std. |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Cena (`price`)** | 2181.62 | 2185.51 | 53.49 | 1113.04 | 3250.91 | 53.49 | 4321.38 | 1245.51 |
| **Ocena (`rating`)** | 4.20 | 4.20 | 3.50 | 3.80 | 4.60 | 3.40 | 5.00 | 0.49 |
| **Opinie (`reviews_count`)** | 480.38 | 479.50 | 3.00 | 246.50 | 714.75 | 3.00 | 969.00 | 277.85 |
| **Gwarancja (`warranty_months`)** | 24.00 | 24.00 | 12.00 | 12.00 | 24.00 | 12.00 | 36.00 | 9.81 |
| **Dostawa w dniach (`delivery`)** | 3.00 | 3.00 | 1.00 | 2.00 | 4.00 | 1.00 | 5.00 | 1.42 |

*(Histogram rozkładu cen oraz wykres pudełkowy zostały wygenerowane i zapisane do pliku `analysis_charts.png`).*

### Analiza korelacji:
* **Współczynnik korelacji Pearsona (Cena vs Ocena):** **$-0.0036$**
* **Komentarz merytoryczny:** Zbliżony do zera współczynnik korelacji wskazuje na zupełny brak liniowej zależności pomiędzy ceną produktu a jego oceną. Wynik ten jest merytorycznie poprawny w kontekście syntetycznego zbioru danych e-commerce, w którym ocena jakościowa jest cechą niezależną od segmentu cenowego towaru.

---

## 7. Wymagania poziomu 5.0: Porównanie surowy HTML vs DOM

| Metoda pobrania | Wykryte rekordy | Opis |
| :--- | :--- | :--- |
| **Surowy HTML (`requests`)** | **0** | Strona serwuje szkielet HTML bez wierszy i kafelków; dane nie istnieją w źródle strony. |
| **Drzewo DOM po wykonaniu skryptów (`Selenium`)** | **412** | Silnik JavaScript asynchronicznie pobrał `products.json` i wyrenderował elementy. |

**Wniosek:**  
Dynamiczne renderowanie wprowadziło 412 rekordów za pośrednictwem JavaScriptu. Zastosowanie klasycznych bibliotek opartych wyłącznie o żądania HTTP uniemożliwia pozyskanie danych ze stron typu Single Page Application lub doładowywanych przez AJAX/fetch.

### Porównanie wydajności trybów przeglądarki:
* **Tryb Headless:** $296.78\text{ s}$ (~4.9 minuty)
* **Tryb Headed (z oknem):** $310.03\text{ s}$ (~5.1 minuty)
* Tryb Headless okazał się szybszy o ok. 13.25 s ze względu na brak konieczności renderowania warstwy graficznej okna systemu operacyjnego. Czas obu przebiegów był zdominowany przez celowe opóźnienia ($400 \times 0.5\text{ s} = 200\text{ s}$) oraz czasy doładowywania partii ($300\text{--}2000\text{ ms}$).

---

## 8. Wnioski końcowe

1. Parser poprawnie obsłużył wszystkie zaplanowane utrudnienia: ujednolicił rekordy z dwóch różnych struktur HTML, znormalizował zróżnicowane formaty walut, obsłużył losową kolejność pól w kartach oraz pobrał opisy z elementów zwijanych `<details>`.
2. Podczas wstępnej kontroli jakości wykryto 100% braków w kolumnie `delivery`, co wynikało z użycia przez autora selektora `#spec-shipping-days` zamiast `#spec-delivery`. Parser obsłużył ten brak bezpiecznie (jako `NaN`), nie przerywając działania programu, a po doprecyzowaniu selektora poprawnie wyekstrahował liczbę dni dostawy do typu `int64`.
3. Mechanizm deduplikacji bezbłędnie wyeliminował 12 zduplikowanych wpisów, dostarczając spójny zbiór 400 unikalnych produktów o 24 atrybutach.