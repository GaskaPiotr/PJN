"""LAB 2, część F: cztery miary podobieństwa napisów.

Punkt wyjścia: W3_przyklady/example_18.py.
Uruchomienie: python 06_czesc_f_miary_podobienstwa.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import textdistance

OUTPUT = Path("output")

# Ustawia UTF-8 w konsoli Windows, aby raport poprawnie wyświetlał polskie znaki i punktory.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def compare(first: str, second: str) -> dict[str, float | int | str]:
    longest = max(len(first), len(second))
    # Zadanie F.1 i F.3: oblicza Levenshteina oraz trzy dodatkowe miary z textdistance.
    lev = textdistance.levenshtein.distance(first, second)
    damerau = textdistance.damerau_levenshtein.distance(first, second)
    jaro_winkler = textdistance.jaro_winkler.similarity(first, second)
    jaccard = textdistance.jaccard.similarity(first.split(), second.split())
    return {"pierwszy": first, "drugi": second, "levenshtein": lev,
            "damerau_levenshtein": damerau, "jaro_winkler": jaro_winkler, "jaccard": jaccard,
            # Normalizacja pozwala porównać odległości z miarami podobieństwa w skali 0–1.
            "lev_similarity": 1 - lev / longest, "damerau_similarity": 1 - damerau / longest}


def main() -> None:
    # Zadanie F.3: zawiera parę z polecenia i trzy własne pary testowe.
    pairs = [("Ala ma kota", "Ala posiada kota"), ("kot", "kto"),
             ("Kraków", "Krakow"), ("programowanie", "programowanie")]
    results = [compare(first, second) for first, second in pairs]
    # Zadanie F.4: znajduje parę o największym rozrzucie wyników po normalizacji.
    for result in results:
        values = (result["lev_similarity"], result["damerau_similarity"],
                  result["jaro_winkler"], result["jaccard"])
        result["roznica_miar"] = max(values) - min(values)
    most_different = max(results, key=lambda result: result["roznica_miar"])

    OUTPUT.mkdir(exist_ok=True)
    lines = [
        "LAB 2 — część F: więcej miar podobieństwa", "",
        "Zasady działania miar:",
        "• Levenshtein: minimalna liczba wstawień, usunięć i zamian pojedynczych znaków.",
        "• Damerau-Levenshtein: jak Levenshtein, ale zamiana sąsiednich znaków miejscami kosztuje 1.",
        "• Jaro-Winkler: podobieństwo znaków; premiuje wspólny początek napisów.",
        "• Jaccard: porównuje zbiory słów wspólnych i wszystkich słów z obu zdań.",
        "",
        "Wyniki (Levenshtein i Damerau to odległości: mniej = bardziej podobne; pozostałe: więcej = bardziej podobne):",
    ]
    for result in results:
        lines.extend(["", f"{result['pierwszy']!r} / {result['drugi']!r}",
                      f"  Levenshtein: {result['levenshtein']}",
                      f"  Damerau-Levenshtein: {result['damerau_levenshtein']}",
                      f"  Jaro-Winkler: {result['jaro_winkler']:.3f}",
                      f"  Jaccard: {result['jaccard']:.3f}"])
    lines.extend(["", "Największa różnica między miarami:",
                  f"{most_different['pierwszy']!r} / {most_different['drugi']!r}",
                  "Różnica wynika z tego, że miary znakowe obserwują kolejność liter, a Jaccard patrzy tylko na wspólne słowa. "
                  "Dodatkowo Damerau-Levenshtein szczególnie łagodnie traktuje przestawienie sąsiednich liter."])
    (OUTPUT / "czesc_f_wyniki.txt").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
