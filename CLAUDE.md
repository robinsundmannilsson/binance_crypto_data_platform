# Project: Crypto Data Pipeline — Onboarding Assignment

## Overview
Full data service lifecycle: ingest crypto data → Postgres → FastAPI → Dashboard → Kubernetes.
Robin is a Junior Data Engineer building this as an onboarding assignment. **AI is explicitly the last resort** per the assignment description — Robin reaches for docs and Stack Overflow first. Act as a mentor/guide: explain concepts, ask guiding questions, give feedback on Robin's code. Do NOT write complete implementations. Short isolated code examples (1-3 lines) to illustrate a specific concept are fine.

## Data Source
- **API**: Binance public REST API (no auth required)
- **Endpoint**: `GET https://api.binance.com/api/v3/klines`
- **Symbols**: BTCUSDT, ETHUSDT, XRPUSDT, SOLUSDT, LINKUSDT, ADAUSDT
- **Interval**: `1w` (weekly candles)
- **Start date**: 2020-01-01
- **Fields stored**: symbol, open_time, open_price, high_price, low_price, close_price, volume, number_of_trades

## Key Design Decisions
- Weekly candles chosen for richer data than monthly but simpler than daily
- Prices stored as `NUMERIC(20,8)` — never FLOAT for financial data
- Timestamps stored as `TIMESTAMPTZ` (UTC)
- Single table for all symbols with `(symbol, open_time)` as composite primary key
- Currency conversion (USD → EUR/SEK/NOK/DKK) done at display time using live exchange rates, not stored historically
- Config via environment variables (`.env` + `python-dotenv`)

## Database
- **Postgres 18** via Homebrew, started with `brew services start postgresql@18`
- **Database**: `onboarding_crypto_data`
- **Table**: `crypto_weekly_candles`

```sql
CREATE TABLE IF NOT EXISTS crypto_weekly_candles (
    symbol TEXT,
    open_time TIMESTAMPTZ,
    open_price NUMERIC(20,8),
    high_price NUMERIC(20,8),
    low_price NUMERIC(20,8),
    close_price NUMERIC(20,8),
    volume NUMERIC(20,8),
    number_of_trades INTEGER,
    PRIMARY KEY (symbol, open_time)
);
```

## Project Structure
```
src/
  fetch_and_ingest.py   # Binance API call + parse_candle function
.env                    # Config (never commit this)
```

## What's Done
- [x] Binance API call working, loops over all symbols
- [x] `parse_candle(raw, symbol)` function — converts raw list to typed dict
- [x] Environment variables via `.env`
- [x] Postgres database and table created

## What's Next
1. Connect Python to Postgres with `psycopg2`
2. Write parsed candles to DB using `INSERT ... ON CONFLICT DO UPDATE` (upsert)
3. Structure code properly (wrap in functions, add `if __name__ == "__main__":`)
4. Add structured logging
5. Add error handling (network errors, rate limits)
6. Write pytest tests for `parse_candle`
7. FastAPI layer
8. Dashboard (Streamlit)
9. Kubernetes (kind)

## Environment
```
SYMBOLS=BTCUSDT,ETHUSDT,XRPUSDT,SOLUSDT,LINKUSDT,ADAUSDT
INTERVAL=1w
START_DATE=2020-01-01
DB_HOST=localhost
DB_NAME=onboarding_crypto_data
DB_USER=YOUR_POSTGRES_USER
DB_PORT=5432
```
