#!/usr/bin/env python3
"""Return the most expensive crop(s) for a given country/year (optionally by category)."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

CSV_FILENAME = "all_products_prices_6cats_2000_2024.csv"


def locate_csv() -> Path:
    script_path = Path(__file__).resolve()
    candidate_roots = [
        script_path.parent,                # python_scripts
        script_path.parent.parent,         # src
        script_path.parent.parent.parent,  # server
        script_path.parent.parent.parent.parent,  # project root
    ]

    for root in candidate_roots:
        csv_path = root / CSV_FILENAME
        if csv_path.exists():
            return csv_path

    cwd_csv = Path.cwd() / CSV_FILENAME
    if cwd_csv.exists():
        return cwd_csv

    searched = [str(root / CSV_FILENAME) for root in candidate_roots]
    searched.append(str(cwd_csv))
    raise FileNotFoundError("CSV file not found. Checked: " + ", ".join(searched))


CSV_PATH = locate_csv()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--country", required=True, help="Country name (case-insensitive)")
    parser.add_argument("--year", required=True, type=int, help="Target year (2000-2024)")
    parser.add_argument(
        "--category_label",
        dest="category_labels",
        action="append",
        help="Optional category label or key to filter (can be repeated or comma separated)",
    )
    return parser.parse_args()


def normalize(text: Optional[str]) -> str:
    return (text or "").strip().lower()


def parse_category_inputs(raw_values: Optional[List[str]]) -> List[str]:
    if not raw_values:
        return []

    categories: List[str] = []
    seen: set[str] = set()

    for raw in raw_values:
        if raw is None:
            continue
        for part in str(raw).split(","):
            trimmed = part.strip()
            if not trimmed:
                continue
            normalized = normalize(trimmed)
            if normalized in seen:
                continue
            seen.add(normalized)
            categories.append(trimmed)

    return categories


def load_filtered_rows(country: str, year: int) -> List[Tuple[float, Dict[str, Any]]]:
    country_norm = normalize(country)
    rows: List[Tuple[float, Dict[str, Any]]] = []

    with CSV_PATH.open(encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            try:
                row_year = int(row.get("year", ""))
            except ValueError:
                continue
            if row_year != year:
                continue

            if country_norm and normalize(row.get("country")) != country_norm:
                continue

            try:
                price = float(row.get("price_eur_tonne", "nan"))
            except (TypeError, ValueError):
                continue

            rows.append((price, row))

    return rows


def find_best_for_category(
    rows: List[Tuple[float, Dict[str, Any]]],
    category_norm: Optional[str],
) -> Optional[Dict[str, Any]]:
    best_row: Optional[Dict[str, Any]] = None
    best_price: float = float("-inf")

    for price, row in rows:
        if category_norm:
            labels = {
                normalize(row.get("category_label")),
                normalize(row.get("category_key")),
            }
            if category_norm not in labels:
                continue

        if best_row is None or price > best_price:
            best_row = row
            best_price = price

    return best_row


def main() -> None:
    args = parse_args()
    categories = parse_category_inputs(args.category_labels)
    rows = load_filtered_rows(args.country, args.year)

    query_categories: List[Optional[str]]
    if categories:
        query_categories = categories
    else:
        query_categories = [None]

    results = []
    for category in query_categories:
        normalized = normalize(category) if category is not None else None
        record = find_best_for_category(rows, normalized)
        results.append(
            {
                "requested_category": category,
                "found": record is not None,
                "record": record,
            }
        )

    payload: Dict[str, Any]
    if categories:
        payload = {
            "found": any(result["found"] for result in results),
            "country": args.country,
            "year": args.year,
            "requested_categories": categories,
            "results": results,
        }
    else:
        payload = {
            "found": results[0]["found"],
            "country": args.country,
            "year": args.year,
            "requested_categories": None,
            "record": results[0]["record"],
        }

    print(json.dumps(payload, ensure_ascii=False))


if __name__ == "__main__":
    main()
