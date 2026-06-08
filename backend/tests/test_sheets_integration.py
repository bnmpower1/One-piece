"""
Integration tests against the live Google Sheet.

Run with:
    cd backend
    python3 -m pytest tests/test_sheets_integration.py -v

These make real API calls to Google Sheets and require the service account
file to be present. They are excluded from the default test run.
"""
import os
import time

import pytest

pytestmark = pytest.mark.integration

_SERVICE_ACCOUNT = os.path.join(os.path.dirname(__file__), "..", "one_piece_service_account.json")
_VALID_RARITIES = {"L", "C", "UC", "R", "SR", "SEC", "DON!!", "SP"}
_VALID_VARIANTS = {"Standard", "Parallel", "Manga Alternate Art"}
_VALID_CARD_TYPES = {"Leader", "Character", "Event", "Stage", "DON!!"}


@pytest.fixture(scope="module")
def real_cards():
    if not os.path.exists(_SERVICE_ACCOUNT):
        pytest.skip("Service account file not found — cannot run integration tests")
    from services.sheets_service import _load_from_sheet
    return _load_from_sheet()


# ---------------------------------------------------------------------------
# Sheet connectivity and row count
# ---------------------------------------------------------------------------

def test_sheet_loads_cards(real_cards):
    assert len(real_cards) > 0, "Sheet returned no cards"


def test_card_count_is_reasonable(real_cards):
    # Sanity check: sheet should have at least 10 cards
    assert len(real_cards) >= 10, f"Suspiciously low card count: {len(real_cards)}"


# ---------------------------------------------------------------------------
# Required field presence
# ---------------------------------------------------------------------------

def test_all_cards_have_card_number(real_cards):
    empty = [c for c in real_cards if not c.card_number.strip()]
    assert not empty, f"Cards with empty card_number: {empty}"


def test_all_cards_have_name(real_cards):
    empty = [c for c in real_cards if not c.name.strip()]
    assert not empty, f"Cards with empty name: {[c.card_number for c in empty]}"


def test_all_cards_have_set_code(real_cards):
    empty = [c for c in real_cards if not c.set_code.strip()]
    assert not empty, f"Cards with empty set_code: {[c.card_number for c in empty]}"


def test_all_cards_have_card_type(real_cards):
    empty = [c for c in real_cards if not c.card_type.strip()]
    assert not empty, f"Cards with empty card_type: {[c.card_number for c in empty]}"


def test_all_cards_have_variant(real_cards):
    empty = [c for c in real_cards if not c.variant.strip()]
    assert not empty, f"Cards with empty variant: {[c.card_number for c in empty]}"


# ---------------------------------------------------------------------------
# Controlled vocabulary — catches typos in the sheet
# ---------------------------------------------------------------------------

def test_rarity_values_are_valid(real_cards):
    invalid = [(c.card_number, c.rarity) for c in real_cards if c.rarity not in _VALID_RARITIES]
    assert not invalid, f"Unexpected rarity values: {invalid}"


def test_variant_values_are_valid(real_cards):
    invalid = [(c.card_number, c.variant) for c in real_cards if c.variant not in _VALID_VARIANTS]
    assert not invalid, f"Unexpected variant values: {invalid}"


def test_card_type_values_are_valid(real_cards):
    invalid = [(c.card_number, c.card_type) for c in real_cards if c.card_type not in _VALID_CARD_TYPES]
    assert not invalid, f"Unexpected card_type values: {invalid}"


# ---------------------------------------------------------------------------
# Price field integrity
# ---------------------------------------------------------------------------

def test_price_fields_are_float_or_none(real_cards):
    bad = [
        (c.card_number, "price_market", c.price_market)
        for c in real_cards
        if c.price_market is not None and not isinstance(c.price_market, float)
    ] + [
        (c.card_number, "price_low", c.price_low)
        for c in real_cards
        if c.price_low is not None and not isinstance(c.price_low, float)
    ]
    assert not bad, f"Price fields with wrong type: {bad}"


def test_no_negative_prices(real_cards):
    bad = [
        (c.card_number, c.price_market, c.price_low)
        for c in real_cards
        if (c.price_market is not None and c.price_market < 0)
        or (c.price_low is not None and c.price_low < 0)
    ]
    assert not bad, f"Negative prices found: {bad}"


def test_price_low_not_greater_than_market(real_cards):
    bad = [
        (c.card_number, c.price_low, c.price_market)
        for c in real_cards
        if c.price_low is not None
        and c.price_market is not None
        and c.price_low > c.price_market
    ]
    assert not bad, f"price_low > price_market for: {bad}"


# ---------------------------------------------------------------------------
# Card number format — basic sanity (e.g. OP01-001)
# ---------------------------------------------------------------------------

def test_card_number_format(real_cards):
    import re
    # Standard format: OP01-001. DON!! cards use a different scheme (e.g. OP01-DON-MANGA-AA).
    standard = re.compile(r"^[A-Z]{2}\d{2}-\d{3}$")
    don = re.compile(r"^[A-Z]{2}\d{2}-DON")
    bad = [
        c.card_number for c in real_cards
        if not standard.match(c.card_number) and not don.match(c.card_number)
    ]
    assert not bad, f"Card numbers not matching any known format: {bad}"


# ---------------------------------------------------------------------------
# Caching — sheet must not be fetched twice within TTL
# ---------------------------------------------------------------------------

def test_cache_prevents_redundant_sheet_calls(monkeypatch):
    from services import sheets_service

    call_log = []
    real_load = sheets_service._load_from_sheet

    def instrumented_load():
        call_log.append(time.time())
        return real_load()

    # Reset cache so the first call is a real fetch
    sheets_service._cache["cards"] = None
    sheets_service._cache["expires_at"] = 0

    monkeypatch.setattr(sheets_service, "_load_from_sheet", instrumented_load)

    first = sheets_service.get_cards()
    second = sheets_service.get_cards()  # should hit cache

    assert len(call_log) == 1, f"Sheet was fetched {len(call_log)} times — cache not working"
    assert first is second, "Cache should return the exact same list object"

    # Cleanup: reset so subsequent tests reload fresh data
    sheets_service._cache["cards"] = None
    sheets_service._cache["expires_at"] = 0
