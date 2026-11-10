import os
import re
from collections import Counter
import matplotlib.pyplot as plt
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from stop_words import get_stop_words

# Upewnienie się, że zasoby NLTK są pobrane
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')
try:
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    nltk.download('punkt_tab')

DATA_PATH = os.path.join("data", "pan_tadeusz.txt")
OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def rysuj_histogram(dane, tytul, nazwa_pliku):
    etykiety = [" ".join(gram) if isinstance(gram, tuple) else gram for gram, _ in dane]
    wartosci = [ilosc for _, ilosc in dane]

    plt.figure(figsize=(10, 5))
    plt.barh(etykiety[::-1], wartosci[::-1], color="#2b5c8f")
    plt.title(tytul)
    plt.xlabel("Liczba wystąpień")
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, nazwa_pliku), dpi=300)
    plt.close()

def main():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        surowy_tekst = f.read()

    # 1. Usuwanie stop words i analiza n-gramów
    polskie_stop_words = set(get_stop_words("polish"))
    
    # Tokenizacja i normalizacja (małe litery, tylko słowa alfanumeryczne)
    wszystkie_slowa = word_tokenize(surowy_tekst.lower(), language="polish")
    slowa_alfanumeryczne = [s for s in wszystkie_slowa if s.isalnum() and not s.isdigit()]
    slowa_bez_stop = [s for s in slowa_alfanumeryczne if s not in polskie_stop_words]

    # Generowanie n-gramów po usunięciu stop words
    bigramy_bez_stop = list(nltk.bigrams(slowa_bez_stop))
    trigramy_bez_stop = list(nltk.trigrams(slowa_bez_stop))

    top10_bigramy = Counter(bigramy_bez_stop).most_common(10)
    top10_trigramy = Counter(trigramy_bez_stop).most_common(10)

    # Zapis wykresów
    rysuj_histogram(top10_bigramy, "Top 10 Bigramów (bez stop words)", "top_10_bigramow_bez_stopwords.png")
    rysuj_histogram(top10_trigramy, "Top 10 Trigramów (bez stop words)", "top_10_trigramow_bez_stopwords.png")

    # 2. Wyszukiwanie nazw własnych (Regex)
    # Podział na zdania, aby badać słowa nienastępujące na początku zdania
    zdania = sent_tokenize(surowy_tekst, language="polish")
    
    # Wzorzec: słowo z wielkiej litery poprzedzone spacją (wyklucza początek napisu)
    # Obsługuje polskie znaki diakrytyczne
    regex_nazwy = re.compile(r'(?<=\s)[A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż]+')

    znalezione_nazwy = []
    for zdanie in zdania:
        # Dzielimy na linijki, aby uwzględnić strukturę wersów poezji
        linie = zdanie.split('\n')
        for linia in linie:
            # Pomijamy pierwsze słowo wersu/zdania
            reszta_linii = re.sub(r'^\s*([—–-]\s*)?\S+', '', linia)
            dopasowania = regex_nazwy.findall(reszta_linii)
            # Odrzucamy słowa, które po zamianie na małe litery są stop-słowami
            dopasowania = [n for n in dopasowania if n.lower() not in polskie_stop_words]
            znalezione_nazwy.extend(dopasowania)

    top10_nazwy_wlasne = Counter(znalezione_nazwy).most_common(10)

    # 3. Zapis wyników i podsumowania do pliku tekstowego
    wyniki_sciezka = os.path.join(OUTPUT_DIR, "czesc_g_wyniki.txt")
    with open(wyniki_sciezka, "w", encoding="utf-8") as f:
        f.write("=== CZĘŚĆ G: WYNIKI ANALIZY ===\n\n")
        f.write(f"Liczba słów przed usunięciem stop words: {len(slowa_alfanumeryczne)}\n")
        f.write(f"Liczba słów po usunięciu stop words: {len(slowa_bez_stop)}\n\n")

        f.write("--- TOP 10 BIGRAMÓW (BEZ STOP WORDS) ---\n")
        for bg, count in top10_bigramy:
            f.write(f"{' '.join(bg)}: {count}\n")
        f.write("\n")

        f.write("--- TOP 10 TRIGRAMÓW (BEZ STOP WORDS) ---\n")
        for tg, count in top10_trigramy:
            f.write(f"{' '.join(tg)}: {count}\n")
        f.write("\n")

        f.write("--- TOP 10 NAZW WŁASNYCH (REGEX) ---\n")
        for nazwa, count in top10_nazwy_wlasne:
            f.write(f"{nazwa}: {count}\n")
        f.write("\n")

        f.write("--- WNIOSKI (STYL VS TREŚĆ) ---\n")
        f.write("1. Bez stop words bigramy i trigramy ujawniają rzeczywiste motywy i treść utworu\n")
        f.write("   (np. powiązania postaci, relacje przestrzenne, kluczowe rekwizyty), zamiast struktur\n")
        f.write("   składniowych i spójników ('i w', 'że się', 'do niego').\n")
        f.write("2. Wariant ze stop words lepiej charakteryzuje styl autora (rytmiczność, budowę zdań,\n")
        f.write("   stylizację retoryczną), natomiast wariant oczyszczony ukazuje semantykę tekstu.\n")
        f.write("3. Zastosowane wyrażenie regularne skutecznie eliminuje słowa rozpoczynające zdania,\n")
        f.write("   co minimalizuje fałszywe wykrycia wyrazów pisanych wielką literą z powodów interpunkcyjnych.\n")

    print("[Część G] Zakończono pomyślnie. Wyniki i wykresy zapisano w folderze output/.")

if __name__ == "__main__":
    main()