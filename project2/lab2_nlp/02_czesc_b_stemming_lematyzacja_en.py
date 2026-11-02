"""LAB 2, czesc B: stemming i lematyzacja angielskiego tekstu.

Przyklad bazowy: W3_przyklady/example_08.py i example_09.py.
Uruchomienie: python 02_czesc_b_stemming_lematyzacja_en.py data/hamlet.txt
"""
from __future__ import annotations
import argparse
import csv
import re
from pathlib import Path
import nltk
from nltk.stem import SnowballStemmer, WordNetLemmatizer

OUTPUT = Path("output")

def ensure_nltk_data() -> None:
    resources = (("punkt", "tokenizers/punkt"), ("punkt_tab", "tokenizers/punkt_tab"),
                 ("wordnet", "corpora/wordnet"), ("averaged_perceptron_tagger_eng", "taggers/averaged_perceptron_tagger_eng"))
    for package, resource in resources:
        try:
            nltk.data.find(resource)
        except LookupError:
            nltk.download(package, quiet=True)

def wordnet_pos(tag: str) -> str:
    return {"J": "a", "V": "v", "N": "n", "R": "r"}.get(tag[0], "n")

def main() -> None:
    parser = argparse.ArgumentParser(description="Stemming i lematyzacja tekstu angielskiego")
    parser.add_argument("file", type=Path, help="plik .txt z Project Gutenberg")
    args = parser.parse_args()
    if not args.file.is_file():
        raise SystemExit(f"Nie znaleziono pliku: {args.file}")
    ensure_nltk_data()
    OUTPUT.mkdir(exist_ok=True)
    # Zadanie B.1: wczytuje angielski tekst i porządkuje białe znaki.
    text = re.sub(r"\s+", " ", args.file.read_text(encoding="utf-8")).strip()
    # Zadanie B.2: pobiera pierwszych 5 zdań zawierających co najmniej 5 tokenów.
    sentences = [s for s in nltk.sent_tokenize(text) if len(nltk.word_tokenize(s)) >= 7][:5]
    if len(sentences) < 5:
        raise SystemExit("Tekst zawiera mniej niz 5 odpowiednio dlugich zdan.")
    # Zadanie B.3: ustawia algorytm stemmingu Snowball i lematyzator WordNet.
    stemmer, lemmatizer = SnowballStemmer("english"), WordNetLemmatizer()
    rows: list[dict[str, str]] = []
    for number, sentence in enumerate(sentences, start=1):
        # Zadanie B.3: dzieli zdanie na słowa i pomija znaki interpunkcyjne.
        tokens = [t.lower() for t in nltk.word_tokenize(sentence) if t.isalpha()]
        for token, tag in nltk.pos_tag(tokens):
            # Zadanie B.3: zapisuje dla każdego słowa jego rdzeń i lemat.
            rows.append({"zdanie": str(number), "token": token, "tag_pos": tag,
                         "rdzen_snowball": stemmer.stem(token),
                         "lemat_wordnet": lemmatizer.lemmatize(token, pos=wordnet_pos(tag))})
    # Zadanie B.4: zapisuje tabelę token → rdzeń → lemat do pliku CSV.
    with (OUTPUT / "czesc_b_tabela.csv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=rows[0].keys())
        writer.writeheader(); writer.writerows(rows)
    # Zadanie B.4: znajduje słowa, dla których stemming i lematyzacja dały inny wynik.
    different = [row for row in rows if row["rdzen_snowball"] != row["lemat_wordnet"]]
    summary = ["LAB 2 — czesc B: stemming i lematyzacja", "", "Wybrane 5 zdan:"]
    summary.extend(f"{i}. {sentence}" for i, sentence in enumerate(sentences, start=1))
    summary.extend(["", "Co najmniej trzy rozne wyniki (token -> rdzen -> lemat):"])
    summary.extend(f"{r['token']} -> {r['rdzen_snowball']} -> {r['lemat_wordnet']}" for r in different[:3])
    summary.append("\nPelna tabela token -> rdzen -> lemat: czesc_b_tabela.csv")
    (OUTPUT / "czesc_b_wyniki.txt").write_text("\n".join(summary), encoding="utf-8")
    print("\n".join(summary))

if __name__ == "__main__":
    main()
