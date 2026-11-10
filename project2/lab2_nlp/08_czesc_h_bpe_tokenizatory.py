import csv
import os
import matplotlib.pyplot as plt
from tokenizers import Tokenizer
from tokenizers.models import BPE
from tokenizers.pre_tokenizers import Whitespace
from tokenizers.trainers import BpeTrainer
from transformers import AutoTokenizer

DATA_PATH = os.path.join("data", "pan_tadeusz.txt")
OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

SLOWA_TESTOWE = ["nieprzetłumaczalny", "hiperparametryzacja", "kotkowi", "niepodległościowy"]

ZDANIA_PL = [
    "Litwo! Ojczyzno moja! ty jesteś jak zdrowie.",
    "Wprowadzenie nowych technologii zmienia rynek pracy.",
    "Wczoraj wieczorem poszliśmy na długi spacer po parku.",
    "Przetwarzanie języka naturalnego jest kluczowym działem sztucznej inteligencji.",
    "Za oknem padał drobny, gęsty deszcz i wiał chłodny wiatr."
]

ZDANIA_EN = [
    "To be, or not to be, that is the question.",
    "Artificial intelligence is transforming modern industries.",
    "We went for a very long walk in the central park yesterday.",
    "Natural language processing allows computers to understand text.",
    "A cold wind began to blow as small drops of rain started falling."
]

def trenuj_bpe(sciezka_tekstu, vocab_size):
    tokenizer = Tokenizer(BPE(unk_token="[UNK]"))
    tokenizer.pre_tokenizer = Whitespace()
    trainer = BpeTrainer(
        vocab_size=vocab_size,
        special_tokens=["[UNK]", "[CLS]", "[SEP]", "[PAD]", "[MASK]"],
        initial_alphabet=[]
    )
    tokenizer.train([sciezka_tekstu], trainer)
    return tokenizer

