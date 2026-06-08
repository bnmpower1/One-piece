# One Piece Card Tracker

A One Piece TCG card tracker with live eBay price lookup and Gemini-powered buy/hold/sell market suggestions.

## Stack

- **Frontend:** React + TypeScript + Vite (`react-app/`) — not yet started, still default Vite template
- **Backend:** Python FastAPI + SQLite via SQLAlchemy (`backend/`)
- **AI:** Google Gemini (`gemini-2.5-flash-lite`) for market suggestions
- **Prices:** eBay Browse API (live), seeded DB prices (fallback)

## Backend Structure

```
backend/
├── main.py                  # FastAPI app, seeds DB on startup, rate limit handler
├── database.py              # SQLAlchemy + SQLite setup
├── models.py                # Card and CardPrice DB tables
├── schemas.py               # Pydantic response shapes
├── limiter.py               # slowapi rate limiter (10/minute on Gemini endpoint)
├── seed.py                  # Seeds DB from seed_data.json on startup
├── seed_data.json           # 8 curated One Piece cards with prices and metadata
├── .env                     # Real keys — gitignored, never commit
├── .env.example             # Placeholder template — safe to commit
├── requirements.txt
├── services/
│   ├── card_service.py      # Card lookup + price fetching (eBay → DB fallback)
│   ├── ebay_service.py      # eBay OAuth token cache + Browse API price fetch
│   └── suggestion_service.py # Gemini buy/hold/sell suggestion logic
├── routers/
│   ├── cards.py             # GET /cards/price?q=
│   └── suggestions.py       # GET /cards/suggest?q= (rate limited)
└── tests/
    ├── conftest.py          # Test DB setup, client fixture, reset_limiter fixture
    ├── test_cards.py        # 8 tests for price lookup
    └── test_suggestions.py  # 9 tests for suggestions + rate limit
```

## API Endpoints

| Endpoint | Description |
|---|---|
| `GET /cards/price?q=<query>` | Returns live eBay price for a card |
| `GET /cards/suggest?q=<query>` | Returns Gemini buy/hold/sell suggestion (10/min rate limit) |

Search query can be a card number (`OP06-118`), character name (`Zoro`), or set code (`OP-06`).

## Response Statuses

Both endpoints return a `status` field:
- `success` — found card and data
- `not_found` — no card matched the query
- `multiple_matches` — query matched more than one card, `data` is a list of matches
- `price_unavailable` — card found but no price data
- `insufficient_data` — card found but suggestion could not be generated

## Price Fallback Chain

```
eBay Browse API (live) → seeded DB prices → price_unavailable
```

eBay credentials are pending developer account approval (~1 day). Until then, seeded DB prices are used automatically.

## Environment Variables

Add these to `backend/.env` (copy from `.env.example`):

```
GOOGLE_API_KEY=        # Gemini API key
MODEL_NAME=gemini-2.5-flash-lite
EBAY_CLIENT_ID=        # Pending eBay developer approval
EBAY_CLIENT_SECRET=    # Pending eBay developer approval
```

## Running the Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

## Running Tests

```bash
cd backend
python3 -m pytest tests/ -v
```

All 17 tests pass. Tests mock eBay and Gemini calls — no real API keys needed to run them.

## Seeded Cards

The DB is pre-seeded with 8 cards from `seed_data.json`:

| Card | Set | Card Number | Rarity |
|---|---|---|---|
| Monkey D. Luffy | OP-01 | OP01-060 | Manga Rare |
| Roronoa Zoro | OP-06 | OP06-118 | Manga Rare |
| Nami | OP-01 | OP01-082 | Manga Rare |
| Trafalgar Law | OP-05 | OP05-093 | Manga Rare |
| Sanji | OP-03 | OP03-098 | Manga Rare |
| Boa Hancock | OP-02 | OP02-093 | Secret Rare |
| Shanks | OP-06 | OP06-078 | Secret Rare |
| Portgas D. Ace | OP-05 | OP05-060 | Secret Rare |

## What's Left

- [ ] eBay developer credentials (approval pending)
- [ ] React frontend UI — connects to `/cards/price` and `/cards/suggest`
- [ ] Wire frontend to backend API
