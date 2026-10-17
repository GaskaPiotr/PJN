import time
import logging
from urllib.parse import urljoin
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

def run_scraper(base_url: str, headless: bool = True):
    start_time = time.time()
    logging.info(f"Starting scraping task for {base_url} (headless={headless})")

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
                # Explicit wait for page initialization (Level 5.0 mandatory)
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                break
            except Exception as exc:
                backoff = 2 ** attempt
                logging.warning(f"Error accessing entry point: {exc}. Retrying in {backoff}s...")
                time.sleep(backoff)
                if attempt == max_retries - 1:
                    raise

        # Infinite loop handling load-more pagination (Level 5.0 mandatory)
        while True:
            try:
                button = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((By.ID, "load-more"))
                )
                button.click()
                time.sleep(0.5)  # Buffer for dynamic batch injection
            except Exception:
                logging.info("Pagination finished: button is unavailable or records exhausted.")
                break

        # Pass rendered DOM into BeautifulSoup parser
        soup = BeautifulSoup(driver.page_source, "lxml")

    except Exception as exc:
        logging.error(f"Critical execution error in Selenium runtime: {exc}")
        # Level 5.0 extension: error snapshot and raw DOM dump
        driver.save_screenshot("error_screenshot.png")
        with open("error_source.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        driver.quit()
        raise exc

    records = []

    # Parse primary catalog: Table structure
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

    # Parse primary catalog: Card structure
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

    # Scrape detail subpages (Level 4.0 mandatory: combine list and detail views)
    for rec in records:
        if not rec["details_url"]:
            continue
        time.sleep(0.5)  # Enforced mandatory delay between requests
        try:
            driver.get(rec["details_url"])
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
            logging.warning(f"Failed to fetch detail view for {rec['details_url']}: {e}")

    driver.quit()

    # Data transformation, deduplication, and export
    df = pd.DataFrame(records)
    initial_count = len(df)

    # Deduplication (Level 4.0 mandatory)
    df.drop_duplicates(subset=["id", "name"], inplace=True)
    dedup_count = len(df)

    # Dual export (Level 4.0 extension)
    df.to_csv("products_output.csv", index=False, encoding="utf-8")
    df.to_excel("products_output.xlsx", index=False)

    total_time = round(time.time() - start_time, 2)
    logging.info(
        f"Execution completed: {initial_count} items scraped, {dedup_count} remaining after deduplication. "
        f"Elapsed time: {total_time}s."
    )
    print(f"Task completed in {total_time}s. Records stored: {dedup_count}. Saved to CSV and XLSX.")

if __name__ == "__main__":
    run_scraper("http://localhost:8000/mock.html", headless=True)