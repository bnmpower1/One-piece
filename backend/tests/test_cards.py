from unittest.mock import patch

MOCK_EBAY_PRICES = {"eBay": 2480.00}


def test_price_lookup_by_card_number(client):
    with patch("services.card_service.fetch_ebay_prices", return_value=MOCK_EBAY_PRICES):
        response = client.get("/cards/price?q=OP06-118")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["data"]["card_name"] == "Roronoa Zoro"
    assert body["data"]["card_number"] == "OP06-118"
    assert body["data"]["set"] == "OP-06"
    assert body["data"]["currency"] == "USD"
    assert body["data"]["prices"] == MOCK_EBAY_PRICES


def test_price_lookup_by_character_name(client):
    with patch("services.card_service.fetch_ebay_prices", return_value={"eBay": 1775.00}):
        response = client.get("/cards/price?q=Luffy")
    body = response.json()
    assert body["status"] == "success"
    assert body["data"]["card_name"] == "Monkey D. Luffy"
    assert body["data"]["prices"]["eBay"] == 1775.00


def test_price_lookup_by_partial_name(client):
    with patch("services.card_service.fetch_ebay_prices", return_value={"eBay": 335.00}):
        response = client.get("/cards/price?q=Nami")
    body = response.json()
    assert body["status"] == "success"
    assert body["data"]["card_number"] == "OP01-082"


def test_price_lookup_falls_back_to_db_when_ebay_fails(client):
    with patch("services.card_service.fetch_ebay_prices", side_effect=Exception("eBay down")):
        response = client.get("/cards/price?q=OP06-118")
    body = response.json()
    # Falls back to seeded DB prices
    assert body["status"] == "success"
    assert "eBay" in body["data"]["prices"] or "TCGPlayer" in body["data"]["prices"]


def test_price_lookup_unavailable_when_ebay_and_db_both_fail(client):
    with patch("services.card_service.fetch_ebay_prices", return_value=None), \
         patch("services.card_service._db_prices", return_value=None):
        response = client.get("/cards/price?q=OP06-118")
    body = response.json()
    assert body["status"] == "price_unavailable"


def test_price_lookup_not_found(client):
    response = client.get("/cards/price?q=Buggy the Clown")
    body = response.json()
    assert body["status"] == "not_found"
    assert "message" in body


def test_price_lookup_multiple_matches(client):
    response = client.get("/cards/price?q=OP-01")
    body = response.json()
    assert body["status"] == "multiple_matches"
    assert isinstance(body["data"], list)
    assert len(body["data"]) > 1


def test_price_lookup_correct_rarity(client):
    with patch("services.card_service.fetch_ebay_prices", return_value=MOCK_EBAY_PRICES):
        response = client.get("/cards/price?q=OP06-118")
    body = response.json()
    assert body["data"]["rarity"] == "manga_rare"
