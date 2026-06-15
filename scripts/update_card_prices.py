#!/usr/bin/env python3
"""Refresh card sale prices in assets/data/cards.json from Scryfall."""

from __future__ import annotations

import argparse
import csv
import json
import time
import urllib.error
import urllib.request
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CARDS_PATH = REPO_ROOT / "assets" / "data" / "cards.json"
DEFAULT_SOURCE_CSV = REPO_ROOT / "data" / "tcgplayer-export.csv"
DEFAULT_LOG_PATH = REPO_ROOT / "logs" / "card-price-updates.log"
SCRYFALL_TCGPLAYER_URL = "https://api.scryfall.com/cards/tcgplayer/{product_id}"
USER_AGENT = "ebarragan-dev-card-price-updater/1.0"


def parse_price(value: Any) -> Decimal | None:
    if value is None:
        return None

    text = str(value).strip().replace("$", "").replace(",", "")
    if not text:
        return None

    try:
        price = Decimal(text)
    except InvalidOperation as exc:
        raise ValueError(f"Could not parse price: {value!r}") from exc

    return price if price > 0 else None


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


def load_cards(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as cards_file:
        cards = json.load(cards_file)

    if not isinstance(cards, list):
        raise ValueError(f"Expected {path} to contain a JSON array")

    for card in cards:
        if not isinstance(card, dict):
            raise ValueError(f"Expected every card in {path} to be a JSON object")

    return cards


def load_printing_by_product_id(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}

    printing_by_product_id: dict[str, str] = {}
    with path.open(newline="", encoding="utf-8-sig") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            product_id = (row.get("Product ID") or "").strip()
            printing = (row.get("Printing") or "").strip().lower()
            if product_id and printing:
                printing_by_product_id[product_id] = printing

    return printing_by_product_id


def fetch_scryfall_card(product_id: str, timeout: int) -> dict[str, Any]:
    request = urllib.request.Request(
        SCRYFALL_TCGPLAYER_URL.format(product_id=product_id),
        headers={
            "Accept": "application/json",
            "User-Agent": USER_AGENT,
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Scryfall returned HTTP {exc.code} for product {product_id}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Could not reach Scryfall for product {product_id}: {exc.reason}") from exc


def choose_market_price(scryfall_card: dict[str, Any], printing_hint: str) -> tuple[Decimal, str]:
    prices = scryfall_card.get("prices")
    if not isinstance(prices, dict):
        raise ValueError("Scryfall response did not include a prices object")

    if printing_hint == "foil":
        price_order = ("usd_foil", "usd", "usd_etched")
    elif printing_hint == "etched":
        price_order = ("usd_etched", "usd_foil", "usd")
    else:
        price_order = ("usd", "usd_foil", "usd_etched")

    for price_key in price_order:
        price = parse_price(prices.get(price_key))
        if price is not None:
            return price, price_key

    raise ValueError("Scryfall response did not include a usable USD price")


def update_prices(
    cards: list[dict[str, Any]],
    printing_by_product_id: dict[str, str],
    delay_seconds: float,
    timeout: int,
) -> tuple[int, int, int, list[str]]:
    updated_count = 0
    skipped_count = 0
    total_delta = 0
    messages: list[str] = []
    request_count = 0

    for index, card in enumerate(cards, start=1):
        product_id = str(card.get("product_id") or "").strip()
        name = str(card.get("name") or product_id or f"card {index}")

        if card.get("manual_sale_price") is True:
            messages.append(f"{name}: skipped manual sale price (${card.get('sale_price')})")
            skipped_count += 1
            continue

        if not product_id:
            messages.append(f"Skipped card {index}: missing product_id")
            skipped_count += 1
            continue

        if request_count > 0 and delay_seconds > 0:
            time.sleep(delay_seconds)

        scryfall_card = fetch_scryfall_card(product_id, timeout)
        request_count += 1
        printing_hint = printing_by_product_id.get(product_id, "")
        market_price, source_key = choose_market_price(scryfall_card, printing_hint)
        old_sale_price = int(card.get("sale_price") or 0)
        new_sale_price = calculate_sale_price(market_price)
        delta = new_sale_price - old_sale_price
        card["sale_price"] = new_sale_price
        updated_count += 1
        total_delta += delta

        messages.append(
            f"{name}: ${old_sale_price} -> ${new_sale_price} ({delta:+d}) "
            f"(Scryfall {source_key} ${market_price})"
        )

    return updated_count, skipped_count, total_delta, messages


def write_cards(path: Path, cards: list[dict[str, Any]]) -> None:
    cards.sort(key=lambda card: (-int(card.get("sale_price") or 0), str(card.get("name") or "").lower()))
    with path.open("w", encoding="utf-8") as cards_file:
        json.dump(cards, cards_file, indent=2)
        cards_file.write("\n")


def append_log(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as log_file:
        for line in lines:
            log_file.write(f"{line}\n")
        log_file.write("\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--cards",
        type=Path,
        default=DEFAULT_CARDS_PATH,
        help=f"Path to cards JSON. Defaults to {DEFAULT_CARDS_PATH}",
    )
    parser.add_argument(
        "--source-csv",
        type=Path,
        default=DEFAULT_SOURCE_CSV,
        help="Optional TCGplayer CSV used only to infer Normal/Foil/Etched printing.",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.1,
        help="Seconds to wait between Scryfall requests. Defaults to 0.1.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="Network timeout per Scryfall request in seconds. Defaults to 30.",
    )
    parser.add_argument(
        "--log",
        type=Path,
        default=DEFAULT_LOG_PATH,
        help=f"Append run output to this log file. Defaults to {DEFAULT_LOG_PATH}",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print price changes without writing cards.json.",
    )
    args = parser.parse_args()

    cards = load_cards(args.cards)
    printing_by_product_id = load_printing_by_product_id(args.source_csv)
    updated_count, skipped_count, total_delta, messages = update_prices(
        cards=cards,
        printing_by_product_id=printing_by_product_id,
        delay_seconds=args.delay,
        timeout=args.timeout,
    )
    summary = (
        f"Total sale price change: {total_delta:+d} "
        f"across {updated_count} updated cards; {skipped_count} skipped."
    )

    run_lines = [
        f"=== {datetime.now().astimezone().isoformat(timespec='seconds')} "
        f"{'DRY RUN' if args.dry_run else 'UPDATE'} ===",
        *messages,
        summary,
    ]

    for line in run_lines:
        print(line)

    if args.dry_run:
        final_message = f"Dry run complete. Checked {updated_count} cards; no file was changed."
        print(final_message)
        append_log(args.log, [*run_lines, final_message])
        return

    write_cards(args.cards, cards)
    final_message = f"Updated {updated_count} cards in {args.cards}"
    print(final_message)
    append_log(args.log, [*run_lines, final_message])


if __name__ == "__main__":
    main()
