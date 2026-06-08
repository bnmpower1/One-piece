from services.ebay_service import fetch_ebay_prices
from services.sheets_service import CardRecord


def fetch_justtcg_price(card: CardRecord) -> dict[str, float] | None:
    return fetch_ebay_prices(card.card_number, card.name, card.variant)
