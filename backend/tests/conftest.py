import sys
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from database import Base, get_db
from main import app
from models import Card, CardPrice

TEST_DATABASE_URL = "sqlite:///./test_onepiece.db"

test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=test_engine)
    db = TestSessionLocal()

    cards = [
        Card(
            id="op06-118",
            name="Roronoa Zoro",
            set_code="OP-06",
            card_number="OP06-118",
            rarity="manga_rare",
            character="Roronoa Zoro",
            character_popularity="high",
            story_relevance="high",
            price_trend="stable",
        ),
        Card(
            id="op01-060",
            name="Monkey D. Luffy",
            set_code="OP-01",
            card_number="OP01-060",
            rarity="manga_rare",
            character="Monkey D. Luffy",
            character_popularity="high",
            story_relevance="high",
            price_trend="up",
        ),
        Card(
            id="op01-082",
            name="Nami",
            set_code="OP-01",
            card_number="OP01-082",
            rarity="manga_rare",
            character="Nami",
            character_popularity="medium",
            story_relevance="medium",
            price_trend="down",
        ),
        Card(
            id="op02-093",
            name="Boa Hancock",
            set_code="OP-02",
            card_number="OP02-093",
            rarity="secret_rare",
            character="Boa Hancock",
            character_popularity="high",
            story_relevance="high",
            price_trend="up",
        ),
    ]

    prices = [
        CardPrice(id="op06-118_tcgplayer", card_id="op06-118", platform="TCGPlayer", price_usd=2500.00),
        CardPrice(id="op06-118_ebay", card_id="op06-118", platform="eBay", price_usd=2450.00),
        CardPrice(id="op01-060_tcgplayer", card_id="op01-060", platform="TCGPlayer", price_usd=1800.00),
        CardPrice(id="op01-060_ebay", card_id="op01-060", platform="eBay", price_usd=1750.00),
        CardPrice(id="op01-082_tcgplayer", card_id="op01-082", platform="TCGPlayer", price_usd=350.00),
        CardPrice(id="op01-082_ebay", card_id="op01-082", platform="eBay", price_usd=320.00),
        CardPrice(id="op02-093_tcgplayer", card_id="op02-093", platform="TCGPlayer", price_usd=150.00),
        CardPrice(id="op02-093_ebay", card_id="op02-093", platform="eBay", price_usd=140.00),
    ]

    db.add_all(cards)
    db.add_all(prices)
    db.commit()
    db.close()

    yield

    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def reset_limiter():
    from limiter import limiter
    limiter._storage.reset()
    yield
    limiter._storage.reset()
