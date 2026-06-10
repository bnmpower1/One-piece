# One Piece Card Tracker

A One Piece TCG card price tracker with live eBay market data and AI-powered buy / hold / sell suggestions via Google Gemini.

---

## Demo Video

> **[Watch Demo Video](#)** ← _link to be added_

---

## Repository Structure

```
One-piece/
├── backend/                        # Python FastAPI backend
│   ├── main.py                     # App entry point, registers routers
│   ├── limiter.py                  # slowapi rate limiter config
│   ├── schemas.py                  # Pydantic response models
│   ├── requirements.txt
│   ├── .env.example                # Environment variable template
│   ├── test_live_output.py         # Manual end-to-end test script
│   ├── services/
│   │   ├── sheets_service.py       # Google Sheets data source + cache
│   │   ├── card_service.py         # Card search and price lookup
│   │   ├── ebay_service.py         # eBay Browse API (live prices)
│   │   ├── justtcg_service.py      # Price service adapter
│   │   └── suggestion_service.py   # Gemini buy/hold/sell suggestions
│   ├── routers/
│   │   ├── cards.py                # GET /cards/price, /cards/image
│   │   ├── suggestions.py          # GET /cards/suggest (rate limited)
│   │   └── ebay_notifications.py   # eBay account deletion webhook
│   └── tests/
│       ├── conftest.py             # Fixtures and mocked sheet data
│       ├── test_cards.py           # Price endpoint tests
│       └── test_suggestions.py     # Suggestion + rate limit tests
├── react-app/                      # React + TypeScript frontend
│   └── src/
│       ├── App.tsx                 # Search UI — card image, price, suggestion
│       └── App.css                 # Styles
├── docs/                           # Requirements spec and design document
├── .github/
│   └── workflows/
│       └── ci.yml                  # GitHub Actions CI
└── README.md
```

| Path | Description |
|---|---|
| [`backend/`](backend/) | Python FastAPI backend — API, services, and tests |
| [`backend/services/`](backend/services/) | Core business logic (card lookup, eBay pricing, Gemini suggestions) |
| [`backend/routers/`](backend/routers/) | FastAPI route handlers |
| [`backend/tests/`](backend/tests/) | Pytest test suite |
| [`react-app/src/`](react-app/src/) | React + TypeScript frontend |
| [`docs/`](docs/) | Requirements specification and design document |

---

## Requirements Specification & Design Document

[`docs/modular_system_design_layers.md`](docs/modular_system_design_layers.md)

---

## Test Directory

[`backend/tests/`](backend/tests/)

Run the tests:

```bash
cd backend
python3 -m pytest tests/ -v
```

All tests mock external APIs (Google Sheets, eBay, Gemini) — no real credentials needed.

---

## Setup & Execution

### Prerequisites

- Python 3.10+
- Node.js 18+
- A Google Cloud service account with Sheets API access
- eBay Developer account (Browse API)
- Google Gemini API key

### 1. Clone the repository

```bash
git clone https://github.com/bnmpower1/One-piece.git
cd One-piece
```

### 2. Backend setup

```bash
cd backend
pip install -r requirements.txt
```

Copy the environment template and fill in your keys:

```bash
cp .env.example .env
```

| Variable | Description |
|---|---|
| `GOOGLE_API_KEY` | Gemini API key |
| `MODEL_NAME` | `gemini-2.5-flash-lite` |
| `SHEETS_ID` | Google Sheets spreadsheet ID |
| `GOOGLE_SERVICE_ACCOUNT` | Path to service account JSON file |
| `EBAY_CLIENT_ID` | eBay application client ID |
| `EBAY_CLIENT_SECRET` | eBay application client secret |

Start the backend:

```bash
uvicorn main:app --reload
```

API available at `http://localhost:8000`

### 3. Frontend setup

```bash
cd react-app
npm install
npm run dev
```

App available at `http://localhost:5173`

> The frontend proxies all `/api` requests to the backend automatically during development.

---

## API Endpoints

| Endpoint | Description |
|---|---|
| `GET /cards/price?q=<query>` | Live eBay price for a card |
| `GET /cards/suggest?q=<query>` | Gemini buy / hold / sell suggestion |
| `GET /cards/image?url=<url>` | Proxied card image |

Search query accepts card number (`OP01-060`), character name (`Luffy`), or descriptive terms (`manga shanks`).

### Response statuses

| Status | Meaning |
|---|---|
| `success` | Card found with data |
| `not_found` | No card matched the query |
| `multiple_matches` | Query matched more than one card |
| `price_unavailable` | Card found but no price data |
| `insufficient_data` | Card found but suggestion could not be generated |

---

## CI

GitHub Actions runs on every push — backend tests and frontend build check.  
See [`.github/workflows/ci.yml`](.github/workflows/ci.yml).
