# Część WEB — Nova Market

Dynamiczny katalog produktów przygotowany jako rola **AUTOR** do laboratorium PJN. Cel: poziom **5.0**.

`mock.html` jest właściwą pierwszą stroną katalogu. Nazwa została zachowana, ponieważ aktualny parser ma ten adres wpisany na stałe: `http://localhost:8000/mock.html`.

## Architektura

```text
generate-data.mjs
        │
        ├──► data/products.json ──► catalog.js ──► tabela i karty w DOM
        │
        └──► details/product-XXXX.html ──► strony szczegółów
```

- [Generator](generate-data.mjs) tworzy 400 unikalnych produktów i 12 celowych duplikatów.
- [products.json](data/products.json) jest źródłem danych katalogu.
- [catalog.js](js/catalog.js) pobiera JSON przez `fetch`, a potem tworzy widoczne rekordy HTML.
- Katalog ma pięć stron: [1](../mock.html), [2](../catalog-page-2.html), [3](../catalog-page-3.html), [4](../catalog-page-4.html), [5](../catalog-page-5.html).
- [details](details) zawiera 400 indywidualnych stron szczegółów. Są statyczne, aby aktualny parser mógł odczytać dane od razu po wejściu na adres produktu.

## Uruchomienie

Z katalogu głównego repozytorium:

```powershell
python -m http.server 8000
```

Potem otwórz `http://localhost:8000/mock.html`.

Dane JSON i strony szczegółów są już zapisane w repozytorium. Generatora nie trzeba uruchamiać do zwykłego działania strony. Aby odtworzyć dane od zera:

```powershell
node web/generate-data.mjs
```

Uwaga: generator nadpisuje [products.json](data/products.json) i cały folder [details](details).

## Najważniejsze elementy kodu

### Dane dynamiczne

