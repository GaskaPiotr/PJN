import csv
import os
import nltk
from nltk.tokenize import word_tokenize
import spacy
from stop_words import get_stop_words
from tokenizers import Tokenizer

DATA_PATH = os.path.join("data", "pan_tadeusz.txt")
TOKENIZER_JSON = "tokenizer_pl.json"
OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def main():
    print("[Część I] Porównanie wszystkich metod przetwarzania tekstu...")
    
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        caly_tekst = f.read()

    # Wybór reprezentatywnego fragmentu (pierwsze 4000 znaków)
    fragment = caly_tekst[1000:5000]

    # Metoda 1: Same wyrazy (tokenizacja i oczyszczenie)
    slowa = [w.lower() for w in word_tokenize(fragment, language="polish") if w.isalnum()]
    n_slowa = len(slowa)
    vocab_slowa = len(set(slowa))

    # Metoda 2: Wyrazy po lematyzacji (spaCy)
    nlp = spacy.load("pl_core_news_sm", disable=["ner", "parser"])
    doc = nlp(fragment.lower())
    lematy = [token.lemma_ for token in doc if token.is_alpha]
    n_lematy = len(lematy)
    vocab_lematy = len(set(lematy))

    # Metoda 3: Wyrazy bez stop words
    polskie_stop = set(get_stop_words("polish"))
    slowa_bez_stop = [w for w in slowa if w not in polskie_stop]
    n_bez_stop = len(slowa_bez_stop)
    vocab_bez_stop = len(set(slowa_bez_stop))

    # Metoda 4: Tokeny podsłowowe z własnego BPE
    if not os.path.exists(TOKENIZER_JSON):
        raise FileNotFoundError("Brak pliku tokenizer_pl.json! Najpierw uruchom skrypt 08_czesc_h.")
    
    tokenizer_bpe = Tokenizer.from_file(TOKENIZER_JSON)
    tokeny_bpe = tokenizer_bpe.encode(fragment).tokens
    n_bpe = len(tokeny_bpe)
    vocab_bpe = len(set(tokeny_bpe))

    # Tabela wyników
    dane_tabeli = [
        {"Metoda": "1. Same wyrazy", "Liczba jednostek (długość)": n_slowa, "Rozmiar słownika (unikalne)": vocab_slowa},
        {"Metoda": "2. Wyrazy po lematyzacji", "Liczba jednostek (długość)": n_lematy, "Rozmiar słownika (unikalne)": vocab_lematy},
        {"Metoda": "3. Wyrazy bez stop words", "Liczba jednostek (długość)": n_bez_stop, "Rozmiar słownika (unikalne)": vocab_bez_stop},
        {"Metoda": "4. Tokeny podsłowowe (BPE)", "Liczba jednostek (długość)": n_bpe, "Rozmiar słownika (unikalne)": vocab_bpe}
    ]

    # Zapis do CSV
    tabela_csv = os.path.join(OUTPUT_DIR, "czesc_i_tabela.csv")
    with open(tabela_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Metoda", "Liczba jednostek (długość)", "Rozmiar słownika (unikalne)"])
        writer.writeheader()
        writer.writerows(dane_tabeli)

    # Zapis podsumowania i wniosków
    with open(os.path.join(OUTPUT_DIR, "czesc_i_wyniki.txt"), "w", encoding="utf-8") as f:
        f.write("=== CZĘŚĆ I: PORÓWNANIE METOD PRZETWARZANIA TEKSTU ===\n\n")
        for row in dane_tabeli:
            f.write(f"{row['Metoda']:<30} | Jednostek: {row['Liczba jednostek (długość)']:<5} | Unikalnych: {row['Rozmiar słownika (unikalne)']}\n")

        f.write("\n=== WNIOSKI: KTÓRA METODA NAJMOCNIEJ ZMNIEJSZA SŁOWNIK I JAKIM KOSZTEM ===\n")
        f.write("1. Lematyzacja vs Same wyrazy:\n")
        f.write("   Lematyzacja redukuje rozmiar unikalnego słownika poprzez sprowadzenie różnych form fleksyjnych\n")
        f.write("   do formy podstawowej. Koszt: utrata informacji gramatycznej (czas, przypadek, liczba, osoba).\n\n")
        f.write("2. Usunięcie stop words:\n")
        f.write("   Drastycznie skraca całkowity tekst (długość sekwencji) oraz zmniejsza słownik o najczęstsze\n")
        f.write("   spójniki i zaimki. Koszt: całkowita utrata spójności składniowej i stylu, tekst nie nadaje się\n")
        f.write("   do generowania zdań przez LLM, choć jest świetny pod klasyczne wyszukiwanie IR.\n\n")
        f.write("3. Tokenizacja podsłowowa (BPE):\n")
        f.write("   BPE daje stały, z góry zdefiniowany rozmiar aktywnego słownika podsłów bez problemu słów nieznanych\n")
        f.write("   (out-of-vocabulary / OOV). Kosztem jest wydłużenie sekwencji (liczby jednostek) w przypadku rzadkich\n")
        f.write("   słów oraz brak bezpośredniej interpretowalności lingwistycznej takich tokenów.\n")

    print("[Część I] Zakończono pomyślnie. Tabela i wnioski zapisane w katalogu output/.")

if __name__ == "__main__":
    main()