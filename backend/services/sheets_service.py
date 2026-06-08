import os
import time
from dataclasses import dataclass

import gspread
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials

load_dotenv()

_SPREADSHEET_ID = os.getenv("SHEETS_ID", "1EII-FStGHhRy0E8CQSm6AM-d0U993l8B9z8TWNxH7Qc")
_SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_SERVICE_ACCOUNT", "one_piece_service_account.json")
_CACHE_TTL = 600  # 10 minutes

_SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

_cache: dict = {"cards": None, "expires_at": 0}


@dataclass
class CardRecord:
    card_number: str
    name: str
    set_code: str
    set_name: str
    rarity: str
    card_type: str
    variant: str
    color: str
    subtypes: str
    price_market: float | None
    price_low: float | None


def _to_float(val) -> float | None:
    try:
        return float(val) if val != "" else None
    except (ValueError, TypeError):
        return None


def _load_from_sheet() -> list[CardRecord]:
    creds = Credentials.from_service_account_file(_SERVICE_ACCOUNT_FILE, scopes=_SCOPES)
    gc = gspread.authorize(creds)
    ws = gc.open_by_key(_SPREADSHEET_ID).sheet1
    return [
        CardRecord(
            card_number=r["card_id"],
            name=r["card_name"],
            set_code=r["set_code"],
            set_name=r["set_name"],
            rarity=r["rarity"],
            card_type=r["card_type"],
            variant=r["variant"],
            color=r["color"],
            subtypes=r["subtypes"],
            price_market=_to_float(r.get("price_market_nm")),
            price_low=_to_float(r.get("price_low_nm")),
        )
        for r in ws.get_all_records()
    ]


def get_cards() -> list[CardRecord]:
    now = time.time()
    if _cache["cards"] is not None and now < _cache["expires_at"]:
        return _cache["cards"]
    _cache["cards"] = _load_from_sheet()
    _cache["expires_at"] = now + _CACHE_TTL
    return _cache["cards"]