def main():
    print("[Część H] Trening tokenizatorów BPE...")
    
    # 1. Trening 3 modeli BPE o różnych rozmiarach słownika
    tok_1k = trenuj_bpe(DATA_PATH, 1000)
    tok_5k = trenuj_bpe(DATA_PATH, 5000)
    tok_30k = trenuj_bpe(DATA_PATH, 30000)

    # Zapis wymaganego modelu 5k do głównego katalogu
    tok_5k.save("tokenizer_pl.json")
    print("  Zapisano tokenizer_pl.json w katalogu głównym.")

    # 2. Test podziału wybranych słów
    tabela_slow = []
    for slowo in SLOWA_TESTOWE:
        podzial_1k = " | ".join(tok_1k.encode(slowo).tokens)
        podzial_5k = " | ".join(tok_5k.encode(slowo).tokens)
        podzial_30k = " | ".join(tok_30k.encode(slowo).tokens)
        tabela_slow.append({
            "Slowo": slowo,
            "BPE_1000": podzial_1k,
            "BPE_5000": podzial_5k,
            "BPE_30000": podzial_30k
        })

    csv_path = os.path.join(OUTPUT_DIR, "czesc_h_podzial_slow.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Slowo", "BPE_1000", "BPE_5000", "BPE_30000"])
        writer.writeheader()
        writer.writerows(tabela_slow)

    # 3. Pobranie gotowych tokenizatorów
    print("  Pobieranie/ładowanie gotowych tokenizatorów z Hugging Face...")
    tok_gpt2 = AutoTokenizer.from_pretrained("gpt2")
    tok_herbert = AutoTokenizer.from_pretrained("allegro/herbert-base-cased")
    tok_bielik = AutoTokenizer.from_pretrained("speakleash/Bielik-7B-v0.1")

    def licz_tokeny_wlasny(tok, zdania):
        return [len(tok.encode(z).tokens) for z in zdania]

    def licz_tokeny_hf(tok, zdania):
        return [len(tok.tokenize(z)) for z in zdania]

    # Liczenie liczby tokenów na zdanie
    wyniki_pl = {
        "Własny BPE (5k)": licz_tokeny_wlasny(tok_5k, ZDANIA_PL),
        "GPT-2": licz_tokeny_hf(tok_gpt2, ZDANIA_PL),
        "HerBERT": licz_tokeny_hf(tok_herbert, ZDANIA_PL),
        "Bielik": licz_tokeny_hf(tok_bielik, ZDANIA_PL)
    }

    wyniki_en = {
        "Własny BPE (5k)": licz_tokeny_wlasny(tok_5k, ZDANIA_EN),
        "GPT-2": licz_tokeny_hf(tok_gpt2, ZDANIA_EN),
        "HerBERT": licz_tokeny_hf(tok_herbert, ZDANIA_EN),
        "Bielik": licz_tokeny_hf(tok_bielik, ZDANIA_EN)
    }

    srednie_pl = [sum(wyniki_pl[m]) / len(ZDANIA_PL) for m in wyniki_pl]
    srednie_en = [sum(wyniki_en[m]) / len(ZDANIA_EN) for m in wyniki_en]
    modele = list(wyniki_pl.keys())

    # 4. Wykres słupkowy
    x = range(len(modele))
    szerokosc = 0.35

    plt.figure(figsize=(10, 5))
    plt.bar([i - szerokosc/2 for i in x], srednie_pl, width=szerokosc, label="Polski", color="#1f77b4")
    plt.bar([i + szerokosc/2 for i in x], srednie_en, width=szerokosc, label="Angielski", color="#ff7f0e")
    plt.xticks(x, modele)
    plt.ylabel("Średnia liczba tokenów na zdanie")
    plt.title("Porównanie efektywności tokenizatorów dla zdań PL i EN")
    plt.legend()
    plt.grid(axis="y", linestyle="--", alpha=0.7)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "porownanie_tokenizatorow.png"), dpi=300)
    plt.close()

    # 5. Zapis wyników i odpowiedzi na pytania teoretyczne
    with open(os.path.join(OUTPUT_DIR, "czesc_h_wyniki.txt"), "w", encoding="utf-8") as f:
        f.write("=== CZĘŚĆ H: PODZIAŁ SŁÓW DLA RÓŻNYCH ROZMIARÓW SŁOWNIKA ===\n")
        for row in tabela_slow:
            f.write(f"\nSłowo: {row['Slowo']}\n")
            f.write(f"  - 1000:  {row['BPE_1000']}\n")
            f.write(f"  - 5000:  {row['BPE_5000']}\n")
            f.write(f"  - 30000: {row['BPE_30000']}\n")

        f.write("\n=== ŚREDNIA LICZBA TOKENÓW NA ZDANIE ===\n")
        for m in modele:
            f.write(f"{m:20} -> PL: {sum(wyniki_pl[m])/len(ZDANIA_PL):.2f} tokenów | EN: {sum(wyniki_en[m])/len(ZDANIA_EN):.2f} tokenów\n")

        f.write("\n=== ODPOWIEDZI NA PYTANIA TEORETYCZNE ===\n")
        f.write("1. Który tokenizator jest najbardziej ekonomiczny dla tekstu polskiego, a który dla angielskiego?\n")
        f.write("   - Dla tekstu polskiego najbardziej ekonomiczny jest Bielik lub HerBERT (oraz własny BPE dla słów\n")
        f.write("     z domeny). Bielik i HerBERT były trenowane na bogatych korpusach języka polskiego.\n")
        f.write("   - Dla tekstu angielskiego najefektywniejszy jest GPT-2, którego słownik zoptymalizowano pod angielski.\n\n")

        f.write("2. Jak zmienia się liczba tokenów wraz ze wzrostem rozmiaru słownika Twojego tokenizatora?\n")
        f.write("   - Wraz ze wzrostem słownika (1k -> 5k -> 30k) słowa dzielone są na coraz dłuższe fragmenty,\n")
        f.write("     a całe wyrazy częściej stają się pojedynczymi tokenami. Zależność NIE JEST liniowa – następuje\n")
        f.write("     szybkie nasycenie (prawo malejących przychodów); rozbudowa słownika o kolejne tysiące obejmuje\n")
        f.write("     bardzo rzadkie zbitki liter i formy fleksyjne.\n\n")

        f.write("3. Dlaczego tokenizator wytrenowany na jednej książce wypada dobrze na niej, a gorzej na innym tekście?\n")
        f.write("   - Tokenizator nauczył się słownictwa, archaizmów i morfemów typowych dla jednego autora/epoki.\n")
        f.write("     Nowoczesne słowa techniczne czy publicystyczne nie występowały w korpusie treningowym,\n")
        f.write("     więc zostaną pofragmentowane na pojedyncze litery lub bardzo drobne podsłowa.\n\n")

        f.write("4. Jaki jest związek między tym ćwiczeniem a pojęciem 'podatku językowego' (fertility/token tax)?\n")
        f.write("   - Modele trenowane głównie na języku angielskim (np. rodzina GPT) dzielą jedno polskie słowo\n")
        f.write("     na 2–4 tokeny, podczas gdy słowo angielskie to najczęściej 1 token. Sprawia to, że przetwarzanie\n")
        f.write("     języka polskiego w modelach komercyjnych jest 2-3x droższe, wolniejsze i szybciej wyczerpuje\n")
        f.write("     okno kontekstowe modelu. Wybór dedykowanego tokenizatora (np. Bielik) eliminuje ten podatek.\n")

    print("[Część H] Zakończono pomyślnie. Wygenerowano tokenizer_pl.json, wykres i pliki wyników.")

if __name__ == "__main__":
    main()