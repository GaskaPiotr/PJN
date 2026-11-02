"""LAB 2, część E: polskie narzędzia językowe.

Punkt wyjścia: W3_przyklady/example_08.py i example_09.py.
Uruchomienie: python 05_czesc_e_polski_stemming_lematyzacja.py data/pan_tadeusz.txt
Przed pierwszym uruchomieniem: python -m spacy download pl_core_news_sm
"""
from __future__ import annotations

import argparse
import csv
import importlib.resources as importlib_resources
import sys
from pathlib import Path
from typing import Any

import spacy
from nltk.stem import SnowballStemmer

# pystempel 2.0.0 odwołuje się do nazw usuniętych w Pythonie 3.14.
# Są to tylko podpowiedzi typów, więc ich bezpieczne zastąpienie przywraca zgodność.
if not hasattr(importlib_resources, "Package") or not hasattr(importlib_resources, "Resource"):
    importlib_resources.Package = Any
    importlib_resources.Resource = Any
from pystempel import Stemmer

OUTPUT = Path("output")

# Ustawia UTF-8 w konsoli Windows, aby raport poprawnie wyświetlał polskie znaki i strzałki.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Polska tokenizacja, stemming i lematyzacja")
    parser.add_argument("file", type=Path, help="polski plik .txt")
    parser.add_argument("--characters", type=int, default=1500, help="długość analizowanego fragmentu")
    args = parser.parse_args()
    if not args.file.is_file():
        raise SystemExit(f"Nie znaleziono pliku: {args.file}")
    try:
        # Zadanie E.1: ładuje polski model spaCy do tokenizacji i lematyzacji.
        nlp = spacy.load("pl_core_news_sm")
    except OSError as error:
        raise SystemExit("Brak modelu. Uruchom: python -m spacy download pl_core_news_sm") from error

    OUTPUT.mkdir(exist_ok=True)
    # Zadanie E.1: wczytuje fragment polskiej książki.
    fragment = args.file.read_text(encoding="utf-8")[:args.characters]
    # Zadanie E.1: dzieli fragment na tokeny i dla każdego podaje lemat oraz część mowy.
    doc = nlp(fragment)
    polish_stemmer = Stemmer.default()
    # Zadanie E.2: tworzy angielski stemmer, celowo użyty później na polskich wyrazach.
    english_stemmer = SnowballStemmer("english")
    rows = []
    for token in doc:
        if token.is_alpha:
            # Zadanie E.1–2: zapisuje polski rdzeń, lemat i błędny rdzeń z angielskiego stemmera.
            rows.append({"token": token.text, "rdzen_stempel": polish_stemmer(token.text.lower()),
                         "lemat_spacy": token.lemma_, "czesc_mowy": token.pos_,
                         "rdzen_angielski_snowball": english_stemmer.stem(token.text.lower())})
    if len(rows) < 5:
        raise SystemExit("Wybrany fragment zawiera mniej niż pięć wyrazów.")

    # Zadanie E.1: zapisuje tabelę wyników polskich narzędzi do CSV.
    with (OUTPUT / "czesc_e_polski_tabela.csv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    # Zadanie E.2: bierze pięć zwykłych polskich wyrazów, pomijając nazwy własne z nagłówka książki.
    five_words = [row for row in rows if row["czesc_mowy"] != "PROPN"][:5]
    # Zadanie E.3: pobiera pełną listę języków, które obsługuje Snowball.
    languages = SnowballStemmer.languages
    report = [
        "LAB 2 — część E: polszczyzna wymaga innych narzędzi", "",
        f"Analizowany fragment: pierwsze {args.characters} znaków pliku {args.file}",
        "",
        "Pięć polskich słów — wynik angielskiego SnowballStemmer:",
        *(f"{row['token']} → {row['rdzen_angielski_snowball']}" for row in five_words),
        "",
        "Wniosek: angielski stemmer nie zna polskiej fleksji, więc jego wyniki nie są wiarygodne dla polszczyzny.",
        "",
        "Języki obsługiwane przez SnowballStemmer:",
        ", ".join(languages),
        "",
        f"Czy lista zawiera język polski? {'Tak' if 'polish' in languages else 'Nie'}.",
        "SnowballStemmer nie obsługuje polskiego, dlatego w tej części użyty jest Stempel do rdzeni "
        "oraz spaCy z modelem pl_core_news_sm do tokenizacji i lematyzacji.",
        "",
        "Pełna tabela: czesc_e_polski_tabela.csv",
    ]
    (OUTPUT / "czesc_e_wyniki.txt").write_text("\n".join(report), encoding="utf-8")
    print("\n".join(report))


if __name__ == "__main__":
    main()
