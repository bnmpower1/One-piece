import base64
import os
import time

import httpx
from dotenv import load_dotenv

load_dotenv()

_TOKEN_URL = "https://api.ebay.com/identity/v1/oauth2/token"
_SEARCH_URL = "https://api.ebay.com/buy/browse/v1/item_summary/search"
_SCOPE = "https://api.ebay.com/oauth/api_scope"

_token_cache: dict = {"token": None, "expires_at": 0}


def _get_token() -> str:
    if _token_cache["token"] and time.time() < _token_cache["expires_at"]:
        return _token_cache["token"]

    client_id = os.getenv("EBAY_CLIENT_ID", "")
    client_secret = os.getenv("EBAY_CLIENT_SECRET", "")
    credentials = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()

    response = httpx.post(
        _TOKEN_URL,
        headers={
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data={"grant_type": "client_credentials", "scope": _SCOPE},
    )
    response.raise_for_status()
    data = response.json()

    _token_cache["token"] = data["access_token"]
    _token_cache["expires_at"] = time.time() + data["expires_in"] - 60
    return _token_cache["token"]


def fetch_ebay_prices(card_number: str, card_name: str) -> dict[str, float] | None:
    token = _get_token()
    query = f"{card_number} One Piece card"

    response = httpx.get(
        _SEARCH_URL,
        headers={"Authorization": f"Bearer {token}"},
        params={
            "q": query,
            "limit": 10,
            "filter": "buyingOptions:{FIXED_PRICE},currency:USD",
        },
    )
    response.raise_for_status()

    items = response.json().get("itemSummaries", [])
    prices = [
        float(item["price"]["value"])
        for item in items
        if "price" in item and item["price"].get("currency") == "USD"
    ]

    if not prices:
        return None

    avg = round(sum(prices) / len(prices), 2)
    return {"eBay": avg}
