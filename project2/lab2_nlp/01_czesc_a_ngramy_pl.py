"""LAB 2, czesc A: n-gramy slowne w polskim tekscie.

Przyklad bazowy: W3_przyklady/example_16.py i example_17.py.
Uruchomienie: python 01_czesc_a_ngramy_pl.py data/pan_tadeusz.txt
"""
from __future__ import annotations
import argparse
import re
from collections import Counter
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import nltk
from nltk.util import ngrams

OUTPUT = Path("output")

def ensure_punkt() -> None:
    for package, resource in (("punkt", "tokenizers/punkt"), ("punkt_tab", "tokenizers/punkt_tab")):
        try:
            nltk.data.find(resource)
        except LookupError:
            nltk.download(package, quiet=True)

def clean_text(text: str) -> str:
    """Zostawia litery (takze polskie), spacje i konce zdan."""
    # Zadanie A.2: zamienia wszystkie litery na małe, więc „Pan” i „pan” są tym samym słowem.
    text = text.lower()
    # Zadanie A.2: usuwa znaki specjalne, ale zostawia . ! ? potrzebne do podziału na zdania.
    text = re.sub(r"[^\w\s.!?]", " ", text, flags=re.UNICODE)
    text = re.sub(r"[_\d]", " ", text)
    # Zadanie A.2: zamienia kilka spacji lub enterów na jedną spację.
    return re.sub(r"\s+", " ", text).strip()

def draw_top(counter: Counter[tuple[str, ...]], title: str, filename: str) -> list[tuple[str, int]]:
    # Zadanie A.6: pobiera 10 n-gramów, które występują najczęściej.
    top = [(" ".join(gram), count) for gram, count in counter.most_common(10)]
    labels, values = zip(*top)
    # Zadanie A.6: tworzy i zapisuje histogram, czyli wykres słupkowy.
    plt.figure(figsize=(12, 6))
    plt.bar(range(len(values)), values, color="#315b7d")
    plt.xticks(range(len(labels)), labels, rotation=35, ha="right")
    plt.ylabel("Czestosc")
    plt.title(title)
    plt.tight_layout()
    plt.savefig(OUTPUT / filename, dpi=160)
    plt.close()
    return top

def main() -> None:
    parser = argparse.ArgumentParser(description="Analiza n-gramow polskiego tekstu")
    parser.add_argument("file", type=Path, help="plik .txt z Wolnych Lektur")
    args = parser.parse_args()
    if not args.file.is_file():
        raise SystemExit(f"Nie znaleziono pliku: {args.file}")
    ensure_punkt()
    OUTPUT.mkdir(exist_ok=True)
    # Zadanie A.1–2: wczytuje książkę i oczyszcza jej tekst.
    text = clean_text(args.file.read_text(encoding="utf-8"))
    # Zadanie A.3: dzieli tekst na zdania.
    sentences = nltk.sent_tokenize(text, language="polish")
    # Zadanie A.3: dzieli każde zdanie na wyrazy; interpunkcja nie trafia na listę.
    words = [word for sentence in sentences for word in nltk.word_tokenize(sentence, language="polish") if word.isalpha()]
    # Zadanie A.4–5: tworzy unigramy, bigramy i trigramy oraz liczy ich wystąpienia.
    unigrams, bigrams, trigrams = Counter(words), Counter(ngrams(words, 2)), Counter(ngrams(words, 3))
    # Zadanie A.6: tworzy dwa wykresy dla 10 najczęstszych par i trójek słów.
    top_bigrams = draw_top(bigrams, "10 najczestszych bigramow", "top_10_bigramow.png")
    top_trigrams = draw_top(trigrams, "10 najczestszych trigramow", "top_10_trigramow.png")
    # Zadanie A.3 i A.7: raport zawiera liczby oraz odpowiedzi do pytań z polecenia.
    report = [
        "LAB 2 — czesc A: n-gramy w tekscie polskim", f"Plik zrodlowy: {args.file}",
        f"Liczba zdan: {len(sentences)}", f"Liczba wyrazow: {len(words)}",
        f"Liczba roznych unigramow: {len(unigrams)}", f"Liczba roznych bigramow: {len(bigrams)}",
        f"Liczba roznych trigramow: {len(trigrams)}", "", "10 najczestszych bigramow:",
        *(f"{gram}: {count}" for gram, count in top_bigrams), "", "10 najczestszych trigramow:",
        *(f"{gram}: {count}" for gram, count in top_trigrams), "", "Odpowiedzi:",
        f"1. W analizowanym tekscie dominuja bigramy: {', '.join(g for g, _ in top_bigrams[:3])}.",
        f"2. Najczestsze trigramy ({', '.join(g for g, _ in top_trigrams[:3])}) sa kandydatami na powtarzalne zwroty autora.",
        "3. Unigramy licza pojedyncze, czesto bardzo czeste slowa; bigramy sa bardziej rozproszone, ale pokazuja sasiedztwo slow i kontekst.",
    ]
    (OUTPUT / "czesc_a_wyniki.txt").write_text("\n".join(report), encoding="utf-8")
    print("\n".join(report))
    print("\nZapisano wykresy i raport w katalogu output/.")

if __name__ == "__main__":
    main()
