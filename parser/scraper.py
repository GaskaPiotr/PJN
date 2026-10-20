import time
import logging
from datetime import datetime
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import cleaners

# Logging configuration (Level 4.0 extension)
logging.basicConfig(
    filename='scraping.log',
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    encoding='utf-8'
)

def save_error_diagnostic(driver, error_type: str):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    screenshot_name = f"error_{error_type}_{timestamp}.png"
    source_name = f"error_{error_type}_{timestamp}.html"
    
    try:
        driver.save_screenshot(screenshot_name)
        with open(source_name, "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        logging.info(f"Diagnostic dump saved: {screenshot_name}, {source_name}")
    except Exception as exc:
        logging.error(f"Failed to capture error diagnostic: {exc}")

def compare_raw_vs_dom(url: str, dom_record_count: int):
    try:
        resp = requests.get(url)
        raw_soup = BeautifulSoup(resp.text, "lxml")
        
        raw_table_items = len(raw_soup.select("table#products-table tbody tr.product-row"))
        raw_card_items = len(raw_soup.select("#products-container article.product-card"))
        raw_total = raw_table_items + raw_card_items
        
        comparison_text = (
            f"\n--- RAW HTML vs DOM COMPARISON ---\n"
            f"Raw HTML (without JS / requests): {raw_total} records found.\n"
            f"Rendered DOM (with Selenium / JS executed): {dom_record_count} records found.\n"
            f"Conclusion: Dynamic rendering injected {dom_record_count - raw_total} records via JavaScript fetch."
        )
        print(comparison_text)
        logging.info(comparison_text)
    except Exception as exc:
        logging.error(f"Failed to compare raw HTML vs DOM: {exc}")

def get_spec_val(soup, *selectors):
    for sel in selectors:
        el = soup.select_one(sel)
        if el and el.get_text(strip=True):
            return cleaners.clean_text(el.get_text())
    return None

def run_scraper(base_url: str, headless: bool = True) -> tuple[float, int]:
    start_time = time.time()
    pages_visited_count = 0
    errors_count = 0

    logging.info(f"=== Starting run (headless={headless}) ===")

    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(options=chrome_options)
    
    catalog_pages = [
        urljoin(base_url, "mock.html"),
        urljoin(base_url, "catalog-page-2.html"),
        urljoin(base_url, "catalog-page-3.html"),
        urljoin(base_url, "catalog-page-4.html"),
        urljoin(base_url, "catalog-page-5.html"),
    ]

    records = []

    try:
        for page_url in catalog_pages:
            # Exponential backoff retry mechanism (Level 5.0 mandatory)
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    driver.get(page_url)
                    pages_visited_count += 1
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.TAG_NAME, "body"))
                    )
                    break
                except Exception as e:
                    errors_count += 1
                    save_error_diagnostic(driver, "page_load")
                    backoff = 2 ** attempt
                    logging.warning(f"Error accessing entry point: {e}. Retrying in {backoff}s...")
                    time.sleep(backoff)
                    if attempt == max_retries - 1:
                        raise

            # Infinite loop handling load-more pagination (Level 5.0 mandatory)
            while True:
                try:
                    btn = WebDriverWait(driver, 4).until(
                        EC.element_to_be_clickable((By.ID, "load-more"))
                    )
                    btn.click()
                    time.sleep(0.3)
                except Exception:
                    logging.info(f"Load more finished or button not present on {page_url}.")
                    break

            soup = BeautifulSoup(driver.page_source, "lxml")

            table_rows = soup.select("table#products-table tbody tr.product-row")
            for row in table_rows:
                link_elem = row.select_one(".details-link")
                price_raw = row.select_one(".price").get_text() if row.select_one(".price") else None
                record = {
                    "id": row.get("data-id"),
                    "warehouse": row.get("data-warehouse"),
                    "name": cleaners.clean_text(row.select_one(".name").get_text()) if row.select_one(".name") else None,
                    "price": cleaners.clean_price(price_raw),
                    "currency": cleaners.extract_currency(price_raw),
                    "category": cleaners.clean_text(row.select_one(".cat").get_text()) if row.select_one(".cat") else None,
                    "brand": cleaners.clean_text(row.select_one(".brand").get_text()) if row.select_one(".brand") else None,
                    "availability": cleaners.clean_text(row.select_one(".stock").get_text()) if row.select_one(".stock") else None,
                    "rating": cleaners.clean_price(row.select_one(".rating").get_text()) if row.select_one(".rating") else None,
                    "reviews_count": cleaners.clean_int(row.select_one(".reviews").get_text()) if row.select_one(".reviews") else None,
                    "date_added": cleaners.clean_text(row.select_one(".date").get_text()) if row.select_one(".date") else None,
                    "warranty_months": cleaners.clean_int(row.select_one(".warranty").get_text()) if row.select_one(".warranty") else None,
                    "details_url": urljoin(page_url, link_elem.get("href")) if link_elem else None
                }
                records.append(record)

            cards = soup.select("#products-container article.product-card")
            for card in cards:
                link_elem = card.select_one(".details-link")
                price_raw = card.select_one(".price").get_text() if card.select_one(".price") else None
                record = {
                    "id": card.get("data-id"),
                    "warehouse": card.get("data-warehouse"),
                    "name": cleaners.clean_text(card.select_one(".name").get_text()) if card.select_one(".name") else None,
                    "price": cleaners.clean_price(price_raw),
                    "currency": cleaners.extract_currency(price_raw),
                    "category": cleaners.clean_text(card.select_one(".cat").get_text()) if card.select_one(".cat") else None,
                    "brand": cleaners.clean_text(card.select_one(".brand").get_text()) if card.select_one(".brand") else None,
                    "availability": cleaners.clean_text(card.select_one(".stock").get_text()) if card.select_one(".stock") else None,
                    "rating": cleaners.clean_price(card.select_one(".rating").get_text()) if card.select_one(".rating") else None,
                    "reviews_count": cleaners.clean_int(card.select_one(".reviews").get_text()) if card.select_one(".reviews") else None,
                    "date_added": cleaners.clean_text(card.select_one(".date").get_text()) if card.select_one(".date") else None,
                    "warranty_months": cleaners.clean_int(card.select_one(".warranty").get_text()) if card.select_one(".warranty") else None,
                    "details_url": urljoin(page_url, link_elem.get("href")) if link_elem else None
                }
                records.append(record)

    except Exception as exc:
        errors_count += 1
        logging.error(f"Critical execution error: {exc}")
        save_error_diagnostic(driver, "critical")
        driver.quit()
        raise exc

    # Scrape detail subpages (Level 4.0 mandatory)
    for idx, rec in enumerate(records, 1):
        if not rec["details_url"]:
            continue
        time.sleep(0.5)
        try:
            driver.get(rec["details_url"])
            pages_visited_count += 1
            detail_soup = BeautifulSoup(driver.page_source, "lxml")
            
            rec["ean_code"] = get_spec_val(detail_soup, "#spec-ean", ".spec-ean")
            rec["weight"] = get_spec_val(detail_soup, "#spec-weight", ".spec-weight")
            rec["dimensions"] = get_spec_val(detail_soup, "#spec-dims", ".spec-dims")
            rec["color"] = get_spec_val(detail_soup, "#spec-color", ".spec-color")
            rec["country_of_origin"] = get_spec_val(detail_soup, "#spec-origin", ".spec-origin")
            rec["material"] = get_spec_val(detail_soup, "#spec-material", ".spec-material")
            rec["condition"] = get_spec_val(detail_soup, "#spec-condition", ".spec-condition")
            rec["model"] = get_spec_val(detail_soup, "#spec-model", ".spec-model")
            rec["energy_class"] = get_spec_val(detail_soup, "#spec-energy", "#spec-energy-class", ".spec-energy")
            rec["delivery"] = cleaners.clean_int(get_spec_val(detail_soup, "#spec-shipping-days", "#spec-delivery"))
            rec["description"] = get_spec_val(detail_soup, ".description-text", "#spec-details p", "details p")

        except Exception as e:
            errors_count += 1
            logging.warning(f"Error fetching detail {rec['details_url']}: {e}")
            save_error_diagnostic(driver, "detail_page")

    driver.quit()

    df = pd.DataFrame(records)
    initial_count = len(df)
    df.drop_duplicates(subset=["id", "name"], inplace=True)
    dedup_count = len(df)

    # Dual export (Level 4.0 extension)
    df.to_csv("products_output.csv", index=False, encoding="utf-8")
    df.to_excel("products_output.xlsx", index=False)

    elapsed_time = round(time.time() - start_time, 2)
    
    # Complete execution summary (Level 4.0 extension)
    logging.info(
        f"Summary (headless={headless}): "
        f"pages_visited={pages_visited_count}, "
        f"raw_records={initial_count}, "
        f"unique_records={dedup_count}, "
        f"errors_encountered={errors_count}, "
        f"execution_time={elapsed_time}s"
    )

    return elapsed_time, initial_count

if __name__ == "__main__":
    target_url = "http://localhost:8000/mock.html"

    print("Measuring performance in both modes (Level 5.0 requirement)...")
    time_headless, dom_records_headless = run_scraper(target_url, headless=True)
    time_headed, dom_records_headed = run_scraper(target_url, headless=False)

    summary_msg = (
        f"\nComparison: Headless mode took {time_headless}s | "
        f"Headed mode took {time_headed}s"
    )
    logging.info(summary_msg)
    print(summary_msg)

    # Compare HTML to rendered DOM (Requirement 5.0)
    compare_raw_vs_dom(target_url, dom_records_headless)