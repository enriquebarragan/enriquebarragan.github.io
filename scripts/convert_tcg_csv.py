#!/usr/bin/env python3
"""Convert a TCGplayer inventory export into browser-friendly JSON."""

from __future__ import annotations

import argparse
import csv
import json
from decimal import Decimal, InvalidOperation
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = REPO_ROOT / "data" / "tcgplayer-export.csv"
DEFAULT_OUTPUT = REPO_ROOT / "assets" / "data" / "cards.json"

PICTURES_URL_BY_PRODUCT_ID = {
    "6883": "/gaeas-cradle/",
}


def clean_text(value: str | None) -> str:
    return (value or "").strip()


def parse_price(value: str | None) -> Decimal:
    text = clean_text(value).replace("$", "").replace(",", "")
    if not text:
        return Decimal("0")

    try:
        return Decimal(text)
    except InvalidOperation as exc:
        raise ValueError(f"Could not parse price: {value!r}") from exc


def calculate_sale_price(market_price: Decimal) -> int:
    if market_price < Decimal("20"):
        multiplier = Decimal("0.70")
    elif market_price <= Decimal("40"):
        multiplier = Decimal("0.75")
    elif market_price <= Decimal("65"):
        multiplier = Decimal("0.80")
    else:
        multiplier = Decimal("0.90")

    return int(market_price * multiplier)


def convert_row(row: dict[str, str]) -> dict[str, object]:
    product_id = clean_text(row.get("Product ID"))
    market_price = parse_price(row.get("TCG Market Price"))

    return {
        "product_id": product_id,
        "tcgplayer_url": f"https://www.tcgplayer.com/product/{product_id}?Language=English",
        "name": clean_text(row.get("Product Name")),
        "set_name": clean_text(row.get("Set Name")),
        "photo_url": clean_text(row.get("Photo URL")),
        "pictures_url": PICTURES_URL_BY_PRODUCT_ID.get(product_id, ""),
        "sold": False,
        "sale_price": calculate_sale_price(market_price),
    }


def convert_csv(input_path: Path, output_path: Path) -> int:
    with input_path.open(newline="", encoding="utf-8-sig") as csv_file:
        reader = csv.DictReader(csv_file)
        cards = [convert_row(row) for row in reader]
        cards.sort(key=lambda card: (-int(card["sale_price"]), str(card["name"]).lower()))

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
