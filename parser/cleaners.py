import re

def clean_price(raw_text: str | None) -> float | None:
    if not raw_text:
        return None
    cleaned = raw_text.replace('\xa0', '').replace('&nbsp;', '').strip()
    match = re.search(r'(\d+[\s\.,]?\d*[\.,]?\d*)', cleaned)
    if not match:
        return None
    val_str = match.group(1).replace(' ', '').replace(',', '.')
    try:
        return float(val_str)
    except ValueError:
        return None

def clean_int(raw_text: str | None) -> int | None:
    if not raw_text:
        return None
    match = re.search(r'\d+', raw_text)
    return int(match.group(0)) if match else None

def clean_text(raw_text: str | None) -> str | None:
    if not raw_text:
        return None
    return " ".join(raw_text.replace('\xa0', ' ').replace('&nbsp;', ' ').split()).strip()