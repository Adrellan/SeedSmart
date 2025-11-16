"""Scrape the State Department country list into JSON."""
import json
from typing import List, Dict

import requests
from bs4 import BeautifulSoup

URL = "https://history.state.gov/countries/all"


def scrape_countries(url: str = URL) -> List[Dict[str, str | int]]:
    """Fetch the country list and return dictionaries with numeric id + name."""
    response = requests.get(url, timeout=10)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    countries: List[Dict[str, str | int]] = []
    seen_slugs: set[str] = set()

    for link in soup.select("div.col-md-6 a[href^='/countries/']"):
        href = link.get("href", "").strip()
        if not href:
            continue

        slug = href.rstrip("/").split("/")[-1]
        if not slug or slug in seen_slugs:
            continue

        name = " ".join(link.get_text(strip=True).split())
        if name.endswith("*"):
            continue

        seen_slugs.add(slug)
        countries.append({"id": len(countries) + 1, "orszag": name})

    return countries


def main() -> None:
    countries = scrape_countries()
    # ensure_ascii=False keeps the original country names intact
    print(json.dumps(countries, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
