from services.sheets_service import CardRecord, get_cards
from services.justtcg_service import fetch_justtcg_price

# Natural-language phrases → sheet field values (applied before tokenising)
_ALIASES: dict[str, str] = {
    "secret rare": "sec",
    "super rare": "sr",
    "alternate art": "alternate art",
    "alt art": "alternate art",
    "manga alt": "manga alternate art",
}


def _prefer_standard(cards: list[CardRecord]) -> list[CardRecord]:
    seen: dict[str, CardRecord] = {}
    for c in cards:
        if c.card_number not in seen or c.variant == "Standard":
            seen[c.card_number] = c
    return list(seen.values())


def find_card(query: str) -> tuple[str, list[CardRecord]]:
    q = query.strip().lower()
    for phrase, code in _ALIASES.items():
        q = q.replace(phrase, code)
    tokens = q.split()
    all_cards = get_cards()

    exact = [c for c in all_cards if c.card_number.lower() == q]
    if exact:
        return "success", [_prefer_standard(exact)[0]]

    def _matches(c: CardRecord) -> bool:
        fields = (c.name, c.set_code, c.subtypes, c.variant, c.color, c.rarity, c.card_type)
        field_values = [f.lower() for f in fields]
        combined = " ".join(field_values)
        # Single phrase: substring match across any field
        if any(q in f for f in field_values):
            return True
        # Multi-word query: every token must appear somewhere in the card's fields
        if len(tokens) > 1:
            def _token_matches(t: str) -> bool:
                # Single-char tokens (e.g. rarity "L") must equal a whole field — not a substring
                if len(t) == 1:
                    return t in field_values
                return t in combined
            return all(_token_matches(t) for t in tokens)
        return False

    matches = [c for c in all_cards if _matches(c)]
    if not matches:
        return "not_found", []

    deduped = _prefer_standard(matches)
    if len(deduped) > 1:
        return "multiple_matches", deduped
    return "success", deduped


def _sheet_prices(card: CardRecord) -> dict[str, float] | None:
    prices = {}
    if card.price_market is not None:
        prices["TCGPlayer_Market"] = card.price_market
    if card.price_low is not None:
        prices["TCGPlayer_Low"] = card.price_low
    return prices or None


def get_card_price(query: str) -> dict:
    status, matches = find_card(query)

    if status == "not_found":
        return {"status": "not_found", "message": "Card not found."}
    if status == "multiple_matches":
        return {
            "status": "multiple_matches",
            "data": [f"{c.card_number} {c.name}" for c in matches],
        }

    card = matches[0]

    try:
        prices = fetch_justtcg_price(card)
    except Exception:
        prices = None

    if prices is None:
        prices = _sheet_prices(card)

    if prices is None:
        return {"status": "price_unavailable", "message": "Price unavailable."}

    return {
        "status": "success",
        "data": {
            "card_name": card.name,
            "card_number": card.card_number,
            "set": card.set_code,
            "rarity": card.rarity,
            "variant": card.variant,
            "image_url": card.image_url,
            "prices": prices,
            "currency": "USD",
        },
    }
