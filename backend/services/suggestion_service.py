import json
import os

from dotenv import load_dotenv
from google import genai
from google.genai import types
from sqlalchemy.orm import Session

from services.card_service import _db_prices, find_card
from services.ebay_service import fetch_ebay_prices

load_dotenv()

_client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY", ""))

_PROMPT_TEMPLATE = """You are a One Piece TCG card market advisor. Based on the card data below, give a buy, hold, or sell suggestion with reasoning.

Card: {name} ({card_number})
Set: {set_code}
Rarity: {rarity}
Character Popularity: {character_popularity}
Story Relevance: {story_relevance}
Price Trend: {price_trend}
Average Market Price: ${avg_price:.2f} USD
Platform Prices: {prices}

Respond with a JSON object in exactly this format:
{{"suggestion": "buy" | "hold" | "sell", "reasoning": "<one or two sentence explanation>"}}"""


def _ask_gemini(card, prices: dict) -> dict:
    avg_price = sum(prices.values()) / len(prices)
    prompt = _PROMPT_TEMPLATE.format(
        name=card.name,
        card_number=card.card_number,
        set_code=card.set_code,
        rarity=card.rarity,
        character_popularity=card.character_popularity,
        story_relevance=card.story_relevance,
        price_trend=card.price_trend,
        avg_price=avg_price,
        prices=json.dumps(prices),
    )
    response = _client.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents=prompt,
        config=types.GenerateContentConfig(response_mime_type="application/json"),
    )
    result = json.loads(response.text)
    if result.get("suggestion") not in ("buy", "hold", "sell"):
        raise ValueError(f"Unexpected suggestion value: {result.get('suggestion')}")
    return result


def get_market_suggestion(db: Session, card_query: str) -> dict:
    status, matches = find_card(db, card_query)

    if status == "not_found":
        return {"status": "not_found", "message": "Card not found."}

    if status == "multiple_matches":
        return {
            "status": "multiple_matches",
            "data": [f"{c.card_number} {c.name}" for c in matches],
        }

    card = matches[0]

    try:
        prices = fetch_ebay_prices(card.card_number, card.name)
    except Exception:
        prices = None

    if prices is None:
        prices = _db_prices(db, card.id)

    if prices is None:
        return {"status": "insufficient_data", "message": "Not enough market data."}

    try:
        gemini_result = _ask_gemini(card, prices)
    except Exception:
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
            "price_trend": card.price_trend,
            "avg_price_usd": round(avg_price, 2),
        },
    }
