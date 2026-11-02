"""LAB 2, czesc C: odleglosc Levenshteina przez textdistance.

Przyklad bazowy: W3_przyklady/example_18.py.
Uruchomienie: python 03_czesc_c_odleglosc_edycyjna.py
"""
from pathlib import Path
import textdistance

OUTPUT = Path("output")

def main() -> None:
    # Zadanie C.1: dwa zdania podane w poleceniu.
    first, second = "Ala ma kota", "Ala posiada kota"
    # Zadanie C.2: biblioteka textdistance liczy odległość Levenshteina.
    distance = textdistance.levenshtein.distance(first, second)
    report = f'''LAB 2 — czesc C: odleglosc edycyjna

Zdanie 1: {first}
Zdanie 2: {second}
Odleglosc Levenshteina (textdistance): {distance}

Wyjasnienie (zadanie C.3):
Wspolne pozostaja fragmenty „Ala ” oraz „a kota”. Srodkowy fragment „ma” mozna
zamienic w „posiada” przez 6 operacji: zamiane „m” na „p” (1 operacja) i wstawienie
liter „osiad” miedzy „p” i „a” (5 operacji). Razem: 1 + 5 = 6.
'''
    OUTPUT.mkdir(exist_ok=True)
    (OUTPUT / "czesc_c_wyniki.txt").write_text(report, encoding="utf-8")
    print(report)

if __name__ == "__main__":
    main()
