"""LAB 2, część D: porównanie stemmerów Porter i Lancaster.

Punkt wyjścia: W3_przyklady/example_08.py.
Uruchomienie: python 04_czesc_d_porownanie_stemmerow.py data/hamlet.txt
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

from nltk.stem import LancasterStemmer, PorterStemmer

OUTPUT = Path("output")

# Ustawia UTF-8 w konsoli Windows, aby raport poprawnie wyświetlał polskie znaki i strzałki.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Porównuje stemmery języka angielskiego")
    parser.add_argument("file", type=Path, help="angielski plik .txt")
    args = parser.parse_args()
    if not args.file.is_file():
        raise SystemExit(f"Nie znaleziono pliku: {args.file}")

    # Zadanie D.1: wczytuje angielski tekst i wyciąga z niego unikalne słowa.
    text = args.file.read_text(encoding="utf-8").lower()
    words = sorted(set(re.findall(r"[a-z]+", text)))
    # Zadanie D.1: tworzy dwa różne algorytmy stemmingu.
    porter, lancaster = PorterStemmer(), LancasterStemmer()
    rows = [{"slowo": word, "porter": porter.stem(word), "lancaster": lancaster.stem(word)}
            for word in words]
    # Zadanie D.2: zostawia słowa, dla których algorytmy zwróciły inne rdzenie.
    different = [row for row in rows if row["porter"] != row["lancaster"]]
    if len(different) < 5:
        raise SystemExit("Tekst nie zawiera pięciu słów o różnych wynikach stemmingu.")

    OUTPUT.mkdir(exist_ok=True)
    # Zadanie D.2: tabela zawiera co najmniej pięć porównywanych słów.
    with (OUTPUT / "czesc_d_porownanie_stemmerow.csv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=("slowo", "porter", "lancaster"))
        writer.writeheader()
        writer.writerows(different)

    # Zadanie D.3: przykład nadmiernego obcinania — różne słowa mają wspólny rdzeń.
    over_words = ("general", "generous")
    over_porter = [porter.stem(word) for word in over_words]
    over_lancaster = [lancaster.stem(word) for word in over_words]
    # Zadanie D.3: przykład niedostatecznego obcinania — formy „go” i „goes” nie schodzą się.
    under_words = ("go", "goes")
    under_porter = [porter.stem(word) for word in under_words]
    under_lancaster = [lancaster.stem(word) for word in under_words]

    sample = different[:5]
    report = [
        "LAB 2 — część D: porównanie stemmerów", "",
        "Pięć słów z tekstu o różnych wynikach:",
        *(f"{r['slowo']} → Porter: {r['porter']}, Lancaster: {r['lancaster']}" for r in sample),
        "",
        "Wniosek: Lancaster jest zwykle bardziej agresywny, bo częściej zwraca krótszy rdzeń. "
        "Porter jest zwykle sensowniejszy do ogólnej analizy tekstu, ponieważ mniej obcina słowa.",
        "",
        "Przykład nadmiernego obcinania:",
        f"{over_words[0]} / {over_words[1]} → Porter: {over_porter[0]} / {over_porter[1]}; "
        f"Lancaster: {over_lancaster[0]} / {over_lancaster[1]}.",
        "Dwa różne wyrazy dostają ten sam rdzeń, więc algorytm zaciera różnicę znaczenia.",
        "",
        "Przykład niedostatecznego obcinania:",
        f"{under_words[0]} / {under_words[1]} → Porter: {under_porter[0]} / {under_porter[1]}; "
        f"Lancaster: {under_lancaster[0]} / {under_lancaster[1]}.",
        "To formy tego samego czasownika, ale różne rdzenie oznaczają, że algorytm ich nie połączył.",
        "",
        "Pełna tabela wszystkich różnych wyników: czesc_d_porownanie_stemmerow.csv",
    ]
    (OUTPUT / "czesc_d_wyniki.txt").write_text("\n".join(report), encoding="utf-8")
    print("\n".join(report))


if __name__ == "__main__":
    main()
