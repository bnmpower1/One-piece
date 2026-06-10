from unittest.mock import patch

MOCK_PRICES = {"eBay": 2480.00}


def test_price_lookup_by_card_number(client):
    with patch("services.card_service.fetch_ebay_prices", return_value=MOCK_PRICES):
        response = client.get("/cards/price?q=OP06-118")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["data"]["card_name"] == "Roronoa Zoro"
    assert body["data"]["card_number"] == "OP06-118"
    assert body["data"]["set"] == "OP-06"
    assert body["data"]["currency"] == "USD"
    assert body["data"]["prices"] == MOCK_PRICES


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


def test_price_lookup_falls_back_to_sheet_when_ebay_fails(client):
    with patch("services.card_service.fetch_ebay_prices", side_effect=Exception("API down")):
        response = client.get("/cards/price?q=OP06-118")
    body = response.json()
    assert body["status"] == "success"
    assert "TCGPlayer_Market" in body["data"]["prices"] or "TCGPlayer_Low" in body["data"]["prices"]


def test_price_lookup_unavailable_when_ebay_and_sheet_both_fail(client):
    with patch("services.card_service.fetch_ebay_prices", return_value=None), \
         patch("services.card_service._sheet_prices", return_value=None):
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


def test_rarity_alias_super_rare(client):
    with patch("services.card_service.fetch_ebay_prices", return_value=MOCK_PRICES):
        response = client.get("/cards/price?q=zoro+super+rare")
    body = response.json()
    assert body["status"] == "success"
    assert body["data"]["rarity"] == "SR"


def test_rarity_alias_secret_rare(client):
    with patch("services.card_service.fetch_ebay_prices", return_value=MOCK_PRICES):
        response = client.get("/cards/price?q=boa+secret+rare")
    body = response.json()
    assert body["status"] == "success"
    assert body["data"]["rarity"] == "SEC"


def test_price_response_includes_variant(client):
    with patch("services.card_service.fetch_ebay_prices", return_value=MOCK_PRICES):
        response = client.get("/cards/price?q=OP06-118")
    body = response.json()
    assert "variant" in body["data"]
    assert body["data"]["variant"] == "Manga Alternate Art"