W [catalog.js](js/catalog.js#L81-L90) katalog pobiera dane:

```js
const response = await fetch("web/data/products.json");
const products = await response.json();
```

Źródło HTML katalogu nie ma rekordów produktów. Pliki katalogu mają tylko puste `tbody` i `#products-container`; JavaScript tworzy rekordy po pobraniu JSON-a.

### Tabela i karty

Generator ustawia `display_type` na `table` albo `card`. W [renderProduct](js/catalog.js#L30-L49) powstaje:

```html
<tr class="product-row">...</tr>
```

dla rekordu tabelarycznego albo:

```html
<article class="product-card">...</article>
```

dla kafelka. Produkt trafia tylko do jednej z tych struktur — połowa do tabeli, połowa do kart.

### Strony szczegółów

[detailPage](generate-data.mjs#L66-L81) generuje jeden HTML na produkt, np. [product-0001.html](details/product-0001.html). Każdy ma m.in. `#spec-ean`, `#spec-weight`, `#spec-dims`, `#spec-color` i `.description-text`.

### Porcjowe ładowanie

[loadBatch](js/catalog.js#L51-L65) pokazuje po 20 produktów. Losuje opóźnienie 300–2000 ms, blokuje `#load-more` podczas ładowania i ukrywa przycisk po wyczerpaniu rekordów.

## Poziom 3.0 — wymagania bazowe

| Wymaganie | Realizacja |
|---|---|
| Katalog produktów | [mock.html](../mock.html) jest pierwszą stroną katalogu. |
| Minimum 60 rekordów | Po pełnym doładowaniu strona 1 ma 82 rekordy; katalog ma 412 wpisów. |
| Minimum 10 atrybutów | ID, magazyn, nazwa, cena, kategoria, marka, dostępność, ocena, opinie, data, gwarancja i link szczegółów. |
| Dwie struktury HTML | `tr.product-row` oraz `article.product-card`. |
| Semantyczne selektory | Np. `.name`, `.price`, `.brand`, `.rating`, `.details-link`, `#products-table`, `#products-container`. |
| Brak nazw generowanych | Nazwy klas opisują dane, a nie wygląd strony. |

Wymóg strony statycznej bez JavaScriptu dotyczy wariantu 3.0. Przy poziomie 5.0 jest świadomie zastąpiony dynamicznym pobieraniem danych przez `fetch`.

## Poziom 4.0 — wymagania i utrudnienia

### Wymagania obowiązkowe

| Wymaganie | Realizacja |
|---|---|
| Pięć podstron | Strony katalogu 1–5 są połączone nawigacją. |
| Minimum 200 rekordów | 400 unikalnych produktów; 412 wpisów razem z duplikatami. |
| Szczegóły każdego produktu | 400 stron w [details](details). |
| Minimum 8 dodatkowych atrybutów | EAN, waga, wymiary, kolor, kraj pochodzenia, materiał, stan, opis, model, klasa energetyczna, dostawa. |
| Łącznie minimum 18 atrybutów | Model produktu ma ponad 22 pola. |

### Wybrane utrudnienia

| Utrudnienie | Realizacja |
|---|---|
| Ceny i różne waluty | Np. `1 299,00 zł`, `1 299,00 EUR`, `1 299.00 USD`. |
| Braki danych | Brak kategorii: 68 rekordów; brak dostępności: 69 rekordów. Oba pola przekraczają 15% wpisów. |
| Duplikaty | 12 kontrolowanych duplikatów rozrzuconych między podstronami. |
| Znaki specjalne | Twarde spacje w cenach, polskie znaki oraz marka `Żar & Córka`. |


## Poziom 5.0 — wymagania i utrudnienia

### Wymagania obowiązkowe

| Wymaganie | Realizacja |
|---|---|
| Dane poza źródłem HTML katalogu | Rekordy są w [products.json](data/products.json), a HTML ma puste kontenery. |
| Wstrzyknięcie przez JavaScript | [catalog.js](js/catalog.js#L83-L90) używa `fetch` i `renderProduct()`. |
| Doładowywanie porcjami | `#load-more` dodaje po 20 rekordów. |
| Minimum 400 rekordów | 400 unikalnych rekordów oraz 12 duplikatów. |
| Minimum 22 atrybuty | Każdy produkt ma ponad 22 pola podstawowe, logistyczne i techniczne. |
| Opóźnienie 300–2000 ms | Losowane w [loadBatch](js/catalog.js#L51-L65). |

### Wybrane utrudnienia

Zrealizowano trzy utrudnienia:

1. **Atrybut po interakcji** — opis jest wewnątrz rozwijanego `<details>`, np. na [product-0001.html](details/product-0001.html).
2. **Filtrowanie i sortowanie bez przeładowania** — [applyFilters](js/catalog.js#L67-L79) obsługuje wyszukiwanie, kategorię oraz sortowanie ceny i oceny.
3. **Losowa kolejność atrybutów karty** — [orderedCardFields](js/catalog.js#L19-L28) miesza metadane. Parser musi używać klas, np. `.brand` i `.rating`, a nie pozycji pola.

## Zgodność z aktualnym parserem

Katalog udostępnia selektory, których używa parser:

```text
table#products-table tbody tr.product-row
#products-container article.product-card
.name, .price, .cat, .brand, .stock, .rating, .reviews, .date, .warranty
.details-link
#spec-ean, #spec-weight, #spec-dims, #spec-color, #spec-origin,
#spec-material, #spec-condition, .description-text
```

Test parsera potwierdził 0 rekordów w surowym HTML katalogu i 82 rekordy w DOM po wykonaniu JavaScriptu. Obecny parser przechodzi stronę 1 i strony szczegółów, ale nie przechodzi jeszcze samodzielnie przez strony 2–5 ani nie eksportuje wszystkich 22+ pól. Jest to ograniczenie części `parser`, a nie części `web`.

## Zawartość folderu

```text
web/
├── README.md                — dokumentacja części WEB
├── generate-data.mjs        — generator JSON-a i stron szczegółów
├── data/products.json       — 412 wpisów katalogu
├── js/catalog.js            — fetch, renderowanie, filtry i doładowywanie
├── css/catalog.css          — style katalogu
├── css/details.css          — style stron szczegółów
└── details/                 — 400 stron produktów
```
