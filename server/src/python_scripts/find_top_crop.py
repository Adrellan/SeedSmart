#!/usr/bin/env python3
"""Return the best crop(s) for a given country/year (optionally by category)
based on the highest price_eur_tonne / cost_eur_tonne ratio."""

from __future__ import annotations

import argparse
import csv
import io
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

CSV_FILENAME = "alap_kiegeszitve_costs_full_modded.csv"


# ----------------------------- utils ----------------------------- #
def locate_csv() -> Path:
    script_path = Path(__file__).resolve()
    candidate_roots = [
        script_path.parent,                           # python_scripts
        script_path.parent.parent,                    # src
        script_path.parent.parent.parent,             # server
        script_path.parent.parent.parent.parent,      # project root
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


def sniff_delimiter(path: Path) -> str:
    """Try to detect delimiter, default to ';' if unsure (common in EU CSVs)."""
    with path.open("r", encoding="utf-8", newline="") as f:
        sample = f.read(4096)
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
        return dialect.delimiter
    except Exception:
        # Fallback: if semicolons appear a lot, assume ';', else ','
        return ";" if sample.count(";") >= sample.count(",") else ","


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


def to_float_mixed(num: Any) -> Optional[float]:
    """
    Convert strings like '1,234.56', '1.234,56', '4835,25', '3862,9' to float.
    Returns None if not parseable.
    """
    if num is None:
        return None
    s = str(num).strip()
    if s == "" or s.lower() == "nan":
        return None

    # remove non-breaking spaces / normal spaces
    s = s.replace("\xa0", "").replace(" ", "")

    # Case 1: both '.' and ',' present -> assume thousands + decimal
    if "," in s and "." in s:
        # Heuristic: if last comma occurs after last dot => comma is decimal
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "")      # remove thousands dots
            s = s.replace(",", ".")     # convert decimal comma
        else:
            s = s.replace(",", "")      # remove thousands commas
        try:
            return float(s)
        except ValueError:
            return None

    # Case 2: only comma present -> treat comma as decimal
    if "," in s:
        s = s.replace(",", ".")
        try:
            return float(s)
        except ValueError:
            return None

    # Case 3: only dot or pure digits
    try:
        return float(s)
    except ValueError:
        return None


# ----------------------------- core ----------------------------- #
CSV_PATH = locate_csv()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--country", required=True, help="Country name (case-insensitive)")
    parser.add_argument("--year", required=True, type=int, help="Target year (e.g. 2024)")
    parser.add_argument(
        "--category_label",
        dest="category_labels",
        action="append",
        help="Optional category label or key to filter (can be repeated or comma separated)",
    )
    return parser.parse_args()


def load_filtered_rows(country: str, year: int) -> List[Tuple[float, Dict[str, Any]]]:
    """
    Returns rows matching country/year as tuples:
      (ratio, row_dict_with_numeric_fields)
    Drops rows where price or cost is missing / <= 0.
    """
    country_norm = normalize(country)
    rows: List[Tuple[float, Dict[str, Any]]] = []

    delimiter = sniff_delimiter(CSV_PATH)

    with CSV_PATH.open("r", encoding="utf-8", newline="") as csvfile:
        reader = csv.DictReader(csvfile, delimiter=delimiter)
        for row in reader:
            # year filter
            try:
                row_year = int(str(row.get("year", "")).strip())
            except ValueError:
                continue
            if row_year != year:
                continue

            # country filter
            if country_norm and normalize(row.get("country")) != country_norm:
                continue

            price = to_float_mixed(row.get("price_eur_tonne"))
            cost = to_float_mixed(row.get("cost_eur_tonne"))
            if price is None or cost is None or cost <= 0:
                continue

            ratio = price / cost

            # carry numeric fields back for transparency
            row_out = dict(row)
            row_out["_price_num"] = price
            row_out["_cost_num"] = cost
            row_out["_ratio"] = ratio

            rows.append((ratio, row_out))

    return rows


def find_best_for_category(
    rows: List[Tuple[float, Dict[str, Any]]],
    category_norm: Optional[str],
) -> Optional[Dict[str, Any]]:
    """
    Pick max ratio; if category_norm is provided, filter by either category_label or category_key.
    """
    best_row: Optional[Dict[str, Any]] = None
    best_ratio: Optional[float] = None

    for ratio, row in rows:
        if category_norm:
            labels = {
                normalize(row.get("category_label")),
                normalize(row.get("category_key")),
            }
            if category_norm not in labels:
                continue

        if best_ratio is None or ratio > best_ratio:
            best_ratio = ratio
            best_row = row

    return best_row


def main() -> None:
    args = parse_args()
    categories = parse_category_inputs(args.category_labels)
    rows = load_filtered_rows(args.country, args.year)

    query_categories: List[Optional[str]] = categories if categories else [None]

    results = []
    for category in query_categories:
        normalized = normalize(category) if category is not None else None
        record = find_best_for_category(rows, normalized)
        results.append(
            {
                "requested_category": category,
                "found": record is not None,
                "record": record,  # includes _ratio, _price_num, _cost_num
            }
        )

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
