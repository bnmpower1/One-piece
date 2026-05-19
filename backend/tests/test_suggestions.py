from unittest.mock import patch


MOCK_BUY = {"suggestion": "buy", "reasoning": "High rarity with stable price — good entry point."}
MOCK_SELL = {"suggestion": "sell", "reasoning": "Rising price on a strong card — take profits."}
MOCK_HOLD = {"suggestion": "hold", "reasoning": "No clear signal right now."}


def test_suggestion_returns_valid_action(client):
    with patch("services.suggestion_service._ask_gemini", return_value=MOCK_BUY):
        response = client.get("/cards/suggest?q=OP06-118")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["data"]["suggestion"] in ("buy", "hold", "sell")
    assert "reasoning" in body["data"]


def test_suggestion_zoro_buy(client):
    with patch("services.suggestion_service._ask_gemini", return_value=MOCK_BUY):
        response = client.get("/cards/suggest?q=OP06-118")
    body = response.json()
    assert body["status"] == "success"
    assert body["data"]["suggestion"] == "buy"
    assert body["data"]["card_name"] == "Roronoa Zoro"
    assert body["data"]["reasoning"] == MOCK_BUY["reasoning"]


def test_suggestion_luffy_sell(client):
    with patch("services.suggestion_service._ask_gemini", return_value=MOCK_SELL):
        response = client.get("/cards/suggest?q=Luffy")
    body = response.json()
    assert body["status"] == "success"
    assert body["data"]["suggestion"] == "sell"
    assert body["data"]["card_name"] == "Monkey D. Luffy"


def test_suggestion_nami_hold(client):
    with patch("services.suggestion_service._ask_gemini", return_value=MOCK_HOLD):
        response = client.get("/cards/suggest?q=Nami")
    body = response.json()
    assert body["status"] == "success"
    assert body["data"]["suggestion"] == "hold"
    assert body["data"]["price_trend"] == "down"


def test_suggestion_includes_price_info(client):
    with patch("services.suggestion_service._ask_gemini", return_value=MOCK_BUY):
        response = client.get("/cards/suggest?q=OP06-118")
    body = response.json()
    assert body["status"] == "success"
    assert "avg_price_usd" in body["data"]
    assert body["data"]["avg_price_usd"] == 2475.00


def test_suggestion_gemini_failure_returns_insufficient_data(client):
    with patch("services.suggestion_service._ask_gemini", side_effect=Exception("API error")):
        response = client.get("/cards/suggest?q=OP06-118")
    body = response.json()
    assert body["status"] == "insufficient_data"
    assert "message" in body


def test_suggestion_not_found(client):
    response = client.get("/cards/suggest?q=Buggy the Clown")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "not_found"
    assert "message" in body


def test_suggestion_multiple_matches(client):
    response = client.get("/cards/suggest?q=OP-01")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "multiple_matches"
    assert isinstance(body["data"], list)


def test_rate_limit_exceeded(client, reset_limiter):
    from limiter import GEMINI_RATE_LIMIT
    limit = int(GEMINI_RATE_LIMIT.split("/")[0])

    with patch("services.suggestion_service._ask_gemini", return_value=MOCK_BUY):
        for _ in range(limit):
            r = client.get("/cards/suggest?q=OP06-118")
            assert r.status_code == 200

        r = client.get("/cards/suggest?q=OP06-118")
        assert r.status_code == 429
