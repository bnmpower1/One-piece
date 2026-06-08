"""
Quick live output check — calls real Google Sheets + real Gemini API.
Shows you exactly what data is being pulled and what Gemini says.

Usage:
    cd backend
    python test_live_output.py [card_query]

Examples:
    python test_live_output.py OP01-001
    python test_live_output.py Zoro
    python test_live_output.py OP-01
"""
import json
import sys

sys.path.insert(0, ".")

from services.sheets_service import get_cards
from services.card_service import find_card, _sheet_prices
from services.justtcg_service import fetch_justtcg_price
from services.suggestion_service import _ask_gemini


def _divider(title=""):
    width = 60
    if title:
        print(f"\n{'─' * 4} {title} {'─' * (width - len(title) - 6)}")
    else:
        print("─" * width)


def run(query: str):
    _divider("STEP 1: Loading cards from Google Sheet")
    all_cards = get_cards()
    print(f"  Loaded {len(all_cards)} cards from sheet (cached after first load)")

    _divider("STEP 2: Searching for card")
    print(f"  Query: {query!r}")
    status, matches = find_card(query)
    print(f"  Status: {status}")

    if status == "not_found":
        print("  No card matched that query.")
        return

    if status == "multiple_matches":
        print(f"  Multiple cards matched ({len(matches)}):")
        for c in matches:
            print(f"    • {c.card_number}  {c.name}  [{c.rarity}] [{c.variant}]")
        print("\n  Tip: search by card number (e.g. OP01-001) to get a single result.")
        return

    card = matches[0]
    _divider("STEP 3: Card data from sheet")
    print(f"  Name:      {card.name}")
    print(f"  Number:    {card.card_number}")
    print(f"  Set:       {card.set_code} — {card.set_name}")
    print(f"  Rarity:    {card.rarity}")
    print(f"  Type:      {card.card_type}")
    print(f"  Color:     {card.color}")
    print(f"  Subtypes:  {card.subtypes}")
    print(f"  Variant:   {card.variant}")
    print(f"  Sheet price (market): {card.price_market}")
    print(f"  Sheet price (low):    {card.price_low}")

    _divider("STEP 4: Fetching eBay prices")
    try:
        justtcg_prices = fetch_justtcg_price(card)
        if justtcg_prices:
            print(f"  eBay live prices: {justtcg_prices}")
        else:
            print("  eBay returned no results — will use sheet prices as fallback")
    except Exception as e:
        justtcg_prices = None
        print(f"  eBay unavailable ({e.__class__.__name__}: {e}) — will use sheet prices as fallback")

    prices = justtcg_prices or _sheet_prices(card)

    if prices is None:
        print("\n  No price data available from either source — cannot generate suggestion.")
        return

    print(f"\n  Using prices: {prices}")
    avg = sum(prices.values()) / len(prices)
    print(f"  Average: ${avg:.2f}")

    _divider("STEP 5: Asking Gemini")
    print("  Sending prompt...\n")
    try:
        result = _ask_gemini(card, prices)
    except Exception as e:
        print(f"  Gemini error: {e}")
        return

    _divider("RESULT")
    print(f"  Suggestion:  {result['suggestion'].upper()}")
    print(f"  Reasoning:   {result['reasoning']}")
    _divider()


if __name__ == "__main__":
    query = sys.argv[1] if len(sys.argv) > 1 else "OP01-001"
    run(query)
