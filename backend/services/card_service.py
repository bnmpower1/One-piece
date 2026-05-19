from sqlalchemy.orm import Session

from models import Card, CardPrice
from services.ebay_service import fetch_ebay_prices


def find_card(db: Session, card_query: str):
    query = card_query.strip().lower()

    # Try exact card number match first (e.g. "OP06-118")
    match = db.query(Card).filter(Card.card_number.ilike(query)).first()
    if match:
        return "success", [match]

    # Try matching by name, character, or set code
    matches = db.query(Card).filter(
        Card.name.ilike(f"%{query}%")
        | Card.character.ilike(f"%{query}%")
        | Card.set_code.ilike(f"%{query}%")
    ).all()

    if not matches:
        return "not_found", []
    if len(matches) > 1:
        return "multiple_matches", matches
    return "success", matches


def _db_prices(db: Session, card_id: str) -> dict[str, float] | None:
    rows = db.query(CardPrice).filter(CardPrice.card_id == card_id).all()
    if not rows:
        return None
    return {p.platform: p.price_usd for p in rows}


def get_card_price(db: Session, card_query: str) -> dict:
    status, matches = find_card(db, card_query)

    if status == "not_found":
        return {"status": "not_found", "message": "Card not found."}

    if status == "multiple_matches":
        return {
            "status": "multiple_matches",
            "data": [f"{c.card_number} {c.name}" for c in matches],
        }

    card = matches[0]

    # Live eBay prices, fall back to seeded DB prices if unavailable
    try:
        prices = fetch_ebay_prices(card.card_number, card.name)
    except Exception:
        prices = None

    if prices is None:
        prices = _db_prices(db, card.id)

    if prices is None:
        return {"status": "price_unavailable", "message": "Price unavailable."}

    return {
        "status": "success",
        "data": {
            "card_name": card.name,
            "card_number": card.card_number,
            "set": card.set_code,
            "rarity": card.rarity,
            "prices": prices,
            "currency": "USD",
        },
    }
