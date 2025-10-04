"""Scrape iban.com country codes (country + alpha-2) into JSON."""
from __future__ import annotations

import json
from typing import Dict, List

import requests
from bs4 import BeautifulSoup

URL = "https://www.iban.com/country-codes"


def scrape_country_codes(url: str = URL) -> List[Dict[str, str]]:
    response = requests.get(url, timeout=10)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    table = soup.select_one("table.downloads")
    if table is None:
        raise RuntimeError("Could not find country code table on page")

    entries: List[Dict[str, str]] = []
    for row in table.select("tbody tr"):
        cells = [cell.get_text(strip=True) for cell in row.select("td")]
        if len(cells) < 2:
            continue

        country, alpha2 = cells[0], cells[1]
        if not country or not alpha2:
            continue

        entries.append({"country": country, "alpha2": alpha2})

    return entries


def main() -> None:
    data = scrape_country_codes()
    print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
