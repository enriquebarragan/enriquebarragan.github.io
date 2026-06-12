#!/usr/bin/env python3
"""Convert a TCGplayer inventory export into browser-friendly JSON."""

from __future__ import annotations

import argparse
import csv
import json
import math
from decimal import Decimal, InvalidOperation
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = REPO_ROOT / "data" / "tcgplayer-export.csv"
DEFAULT_OUTPUT = REPO_ROOT / "assets" / "data" / "cards.json"


def clean_text(value: str | None) -> str:
    return (value or "").strip()


def parse_price(value: str | None) -> float:
    text = clean_text(value).replace("$", "").replace(",", "")
    if not text:
        return 0.0

    try:
        return float(Decimal(text))
    except InvalidOperation as exc:
        raise ValueError(f"Could not parse price: {value!r}") from exc


def parse_quantity(row: dict[str, str]) -> int:
    quantity = clean_text(row.get("Total Quantity")) or clean_text(row.get("Add to Quantity"))
    if not quantity:
        return 0

    return int(Decimal(quantity))


def convert_row(row: dict[str, str]) -> dict[str, object]:
    product_id = clean_text(row.get("Product ID"))
    market_price = parse_price(row.get("TCG Market Price"))

    return {
        "product_id": product_id,
        "tcgplayer_url": f"https://www.tcgplayer.com/product/{product_id}?Language=English",
        "name": clean_text(row.get("Product Name")),
        "set_name": clean_text(row.get("Set Name")),
        "market_price": market_price,
        "quantity": parse_quantity(row),
        "photo_url": clean_text(row.get("Photo URL")),
        "sold": False,
        "sale_price": math.floor(market_price * 0.8),
    }


def convert_csv(input_path: Path, output_path: Path) -> int:
    with input_path.open(newline="", encoding="utf-8-sig") as csv_file:
        reader = csv.DictReader(csv_file)
        cards = [convert_row(row) for row in reader]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as json_file:
        json.dump(cards, json_file, indent=2)
        json_file.write("\n")

    return len(cards)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "input",
        nargs="?",
        type=Path,
        default=DEFAULT_INPUT,
        help=f"CSV export path. Defaults to {DEFAULT_INPUT}",
    )
    parser.add_argument(
        "output",
        nargs="?",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"JSON output path. Defaults to {DEFAULT_OUTPUT}",
    )
    args = parser.parse_args()

    count = convert_csv(args.input, args.output)
    print(f"Wrote {count} cards to {args.output}")


if __name__ == "__main__":
    main()
