# Running Locally (uv + local Postgres)

Run the services directly on your machine, against a local Postgres.

## Postgres

Start local Postgres 18 (Homebrew):

```bash
brew services start postgresql@18
```

Connect with psql:

```bash
psql -U <your_postgres_user> -d binance_crypto_data
```

## Services

**Ingest** — fetches the full history and upserts, safe to re-run:

```bash
uv run python src/fetch_and_ingest.py
```

**API** — hot reload, serves on <http://localhost:8000> (interactive docs at `/docs`):

```bash
uv run fastapi dev src/api.py
```

**Dashboard** — serves on <http://localhost:8501>:

```bash
uv run streamlit run src/dashboard.py
```

## Tests

```bash
uv run pytest
```

## Useful queries

```sql
SELECT COUNT(*) FROM crypto_daily_candles;
SELECT DISTINCT symbol FROM crypto_daily_candles;
SELECT * FROM crypto_daily_candles WHERE symbol = 'BTCUSDT' ORDER BY open_time DESC LIMIT 5;
```
