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
    
    try:
        # Exponential backoff retry mechanism (Level 5.0 mandatory)
        max_retries = 3
        for attempt in range(max_retries):
            try:
                driver.get(base_url)
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
                btn = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((By.ID, "load-more"))
                )
                btn.click()
                time.sleep(0.5)
            except Exception:
                logging.info("Load more finished or button not present.")
                break

        soup = BeautifulSoup(driver.page_source, "lxml")

    except Exception as exc:
        errors_count += 1
        logging.error(f"Critical execution error: {exc}")
        save_error_diagnostic(driver, "critical")
        driver.quit()
        raise exc

    records = []

    # 1. Parse table
    table_rows = soup.select("table#products-table tbody tr.product-row")
    for row in table_rows:
        link_elem = row.select_one(".details-link")
        record = {
            "id": row.get("data-id"),
            "warehouse": row.get("data-warehouse"),
            "name": cleaners.clean_text(row.select_one(".name").get_text()) if row.select_one(".name") else None,
            "price": cleaners.clean_price(row.select_one(".price").get_text()) if row.select_one(".price") else None,
            "category": cleaners.clean_text(row.select_one(".cat").get_text()) if row.select_one(".cat") else None,
            "brand": cleaners.clean_text(row.select_one(".brand").get_text()) if row.select_one(".brand") else None,
            "availability": cleaners.clean_text(row.select_one(".stock").get_text()) if row.select_one(".stock") else None,
            "rating": cleaners.clean_price(row.select_one(".rating").get_text()) if row.select_one(".rating") else None,
            "reviews_count": cleaners.clean_int(row.select_one(".reviews").get_text()) if row.select_one(".reviews") else None,
            "date_added": cleaners.clean_text(row.select_one(".date").get_text()) if row.select_one(".date") else None,
            "warranty_months": cleaners.clean_int(row.select_one(".warranty").get_text()) if row.select_one(".warranty") else None,
            "details_url": urljoin(base_url, link_elem.get("href")) if link_elem else None
        }
        records.append(record)

    # 2. Parse cards
    cards = soup.select("#products-container article.product-card")
    for card in cards:
        link_elem = card.select_one(".details-link")
        record = {
            "id": card.get("data-id"),
            "warehouse": card.get("data-warehouse"),
            "name": cleaners.clean_text(card.select_one(".name").get_text()) if card.select_one(".name") else None,
            "price": cleaners.clean_price(card.select_one(".price").get_text()) if card.select_one(".price") else None,
            "category": cleaners.clean_text(card.select_one(".cat").get_text()) if card.select_one(".cat") else None,
            "brand": cleaners.clean_text(card.select_one(".brand").get_text()) if card.select_one(".brand") else None,
            "availability": cleaners.clean_text(card.select_one(".stock").get_text()) if card.select_one(".stock") else None,
            "rating": cleaners.clean_price(card.select_one(".rating").get_text()) if card.select_one(".rating") else None,
            "reviews_count": cleaners.clean_int(card.select_one(".reviews").get_text()) if card.select_one(".reviews") else None,
            "date_added": cleaners.clean_text(card.select_one(".date").get_text()) if card.select_one(".date") else None,
            "warranty_months": cleaners.clean_int(card.select_one(".warranty").get_text()) if card.select_one(".warranty") else None,
            "details_url": urljoin(base_url, link_elem.get("href")) if link_elem else None
        }
        records.append(record)

    # Scrape detail subpages (Level 4.0 mandatory)
    for rec in records:
        if not rec["details_url"]:
            continue
        time.sleep(0.5)
        try:
            driver.get(rec["details_url"])
            pages_visited_count += 1
            detail_soup = BeautifulSoup(driver.page_source, "lxml")
            
            ean = detail_soup.select_one("#spec-ean")
            weight = detail_soup.select_one("#spec-weight")
            dims = detail_soup.select_one("#spec-dims")
            color = detail_soup.select_one("#spec-color")
            origin = detail_soup.select_one("#spec-origin")
            mat = detail_soup.select_one("#spec-material")
            condition = detail_soup.select_one("#spec-condition")
            desc = detail_soup.select_one(".description-text")

            rec["ean_code"] = cleaners.clean_text(ean.get_text()) if ean else None
            rec["weight"] = cleaners.clean_text(weight.get_text()) if weight else None
            rec["dimensions"] = cleaners.clean_text(dims.get_text()) if dims else None
            rec["color"] = cleaners.clean_text(color.get_text()) if color else None
            rec["country_of_origin"] = cleaners.clean_text(origin.get_text()) if origin else None
            rec["material"] = cleaners.clean_text(mat.get_text()) if mat else None
            rec["condition"] = cleaners.clean_text(condition.get_text()) if condition else None
            rec["description"] = cleaners.clean_text(desc.get_text()) if desc else None

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
    
    # 1. Run in Headless mode
    print("Running in HEADLESS mode...")
    time_headless, dom_records_headless = run_scraper(target_url, headless=True)
    
    # 2. Run in Headed mode
    print("Running in HEADED mode...")
    time_headed, dom_records_headed = run_scraper(target_url, headless=False)

    # Performance comparison logged
    summary_msg = (
        f"\nComparison: Headless mode took {time_headless}s | "
        f"Headed mode took {time_headed}s"
    )
    logging.info(summary_msg)
    print(summary_msg)

    # Compare HTML to rendered DOM (Requirement 5.0)
    compare_raw_vs_dom(target_url, dom_records_headless)
