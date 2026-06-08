import os
import sys
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from main import app
from services.sheets_service import CardRecord

_TEST_CARDS = [
    CardRecord(
        card_number="OP06-118",
        name="Roronoa Zoro",
        set_code="OP-06",
        set_name="Wings of the Captain",
        rarity="SR",
        card_type="Character",
        variant="Manga Alternate Art",
        color="Green",
        subtypes="Supernovas/Straw Hat Crew",
        price_market=2500.00,
        price_low=2450.00,
    ),
    CardRecord(
        card_number="OP01-060",
        name="Monkey D. Luffy",
        set_code="OP-01",
        set_name="Romance Dawn",
        rarity="SR",
        card_type="Character",
        variant="Manga Alternate Art",
        color="Red",
        subtypes="Supernovas/Straw Hat Crew",
        price_market=1800.00,
        price_low=1750.00,
    ),
    CardRecord(
        card_number="OP01-082",
        name="Nami",
        set_code="OP-01",
        set_name="Romance Dawn",
        rarity="SR",
        card_type="Character",
        variant="Manga Alternate Art",
        color="Green",
        subtypes="Straw Hat Crew",
        price_market=350.00,
        price_low=320.00,
    ),
    CardRecord(
        card_number="OP02-093",
        name="Boa Hancock",
        set_code="OP-02",
        set_name="Paramount War",
        rarity="SEC",
        card_type="Character",
        variant="Standard",
        color="Red",
        subtypes="Amazon Lily",
        price_market=150.00,
        price_low=140.00,
    ),
]


@pytest.fixture(scope="session", autouse=True)
def mock_sheets():
    with patch("services.card_service.get_cards", return_value=_TEST_CARDS):
        yield


@pytest.fixture
def client(mock_sheets):
    return TestClient(app)


@pytest.fixture
def reset_limiter():
    from limiter import limiter
    limiter._storage.reset()
    yield
    limiter._storage.reset()
