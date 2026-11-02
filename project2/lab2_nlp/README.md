# Przetwarzanie jezyka naturalnego — Laboratorium 2

> Najpierw przeczytaj ten README przed uruchomieniem skryptów. Projekt obejmuje zadania na oceny **3.0 i 4.0**; część na **5.0** nie została jeszcze zrealizowana. Gotowe wyniki znajdują się w folderze `output/`.

Przygotowana jest kompletna implementacja zadań na **3.0 i 4.0**. Każda część ma osobny skrypt, wyniki są zapisywane do `output/`, a teksty źródłowe znajdują się w `data/`.

## Struktura

- `01_czesc_a_ngramy_pl.py` — czesc A: czyszczenie, zdania, slowa, n-gramy i wykresy;
- `02_czesc_b_stemming_lematyzacja_en.py` — czesc B: 5 zdan, Snowball i WordNet;
- `03_czesc_c_odleglosc_edycyjna.py` — czesc C: Levenshtein z `textdistance`;
- `04_czesc_d_porownanie_stemmerow.py` — część D: Porter kontra Lancaster;
- `05_czesc_e_polski_stemming_lematyzacja.py` — część E: Stempel, spaCy i polszczyzna;
- `06_czesc_f_miary_podobienstwa.py` — część F: cztery miary z `textdistance`;
- `data/` — tu nalezy zapisac pobrane pliki `.txt`;
- `output/` — wyniki tworzone podczas uruchomienia.

## Instalacja (Windows PowerShell)

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m spacy download pl_core_news_sm
```

Skrypty przy pierwszym uruchomieniu pobiora potrzebne dane NLTK lokalnie. Nie korzystaja z platnych API ani wag modeli.

## Teksty

1. Pobierz plik z Wolnych Lektur, np. [Pan Tadeusz](https://wolnelektury.pl/media/book/txt/pan-tadeusz.txt), i zapisz jako `data/pan_tadeusz.txt`.
2. Pobierz dowolny angielski tekst z Project Gutenberg, np. [Hamlet](https://www.gutenberg.org/ebooks/27761), w wersji Plain Text UTF-8 i zapisz jako `data/hamlet.txt`.

## Uruchomienie

```powershell
python 01_czesc_a_ngramy_pl.py data/pan_tadeusz.txt
python 02_czesc_b_stemming_lematyzacja_en.py data/hamlet.txt
python 03_czesc_c_odleglosc_edycyjna.py
python 04_czesc_d_porownanie_stemmerow.py data/hamlet.txt
python 05_czesc_e_polski_stemming_lematyzacja.py data/pan_tadeusz.txt
python 06_czesc_f_miary_podobienstwa.py
```

Po uruchomieniu części A powstaną pliki `top_10_bigramow.png`, `top_10_trigramow.png` i `czesc_a_wyniki.txt`. Część B zapisze tabelę `token -> rdzeń -> lemat` w CSV oraz wybrane zdania. Części C–F zapiszą odpowiednie raporty tekstowe i tabele w folderze `output/`.
