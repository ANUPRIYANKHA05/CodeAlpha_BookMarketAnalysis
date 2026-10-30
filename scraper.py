import argparse
import csv
import re
import time
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://books.toscrape.com/"
START_URL = urljoin(BASE_URL, "catalogue/page-1.html")
OUTPUT = Path("data/books_raw.csv")
HEADERS = {"User-Agent": "Mozilla/5.0 (CodeAlpha internship learning project)"}
RATING_MAP = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}
FIELDS = ["title", "category", "price_gbp", "rating", "in_stock", "stock_count",
          "upc", "num_reviews", "description", "product_url", "image_url"]


def get_soup(session, url, retries=3):
    for attempt in range(1, retries + 1):
        try:
            resp = session.get(url, headers=HEADERS, timeout=15)
            resp.raise_for_status()
            resp.encoding = "utf-8"
            return BeautifulSoup(resp.text, "html.parser")
        except requests.RequestException as exc:
            print(f"  [warn] {url} failed ({exc}); attempt {attempt}/{retries}")
            time.sleep(2 * attempt)
    return None


def parse_book_page(session, url):
    soup = get_soup(session, url)
    if soup is None:
        return None
    title = soup.select_one("div.product_main h1").get_text(strip=True)
    crumbs = soup.select("ul.breadcrumb li a")
    category = crumbs[2].get_text(strip=True) if len(crumbs) > 2 else ""
    star = soup.select_one("p.star-rating")
    rating = next((RATING_MAP[c] for c in star["class"] if c in RATING_MAP), None)
    table = {row.th.get_text(strip=True): row.td.get_text(strip=True)
             for row in soup.select("table.table-striped tr")}
    price = float(re.sub(r"[^\d.]", "", table.get("Price (excl. tax)", "0")) or 0)
    availability = table.get("Availability", "")
    stock_match = re.search(r"\((\d+) available\)", availability)
    desc_tag = soup.select_one("#product_description ~ p")
    image = soup.select_one("div.item.active img")
    return {
        "title": title,
        "category": category,
        "price_gbp": price,
        "rating": rating,
        "in_stock": "In stock" in availability,
        "stock_count": int(stock_match.group(1)) if stock_match else 0,
        "upc": table.get("UPC", ""),
        "num_reviews": int(table.get("Number of reviews", 0) or 0),
        "description": desc_tag.get_text(strip=True) if desc_tag else "",
        "product_url": url,
        "image_url": urljoin(url, image["src"]) if image else "",
    }


def scrape(limit=None, delay=0.3):
    books = []
    url = START_URL
    with requests.Session() as session:
        while url:
            print(f"Listing page: {url}")
            soup = get_soup(session, url)
            if soup is None:
                break
            for link in soup.select("article.product_pod h3 a"):
                record = parse_book_page(session, urljoin(url, link["href"]))
                if record:
                    books.append(record)
                    print(f"  [{len(books):4d}] {record['title'][:60]}")
                if limit and len(books) >= limit:
                    return books
                time.sleep(delay)
            nxt = soup.select_one("li.next a")
            url = urljoin(url, nxt["href"]) if nxt else None
    return books


def save_csv(books, path=OUTPUT):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(books)
    print(f"\nSaved {len(books)} books -> {path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape books.toscrape.com")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()
    save_csv(scrape(limit=args.limit))