# Project: Crypto Data Pipeline — Onboarding Assignment

## Overview
Full data service lifecycle: ingest crypto data → Postgres → FastAPI → Dashboard → Kubernetes.
Robin is a Junior Data Engineer building this as an onboarding assignment. **AI is explicitly the last resort** per the assignment description — Robin reaches for docs and Stack Overflow first. Act as a mentor/guide: explain concepts, ask guiding questions, give feedback on Robin's code. Do NOT write complete implementations. Short isolated code examples (1-3 lines) to illustrate a specific concept are fine.

## Data Source
- **API**: Binance public REST API (no auth required)
- **Endpoint**: `GET https://api.binance.com/api/v3/klines`
- **Symbols**: BTCUSDT, ETHUSDT, XRPUSDT, SOLUSDT, LINKUSDT, ADAUSDT
- **Interval**: `1d` (daily candles)
- **Start date**: 2000-01-01
- **Fields stored**: symbol, open_time, open_price, high_price, low_price, close_price, volume, number_of_trades

## Key Design Decisions
- Daily candles chosen for granular historical data back to 2000-01-01
- Prices stored as `NUMERIC(20,8)` — never FLOAT for financial data
- Timestamps stored as `TIMESTAMPTZ` (UTC)
- Single table for all symbols with `(symbol, open_time)` as composite primary key
- Currency conversion (USD → EUR/SEK/NOK/DKK) done at display time using live exchange rates, not stored historically
- Config via environment variables (`.env` + `python-dotenv`)

## Database
- **Postgres 18** via Homebrew, started with `brew services start postgresql@18`
- **Database**: `binance_crypto_data`
- **Table**: `crypto_daily_candles`

```sql
CREATE TABLE IF NOT EXISTS crypto_daily_candles (
    symbol TEXT NOT NULL,
    open_time TIMESTAMPTZ NOT NULL,
    open_price NUMERIC(20,8) NOT NULL,
    high_price NUMERIC(20,8) NOT NULL,
    low_price NUMERIC(20,8) NOT NULL,
    close_price NUMERIC(20,8) NOT NULL,
    volume NUMERIC(20,8) NOT NULL,
    number_of_trades INTEGER NOT NULL,
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
  postgres-pvc.yaml         # PersistentVolumeClaim for Postgres
  postgres-deployment.yaml  # Postgres Deployment
  postgres-service.yaml     # Postgres Service
  api-deployment.yaml       # API Deployment
  api-service.yaml          # API Service
  dashboard-deployment.yaml # Dashboard Deployment
  dashboard-service.yaml    # Dashboard Service
  ingest-job.yaml           # CronJob for daily ingest
infra/
  __main__.py           # Pulumi IaC (VPC, RDS, ECR, Lambda, API Gateway, EventBridge)
  Pulumi.yaml           # Pulumi project config
  Pulumi.dev.yaml       # Stack config for dev (encrypted secrets)
  requirements.txt      # Pulumi Python dependencies
dockerfile.ingest       # Docker image for ingest
dockerfile.api          # Docker image for API
dockerfile.dashboard    # Docker image for dashboard
docker-compose.yml      # Local orchestration
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
- [x] FastAPI with three endpoints, Pydantic models, RealDictCursor
- [x] Streamlit dashboard with currency conversion and Plotly candlestick chart
- [x] Dockerfiles for all three services (ingest, api, dashboard)
- [x] docker-compose.yml with healthcheck, volumes and service dependencies
- [x] Kubernetes manifests for all services (Deployment, Service, PVC, Secret, CronJob)
- [x] Local kind cluster (`binance-crypto-cluster`) with all pods running
- [x] AWS SSO configured (`<AWS_PROFILE>` profile, `<AWS_REGION>`)
- [x] Pulumi local mode (`pulumi login --local`), stack `dev`
- [x] VPC, subnets, security group, RDS subnet group deployed via Pulumi
- [x] RDS Postgres 18.4 (`db.t4g.micro`) deployed in private subnet
- [x] ECR repos created for ingest and api images
- [x] Docker images built and pushed to ECR
- [x] IAM Role + policy attachments for Lambda
- [x] ingest Lambda + api Lambda created (container image from ECR)
- [x] `mangum` added as dependency for FastAPI Lambda adapter

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
- Run the full stack with: `docker compose up --build`
- Postgres 18 image with named volume (`postgres_data`) for persistent data
- `DB_HOST=postgres` set explicitly in compose to override `.env` (localhost does not work in Docker)
- `API_BASE=http://api:8000` set in dockerfile.dashboard via ENV
- Healthcheck on postgres + `condition: service_healthy` ensures correct startup order

## Kubernetes (kind)
- **Cluster**: `binance-crypto-cluster` — created with `kind create cluster --name binance-crypto-cluster`
- **Images** loaded with: `kind load docker-image <image> --name binance-crypto-cluster`
- **imagePullPolicy: Never** required in deployments to use local images
- **Secrets** for sensitive variables (`DB_USER`, `DB_PASSWORD`, `DB_PORT`) — gitignored
- **CronJob** for ingest runs daily at midnight — trigger manually with: `kubectl create job ingest-manual --from=cronjob/ingest`
- **Port-forward** to reach dashboard locally: `kubectl port-forward service/dashboard 8501:8501`
- Apply all manifests: `kubectl apply -f k8s/`

## AWS Deployment (Serverless + Pulumi)
- **Goal**: deploy the full stack to AWS with serverless architecture via Pulumi (Infrastructure as Code)
- **Tools**: `awscli` + `pulumi` — installed globally via Homebrew
- **Architecture**:
  - **Ingest** → AWS Lambda + EventBridge (daily cron schedule)
  - **API** → AWS Lambda + API Gateway (FastAPI via Mangum adapter)
  - **Database** → AWS RDS Postgres
  - **Dashboard** → AWS ECS Fargate (Streamlit does not fit serverless)
- **Pulumi language**: Python, local state mode (`pulumi login --local`)
- **AWS environment**: sandbox account (`<AWS_PROFILE>` profile, `<AWS_REGION>`)
- **Docker builds for Lambda**: must use `--platform linux/amd64 --provenance=false` on Apple Silicon — Lambda only supports the classic Docker manifest format, not OCI format which Docker Desktop on Mac produces by default

## What's Next
- Add `handler = Mangum(app)` to `src/api.py`
- API Gateway for api-Lambda (HTTP API)
- EventBridge schedule for ingest-Lambda (daily cron)
- ECS Fargate for the Streamlit dashboard
- Rebuild and push new Docker images after code changes

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
