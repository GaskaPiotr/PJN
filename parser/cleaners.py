import re

def clean_price(raw_text: str | None) -> float | None:
    if not raw_text:
        return None
    cleaned = raw_text.replace('\xa0', ' ').replace('&nbsp;', ' ').strip()
    match = re.search(r'(\d[\d\s\.,]*)', cleaned)
    if not match:
        return None
    num_str = re.sub(r'[^\d,\.]', '', match.group(1))
    if ',' in num_str and '.' in num_str:
        if num_str.rfind(',') > num_str.rfind('.'):
            num_str = num_str.replace('.', '').replace(',', '.')
        else:
            num_str = num_str.replace(',', '')
    elif ',' in num_str:
        num_str = num_str.replace(',', '.')
    try:
        return float(num_str)
    except ValueError:
        return None

def extract_currency(raw_text: str | None) -> str:
    if not raw_text:
        return "PLN"
    upper = raw_text.upper()
    if "EUR" in upper or "€" in upper:
        return "EUR"
    if "USD" in upper or "$" in upper:
        return "USD"
    if "ZŁ" in upper or "PLN" in upper or "ZL" in upper:
        return "PLN"
    return "PLN"

def clean_int(raw_text: str | None) -> int | None:
    if not raw_text:
        return None
    match = re.search(r'\d+', raw_text)
    return int(match.group(0)) if match else None

def clean_text(raw_text: str | None) -> str | None:
    if not raw_text:
        return None
    val = " ".join(raw_text.replace('\xa0', ' ').replace('&nbsp;', ' ').split()).strip()
    return val if val else None