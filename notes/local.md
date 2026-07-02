# Running Locally (uv + local Postgres)

## Postgres
# Start local Postgres 18 (Homebrew)
brew services start postgresql@18

# Connect to local Postgres
psql -U <your_postgres_user> -d binance_crypto_data

## Services
# Run ingest once (fetches full history, upserts — safe to re-run)
uv run python src/fetch_and_ingest.py

# Run API with hot reload — http://localhost:8000 (interactive docs at /docs)
uv run fastapi dev src/api.py

# Run dashboard — http://localhost:8501
uv run streamlit run src/dashboard.py

## Tests
uv run pytest

## Useful queries
SELECT COUNT(*) FROM crypto_daily_candles;
SELECT DISTINCT symbol FROM crypto_daily_candles;
SELECT * FROM crypto_daily_candles WHERE symbol = 'BTCUSDT' ORDER BY open_time DESC LIMIT 5;
