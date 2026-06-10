from unittest.mock import patch

MOCK_BUY = {"suggestion": "buy", "reasoning": "Strong card."}


# ── Functionality 1: Card Price Lookup ────────────────────────────────────────

def test_empty_query_returns_not_found(client):
    response = client.get("/cards/price?q=")
    assert response.json()["status"] == "not_found"


def test_whitespace_query_returns_not_found(client):
    response = client.get("/cards/price?q=   ")
    assert response.json()["status"] == "not_found"


def test_nonexistent_set_code_returns_not_found(client):
    response = client.get("/cards/price?q=OP-99")
    assert response.json()["status"] == "not_found"


def test_single_char_token_matches_exact_rarity_only(client):
    # "R" should not match "Roronoa Zoro" as a substring — only exact rarity field
    with patch("services.card_service.fetch_justtcg_price", return_value={"eBay": 100.0}):
        response = client.get("/cards/price?q=R")
    # no card in test data has rarity "R", so should be not_found
    assert response.json()["status"] == "not_found"


def test_rarity_alias_manga_rare(client):
    with patch("services.card_service.fetch_justtcg_price", return_value={"eBay": 100.0}):
        response = client.get("/cards/price?q=zoro+super+rare")
    body = response.json()
    assert body["status"] == "success"
    assert body["data"]["rarity"] == "SR"


def test_ebay_fails_falls_back_to_sheet_prices(client):
    with patch("services.card_service.fetch_justtcg_price", side_effect=Exception("eBay down")):
        response = client.get("/cards/price?q=OP06-118")
    body = response.json()
    assert body["status"] == "success"
    assert "TCGPlayer_Market" in body["data"]["prices"] or "TCGPlayer_Low" in body["data"]["prices"]


def test_both_price_sources_fail_returns_price_unavailable(client):
    with patch("services.card_service.fetch_justtcg_price", return_value=None), \
         patch("services.card_service._sheet_prices", return_value=None):
        response = client.get("/cards/price?q=OP06-118")
    assert response.json()["status"] == "price_unavailable"


def test_sec_rarity_card_found(client):
    with patch("services.card_service.fetch_justtcg_price", return_value={"eBay": 150.0}):
        response = client.get("/cards/price?q=secret+rare+boa")
    body = response.json()
    assert body["status"] == "success"
    assert body["data"]["rarity"] == "SEC"


def test_response_includes_image_url_field(client):
    with patch("services.card_service.fetch_justtcg_price", return_value={"eBay": 100.0}):
        response = client.get("/cards/price?q=OP06-118")
    assert "image_url" in response.json()["data"]


# ── Functionality 2: Buy / Hold / Sell Suggestion ─────────────────────────────

def test_gemini_returns_invalid_suggestion_value(client, reset_limiter):
    bad = {"suggestion": "maybe", "reasoning": "who knows"}
    with patch("services.suggestion_service._ask_gemini", return_value=bad):
        response = client.get("/cards/suggest?q=OP06-118")
    assert response.json()["status"] == "insufficient_data"


def test_gemini_returns_malformed_response(client, reset_limiter):
    with patch("services.suggestion_service._ask_gemini", side_effect=ValueError("bad JSON")):
        response = client.get("/cards/suggest?q=OP06-118")
    assert response.json()["status"] == "insufficient_data"


def test_suggestion_uses_sheet_prices_when_ebay_unavailable(client, reset_limiter):
    with patch("services.suggestion_service.fetch_justtcg_price", return_value=None), \
         patch("services.suggestion_service._ask_gemini", return_value=MOCK_BUY):
        response = client.get("/cards/suggest?q=OP06-118")
    # sheet prices exist for OP06-118 so suggestion should still succeed
    assert response.json()["status"] == "success"


def test_suggestion_response_includes_image_url(client, reset_limiter):
    with patch("services.suggestion_service._ask_gemini", return_value=MOCK_BUY):
        response = client.get("/cards/suggest?q=OP06-118")
    assert "image_url" in response.json()["data"]


def test_suggestion_empty_query_returns_not_found(client, reset_limiter):
    response = client.get("/cards/suggest?q=")
    assert response.json()["status"] == "not_found"


# ── Functionality 3: Card Image Proxy ─────────────────────────────────────────

def test_image_proxy_rejects_disallowed_host(client):
    response = client.get("/cards/image?url=https://evil.com/card.png")
    assert response.status_code == 400


def test_image_proxy_rejects_malformed_url(client):
    response = client.get("/cards/image?url=not-a-url")
    assert response.status_code == 400


def test_image_proxy_missing_url_param_returns_422(client):
    response = client.get("/cards/image")
    assert response.status_code == 422


def test_image_proxy_rejects_non_image_response(client):
    from unittest.mock import MagicMock
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.headers = {"content-type": "text/html"}
    mock_resp.content = b"<html>not an image</html>"
    with patch("routers.cards.httpx.get", return_value=mock_resp):
        response = client.get("/cards/image?url=https://en.onepiece-cardgame.com/card.html")
    assert response.status_code == 400


def test_image_proxy_returns_404_on_remote_failure(client):
    import httpx
    with patch("routers.cards.httpx.get", side_effect=Exception("connection error")):
        response = client.get("/cards/image?url=https://en.onepiece-cardgame.com/card.png")
    assert response.status_code == 404
