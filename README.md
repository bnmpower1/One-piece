# One Piece Card Tracker

A One Piece TCG card price tracker with live eBay market data and AI-powered buy / hold / sell suggestions via Google Gemini.

---

## Demo Video

> **[Watch Demo Video](#)** ← *link to be added*

---

## Repository Structure

```text
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
│   │   ├── ebay_service.py         # eBay Browse API live prices
│   │   └── suggestion_service.py   # Gemini buy/hold/sell suggestions
│   ├── routers/
│   │   ├── cards.py                # GET /cards/price, /cards/image
│   │   ├── suggestions.py          # GET /cards/suggest
│   │   └── ebay_notifications.py   # eBay account deletion webhook
│   └── tests/
│       ├── conftest.py             # Fixtures and mocked sheet data
│       ├── test_cards.py           # Price endpoint tests
│       └── test_suggestions.py     # Suggestion and rate limit tests
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

| Path                                     | Description                                                            |
| ---------------------------------------- | ---------------------------------------------------------------------- |
| [`backend/`](backend/)                   | Python FastAPI backend — API, services, and tests                      |
| [`backend/services/`](backend/services/) | Core business logic: card lookup, eBay pricing, and Gemini suggestions |
| [`backend/routers/`](backend/routers/)   | FastAPI route handlers                                                 |
| [`backend/tests/`](backend/tests/)       | Pytest test suite                                                      |
| [`react-app/src/`](react-app/src/)       | React + TypeScript frontend                                            |
| [`docs/`](docs/)                         | Requirements specification and design document                         |

---

## Requirements Specification & Design Document

[`docs/modular_system_design_layers.md`](docs/modular_system_design_layers.md)

---

## Test Directory

[`backend/tests/`](backend/tests/)

Run the backend tests:

### Mac / Linux

```bash
cd backend
python3 -m pytest tests/ -v
```

### Windows PowerShell

```powershell
cd backend
py -m pytest tests/ -v
```

All tests mock external APIs such as Google Sheets, eBay, and Gemini, so no real credentials are needed to run the test suite.

---

## Setup & Execution

### Prerequisites

* Python 3.10+
* Node.js 18+
* A Google Cloud service account with Sheets API access
* eBay Developer account with Browse API access
* Google Gemini API key

---

## 1. Clone the Repository

```bash
git clone https://github.com/bnmpower1/One-piece.git
cd One-piece
```
---

## 2. Backend Setup

### Mac / Linux

```bash
cd backend
python3 -m pip install -r requirements.txt
cp .env.example .env
```

### Windows PowerShell

```powershell
cd backend
py -m pip install -r requirements.txt
copy .env.example .env
```

Then fill in your keys inside `.env`.

| Variable                 | Description                                        |
| ------------------------ | -------------------------------------------------- |
| `GOOGLE_API_KEY`         | Gemini API key                                     |
| `MODEL_NAME`             | Gemini model name, such as `gemini-2.5-flash-lite` |
| `SHEETS_ID`              | Google Sheets spreadsheet ID                       |
| `GOOGLE_SERVICE_ACCOUNT` | Path to service account JSON file                  |
| `EBAY_CLIENT_ID`         | eBay application client ID                         |
| `EBAY_CLIENT_SECRET`     | eBay application client secret                     |

---

## 3. Start the Backend

### Mac / Linux

```bash
python3 -m uvicorn main:app --reload
```

### Windows PowerShell

```powershell
py -m uvicorn main:app --reload
```

The backend API will be available at:

```text
http://localhost:8000
```

---

## 4. Frontend Setup

Open a new terminal window from the project root.

### Mac / Linux

```bash
cd react-app
npm install
npm run dev
```

### Windows PowerShell

```powershell
cd react-app
npm install
npm run dev
```

The frontend app will be available at:

```text
http://localhost:5173
```

The frontend proxies all `/api` requests to the backend automatically during development.

---

## API Endpoints

| Endpoint                       | Description                         |
| ------------------------------ | ----------------------------------- |
| `GET /cards/price?q=<query>`   | Live eBay price for a card          |
| `GET /cards/suggest?q=<query>` | Gemini buy / hold / sell suggestion |
| `GET /cards/image?url=<url>`   | Proxied card image                  |

Search query accepts card number, character name, or descriptive terms.

Examples:

```text
OP01-060
Luffy
manga shanks
parallel zoro
```

---

## Response Statuses

| Status              | Meaning                                          |
| ------------------- | ------------------------------------------------ |
| `success`           | Card found with data                             |
| `not_found`         | No card matched the query                        |
| `multiple_matches`  | Query matched more than one card                 |
| `price_unavailable` | Card found but no price data                     |
| `insufficient_data` | Card found but suggestion could not be generated |

---

## CI

GitHub Actions runs on every push. It checks the backend tests and frontend build.

See [`.github/workflows/ci.yml`](.github/workflows/ci.yml).
