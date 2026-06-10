# Modular System Design Layers

## Part A: Functionality (2-4 Functionalities Required)

### Functionality 1: Card Price Lookup
- **Input:** Search query string — card number (`OP01-060`), character name (`Luffy`), or descriptive terms (`manga shanks`)
- **Output:** Card name, card number, set code, rarity, variant, image URL, live eBay price in USD, currency label
- **Success:** Card matched uniquely and eBay returns at least one listing → `status: "success"` with full card and price data
- **Failure/Edge Cases:**
  - Query matches no card → `status: "not_found"`
  - Query matches more than one card → `status: "multiple_matches"`, returns list of candidates for the user to refine
  - Card found but eBay returns no listings and sheet has no fallback prices → `status: "price_unavailable"`
  - eBay API is unreachable → falls back to TCGPlayer prices stored in Google Sheets; if both unavailable → `status: "price_unavailable"`
  - eBay OAuth token expired mid-session → engine automatically re-fetches token and retries
  - Query is empty or only whitespace → treated as no match → `status: "not_found"`
  - Query contains a valid set code prefix but no matching card number (e.g. `OP-99`) → `status: "not_found"`
  - Single-character query token (e.g. `R`) → matched as exact rarity field only, not substring, to avoid false positives across unrelated cards
  - Natural-language rarity alias used (e.g. `super rare`, `secret rare`) → normalised to sheet codes (`SR`, `SEC`) before matching
  - Card exists in multiple variants (Standard, Parallel, Manga Alternate Art) → engine prefers Standard unless variant keyword is present in query; all variants returned as `multiple_matches` if ambiguous
  - Google Sheets cache is stale and Sheets API is temporarily unreachable → engine serves last cached result until TTL expires, then raises

---

### Functionality 2: Buy / Hold / Sell Suggestion
- **Input:** Search query string (same format as Functionality 1)
- **Output:** Suggestion (`buy`, `hold`, or `sell`), plain-English reasoning, card name, card number, rarity, average price in USD
- **Success:** Card matched, price data available, and Gemini returns a valid JSON suggestion → `status: "success"`
- **Failure/Edge Cases:**
  - Rate limit exceeded (10 requests/minute or 50 requests/day per IP) → HTTP 429
  - Query matches no card → `status: "not_found"`
  - No price data available from any source → `status: "insufficient_data"`
  - Gemini API is unreachable or returns an HTTP error → exception caught → `status: "insufficient_data"`
  - Gemini returns malformed JSON or a suggestion value outside `buy`/`hold`/`sell` → `ValueError` raised → `status: "insufficient_data"`
  - Multiple cards matched → `status: "multiple_matches"`, returns candidate list for user to refine
  - User asks for guaranteed profit → Gemini reasoning includes a disclaimer that suggestions are speculative, not financial advice; `status: "success"` is still returned
  - Card has no live eBay price but has sheet fallback prices → suggestion is still generated using sheet prices
  - Card has extremely low market value (< $1) → suggestion generated normally; Gemini may note the card has low trade value
  - Gemini prompt includes card metadata fields that are empty (e.g. no subtypes) → empty fields passed as-is; Gemini ignores them gracefully

---

### Functionality 3: Card Image Display
- **Input:** Image URL string (passed as `?url=` query parameter, sourced from Google Sheets)
- **Output:** Raw image bytes served with correct `Content-Type` header
- **Success:** URL is from an allowed domain and the remote server returns an image → image bytes proxied to client
- **Failure/Edge Cases:**
  - URL hostname not in allowlist (`en.onepiece-cardgame.com`, `tcgplayer.com`) → HTTP 400
  - Remote server returns non-image content type → HTTP 400
  - Remote server unreachable, returns 403, or times out → HTTP 404
  - `url` parameter is missing entirely → FastAPI returns HTTP 422 (unprocessable entity)
  - URL is malformed and hostname cannot be parsed → resolves to empty string, fails allowlist check → HTTP 400
  - Remote CDN enforces hotlink protection via `Referer` header → backend request has no browser `Referer`, bypassing the restriction
  - Remote server redirects to a different domain → `httpx` follows redirects; final resolved URL is served; hostname of the original URL is what is validated

---

## Part B: Architecture Mapping

> **Layer definitions**
> - `interface` — React frontend (search bar, results display) and FastAPI routers (HTTP request/response handling)
> - `engine` — Python service layer (business logic: card matching, price fetching, suggestion generation)
> - `storage` — Google Sheets (card catalog), eBay Browse API (live prices), Google Gemini API (AI suggestions)

---

### Functionality 1 Mapping
- `interface` responsibilities: Render search input; send `GET /cards/price?q=` request; display card image (via proxy), name, set, rarity, variant, and price; show appropriate message for `not_found`, `multiple_matches`, and `price_unavailable` statuses; allow user to click a match candidate to re-search by card number
- `engine` responsibilities: Tokenise and normalise the query; expand rarity aliases; apply single-character exact-field matching to prevent false positives; match against in-memory card list; prefer Standard variant when deduplicating; call eBay Browse API with a variant-aware query string; fall back to sheet prices if eBay fails; build and return response payload
- `storage` responsibilities: Google Sheets provides the full card catalog (name, number, set, rarity, variant, fallback TCGPlayer prices, image URL) cached for 10 minutes; eBay Browse API provides live fixed-price listing data filtered by USD currency

---

