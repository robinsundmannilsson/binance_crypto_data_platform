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
  api.py                # FastAPI app
  models.py             # Pydantic response models
  dashboard.py          # Streamlit dashboard
k8s/
  postgres-secrets.yaml     # Kubernetes Secret (gitignored)
  postgres-pvc.yaml         # PersistentVolumeClaim för Postgres
  postgres-deployment.yaml  # Postgres Deployment
  postgres-service.yaml     # Postgres Service
  api-deployment.yaml       # API Deployment
  api-service.yaml          # API Service
  dashboard-deployment.yaml # Dashboard Deployment
  dashboard-service.yaml    # Dashboard Service
  ingest-job.yaml           # CronJob för daglig ingest
dockerfile.ingest       # Docker image for ingest
dockerfile.api          # Docker image for API
dockerfile.dashboard    # Docker image for dashboard
docker-compose.yml      # Orchestrerar alla services
.env                    # Config (never commit this)
```

## What's Done
- [x] Binance API call working, loops over all symbols
- [x] `parse_candle(raw, symbol)` function — converts raw list to typed dict
- [x] Environment variables via `.env`
- [x] `get_connection()` via psycopg2
- [x] `insert_candle(cur, candle)` with `INSERT ... ON CONFLICT DO UPDATE` upsert
- [x] `create_table_if_not_exists(cur)` — creates table on startup
- [x] Code structured with functions and `if __name__ == "__main__":`
- [x] Structured logging with `logging.basicConfig(level=logging.INFO)`
- [x] Error handling for network errors with `try/except requests.RequestException`
- [x] pytest tests for `parse_candle` (types, UTC timezone, short raw)
- [x] FastAPI med tre endpoints, Pydantic-modeller, RealDictCursor
- [x] Streamlit dashboard med valutakonvertering och Plotly candlestick-chart
- [x] Dockerfiles för alla tre services (ingest, api, dashboard)
- [x] docker-compose.yml med healthcheck, volumes och service dependencies
- [x] Kubernetes manifests för alla services (Deployment, Service, PVC, Secret, CronJob)
- [x] Lokalt kind-kluster (`binance-crypto-cluster`) med alla pods körandes

## FastAPI
- **File**: `src/api.py`
- **Models**: `src/models.py` — `CandleResponse` (Pydantic BaseModel)
- Uses `RealDictCursor` from psycopg2 for dict responses
- Endpoints:
  - `GET /health` — health check
  - `GET /candles/{symbol}` — full price history with optional `from_date`/`to_date` query params
  - `GET /candles/{symbol}/latest` — latest candle for a symbol
- Run locally with: `uv run fastapi dev src/api.py`

## Dashboard (Streamlit)
- **File**: `src/dashboard.py`
- Reads from FastAPI (not DB directly) via `API_BASE` env var (default: `http://localhost:8000`)
- Sidebar with symbol selector (6 symbols with full names) and currency selector (USD/EUR/SEK/NOK/DKK)
- Binance logo via base64-encoded SVG
- Live currency conversion via frankfurter.app API (done at display time, not stored)
- Metrics: open/high/low/close price, volume, number of trades, all-time high, all-time low
- Candlestick chart via Plotly (`go.Candlestick`) with currency conversion
- Run locally with: `uv run streamlit run src/dashboard.py`

## Docker
- Kör hela stacken med: `docker compose up --build`
- Postgres 18 image med named volume (`postgres_data`) för persistent data
- `DB_HOST=postgres` sätts explicit i compose för att överskriva `.env` (localhost fungerar inte i Docker)
- `API_BASE=http://api:8000` sätts i dockerfile.dashboard via ENV
- Healthcheck på postgres + `condition: service_healthy` säkerställer rätt startordning

## Kubernetes (kind)
- **Kluster**: `binance-crypto-cluster` — skapat med `kind create cluster --name binance-crypto-cluster`
- **Images** laddas in med: `kind load docker-image <image> --name binance-crypto-cluster`
- **imagePullPolicy: Never** krävs i deployments för att använda lokala images
- **Secrets** för känsliga variabler (`DB_USER`, `DB_PASSWORD`, `DB_PORT`) — gitignorerad
- **CronJob** för ingest kör dagligen midnatt — triggas manuellt med: `kubectl create job ingest-manual --from=cronjob/ingest`
- **Port-forward** för att nå dashboard lokalt: `kubectl port-forward service/dashboard 8501:8501`
- Applicera alla manifests: `kubectl apply -f k8s/`

## What's Next
- Assignment är komplett!

## Environment
Copy `.env.example` and fill in your values:
```
SYMBOLS=BTCUSDT,ETHUSDT,XRPUSDT,SOLUSDT,LINKUSDT,ADAUSDT
INTERVAL=1d
START_DATE=2000-01-01
DB_HOST=localhost
DB_NAME=binance_crypto_data
DB_USER=<your_postgres_user>
DB_PASSWORD=<your_postgres_password>
DB_PORT=5432
BASE_URL=https://api.binance.com/api/v3/klines
```
