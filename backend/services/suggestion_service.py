import json
import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

from services.card_service import _sheet_prices, find_card
from services.ebay_service import fetch_ebay_prices
from services.sheets_service import CardRecord

load_dotenv()

_client: genai.Client | None = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY", ""))
    return _client

_PROMPT_TEMPLATE = """I'm a One Piece TCG collector trying to decide what to do with a card I own. Should I hold this card or sell it, and why?

Here's the card info:
- Card: {name} ({card_number})
- Set: {set_code}
- Rarity: {rarity}
- Type: {card_type} — Color: {color}
- Subtypes: {subtypes}
- Variant: {variant}
- Current average market price: ${avg_price:.2f} USD
- Price breakdown: {prices}

Give me a straight answer — hold or sell (or buy if it's a good deal) — and explain your reasoning in plain English like you're talking to a collector, not a robot.

Respond with a JSON object in exactly this format:
{{"suggestion": "buy" | "hold" | "sell", "reasoning": "<two to three sentence explanation in plain, conversational English>"}}"""


def _ask_gemini(card: CardRecord, prices: dict) -> dict:
    avg_price = sum(prices.values()) / len(prices)
    prompt = _PROMPT_TEMPLATE.format(
        name=card.name,
        card_number=card.card_number,
        set_code=card.set_code,
        rarity=card.rarity,
        card_type=card.card_type,
        color=card.color,
        subtypes=card.subtypes,
        variant=card.variant,
        avg_price=avg_price,
        prices=json.dumps(prices),
    )
    response = _get_client().models.generate_content(
        model="gemini-2.5-flash-lite",
        contents=prompt,
        config=types.GenerateContentConfig(response_mime_type="application/json"),
    )
    result = json.loads(response.text)
    if result.get("suggestion") not in ("buy", "hold", "sell"):
        raise ValueError(f"Unexpected suggestion value: {result.get('suggestion')}")
    return result


def get_market_suggestion(card_query: str) -> dict:
    status, matches = find_card(card_query)

    if status == "not_found":
        return {"status": "not_found", "message": "Card not found."}
    if status == "multiple_matches":
        return {
            "status": "multiple_matches",
            "data": [f"{c.card_number} {c.name}" for c in matches],
        }

    card = matches[0]

    try:
        prices = fetch_ebay_prices(card.card_number, card.name, card.variant)
    except Exception:
        prices = None

    if prices is None:
        prices = _sheet_prices(card)

    if prices is None:
        return {"status": "insufficient_data", "message": "Not enough market data."}

    try:
        gemini_result = _ask_gemini(card, prices)
    except Exception:
        return {"status": "insufficient_data", "message": "Could not generate suggestion."}

    if gemini_result.get("suggestion") not in ("buy", "hold", "sell"):
        return {"status": "insufficient_data", "message": "Could not generate suggestion."}

    avg_price = sum(prices.values()) / len(prices)
    return {
        "status": "success",
        "data": {
            "suggestion": gemini_result["suggestion"],
            "reasoning": gemini_result["reasoning"],
            "card_name": card.name,
            "card_number": card.card_number,
            "rarity": card.rarity,
            "image_url": card.image_url,
            "avg_price_usd": round(avg_price, 2),
        },
    }
