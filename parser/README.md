Parser part

## How to run

1. Install required packages:
    ```bash
    pip install -r requirements.txt
    ```
2. Start the local server (in terminal 1):
    ```bash
    python -m http.server 8000
    ```
3. Run the scraper (in terminal 2):
    ```bash
    python scraper.py
    ```

## Chosen requirements

# 4.0:
    • eksport do dwóch formatów jednocześnie (np. CSV oraz XLSX lub JSON); 
    • logowanie przebiegu do pliku wraz z podsumowaniem: liczba stron, rekordów, błędów, czas działania; 

# 5.0:
    • automatyczny zrzut ekranu i zapis źródła strony przy każdym błędzie, do celów diagnostycznych; 
    • tryb headless wraz z pomiarem czasu działania w obu trybach; 