### Functionality 2 Mapping
- `interface` responsibilities: Render buy/hold/sell badge colour-coded by suggestion; display plain-English reasoning; show average price; display error message on HTTP 429 rate limit response
- `engine` responsibilities: Reuse card lookup and price fetch logic from Functionality 1; build a structured natural-language prompt from card metadata and price; call Gemini API with JSON output mode; validate suggestion value; apply per-IP rate limiting (10/minute, 50/day) via slowapi; lazy-initialise the Gemini client on first call so import does not require a live API key
- `storage` responsibilities: Google Sheets provides card metadata (rarity, variant, color, subtypes, card type) embedded in the Gemini prompt; eBay Browse API provides the live price embedded in the prompt; Gemini API generates the suggestion and reasoning text

---

### Functionality 3 Mapping
- `interface` responsibilities: Construct proxy URL (`/api/cards/image?url=<encoded>`) from the `image_url` field returned in the price response; render `<img>` element pointing to the proxy endpoint instead of the direct CDN URL
- `engine` responsibilities: Parse and validate URL hostname against a hardcoded allowlist to prevent SSRF; fetch image bytes from remote CDN via `httpx`; validate response `Content-Type` starts with `image/`; stream bytes back to client with matching media type header
- `storage` responsibilities: Google Sheets provides the `image_url` column value for each card; remote CDN (Bandai official site or TCGPlayer) serves the actual image bytes

---

## Part C: Interface Contracts

---

### Functionality 1

#### `interface -> engine`
- **Function(s):** `GET /cards/price?q={query}` → `get_card_price(query: str)` in `services/card_service.py`
- **Input payload:** `q` — URL query parameter string
- **Return payload/status:**
  ```json
  {
    "status": "success",
    "data": {
      "card_name": "Monkey D. Luffy",
      "card_number": "OP01-060",
      "set": "OP-01",
      "rarity": "MR",
      "variant": "Manga Alternate Art",
      "image_url": "https://...",
      "prices": { "eBay": 1775.00 },
      "currency": "USD"
    }
  }
  ```
- **Failure statuses:**
  - `{"status": "not_found", "message": "Card not found."}`
  - `{"status": "multiple_matches", "data": ["OP01-060 Monkey D. Luffy", "OP01-060 Monkey D. Luffy (Parallel)"]}`
  - `{"status": "price_unavailable", "message": "Price unavailable."}`

#### `engine -> storage`
- **Function(s):** `get_cards()` in `services/sheets_service.py`; `fetch_ebay_prices(card_number, card_name, variant)` in `services/ebay_service.py`
- **Input payload:** `get_cards()` takes no arguments (uses 10-minute in-memory cache); `fetch_ebay_prices` takes card number string, card name string, variant string
- **Return payload/status:** `get_cards()` returns `list[CardRecord]`; `fetch_ebay_prices` returns `{"eBay": float}` or `None`
- **Failure statuses:**
  - `get_cards()` raises `gspread.exceptions.APIError` on Sheets auth/network failure
  - `fetch_ebay_prices` returns `None` if no USD listings found; raises `httpx.HTTPStatusError` on API error

---

### Functionality 2

#### `interface -> engine`
- **Function(s):** `GET /cards/suggest?q={query}` → `get_market_suggestion(query: str)` in `services/suggestion_service.py`
- **Input payload:** `q` — URL query parameter string
- **Return payload/status:**
  ```json
  {
    "status": "success",
    "data": {
      "suggestion": "hold",
      "reasoning": "Shanks from OP-01 is a chase card...",
      "card_name": "Shanks",
      "card_number": "OP01-120",
      "rarity": "SEC",
      "image_url": "https://...",
      "avg_price_usd": 173.46
    }
  }
  ```
- **Failure statuses:**
  - `{"status": "not_found", "message": "Card not found."}`
  - `{"status": "multiple_matches", "data": [...]}`
  - `{"status": "insufficient_data", "message": "Not enough market data."}`
  - `{"status": "insufficient_data", "message": "Could not generate suggestion."}`
  - HTTP 429 on rate limit exceeded

#### `engine -> storage`
- **Function(s):** `fetch_justtcg_price(card: CardRecord)` → `fetch_ebay_prices(...)` for price data; `_get_client().models.generate_content(...)` for Gemini call in `services/suggestion_service.py`
- **Input payload:** `CardRecord` dataclass; structured prompt string containing card name, number, set, rarity, type, color, subtypes, variant, and average price
- **Return payload/status:** Price function returns `{"eBay": float}` or `None`; Gemini returns `{"suggestion": "buy"|"hold"|"sell", "reasoning": str}`
- **Failure statuses:**
  - Price returns `None` → falls back to `_sheet_prices(card)`; if both `None` → `status: "insufficient_data"`
  - Gemini raises any exception → caught → `status: "insufficient_data"`
  - Gemini returns suggestion not in `("buy", "hold", "sell")` → `ValueError` raised → `status: "insufficient_data"`

---

### Functionality 3

#### `interface -> engine`
- **Function(s):** `GET /cards/image?url={encoded_url}` → `proxy_image(url: str)` in `routers/cards.py`
- **Input payload:** `url` — URL-encoded image URL string from the `image_url` field in the price response
- **Return payload/status:** Raw image bytes with `Content-Type: image/png` (or matching remote type)
- **Failure statuses:**
  - HTTP 422 if `url` parameter is missing (FastAPI validation)
  - HTTP 400 if hostname not in allowlist or response is not `image/*`
  - HTTP 404 if remote fetch fails or times out

#### `engine -> storage`
- **Function(s):** `httpx.get(url, follow_redirects=True, timeout=10)`
- **Input payload:** Validated image URL string
- **Return payload/status:** `httpx.Response` with image bytes and `content-type` header
- **Failure statuses:**
  - `httpx.HTTPStatusError` (e.g. 403 from CDN) → caught → HTTP 404 to client
  - `httpx.TimeoutException` → caught → HTTP 404 to client
  - Connection error → caught → HTTP 404 to client
