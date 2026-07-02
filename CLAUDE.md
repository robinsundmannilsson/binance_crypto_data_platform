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
  __main__.py           # Pulumi IaC (RDS, ECR, Lambda, API Gateway, EventBridge, ECS Fargate)
  Pulumi.yaml           # Pulumi project config
  Pulumi.dev.yaml       # Stack config for dev (encrypted secrets)
  requirements.txt      # Pulumi Python dependencies
dockerfile.ingest        # Docker image for ingest (local/Docker Compose/kind)
dockerfile.ingest.lambda # Docker image for ingest Lambda (Lambda base image + handler entry point)
dockerfile.api           # Docker image for API (local/Docker Compose only)
dockerfile.api.lambda    # Docker image for API Lambda (Lambda base image + Mangum handler)
dockerfile.dashboard     # Docker image for dashboard (local/Docker Compose/kind + ECS Fargate)
notes/
  README.md             # Index: which notes file for which run target
  local.md              # Commands: run directly (uv + local Postgres)
  docker.md             # Commands: Docker Compose
  kubernetes.md         # Commands: kind cluster
  aws-deploy.md         # Commands: deploy.sh, Pulumi, ECR builds, teardown
  aws-operations.md     # Commands: ingest trigger, logs, dashboard IP, pause/resume
docker-compose.yml      # Local orchestration
deploy.sh               # Full AWS deploy script (infra → images → services)
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
- [x] AWS SSO configured (profile/region set via `AWS_PROFILE`/`AWS_REGION` in `.env`)
- [x] Pulumi local mode (`pulumi login --local`), stack `dev`
- [x] RDS Postgres 18.4 (`db.t4g.micro`) in default VPC (publicly accessible)
- [x] ECR repos created for ingest, api and dashboard images
- [x] Docker images built and pushed to ECR (via deploy.sh)
- [x] IAM Role + policy attachments for Lambda
- [x] ingest Lambda + api Lambda created (container image from ECR)
- [x] `mangum` added as dependency for FastAPI Lambda adapter
- [x] `handler(event, context)` + `run_ingest()` in fetch_and_ingest.py — dual entry points (local `__main__` + Lambda)
- [x] API Gateway (HTTP API) connected to api Lambda
- [x] EventBridge daily cron schedule connected to ingest Lambda
- [x] Image-digest detection in Pulumi (`get_image_digest`) — deploys only services whose images exist in ECR, replaced the old `deploy_lambda` flag
- [x] Lambdas reference images by digest (not `:latest` tag) — in-place updates, stable api_url between deploys
- [x] Dashboard on ECS Fargate (cluster, task definition, service, SG, execution role, CloudWatch logs) with public IP on port 8501
- [x] `deploy.sh` script automates full deployment in correct order, prints API URL + dashboard URL
- [x] Ingest Lambda triggered, RDS populated with full history for all 6 symbols
- [x] All three API endpoints tested against API Gateway

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
  - **Database** → AWS RDS Postgres (publicly accessible, in default VPC)
  - **Dashboard** → AWS ECS Fargate (Streamlit is a long-lived server — does not fit Lambda), public IP on port 8501, `API_BASE` env in the task definition overrides the dockerfile ENV and points to API Gateway
- **Pulumi language**: Python, local state mode (`pulumi login --local`)
- **AWS environment**: sandbox account (profile/region configured via `AWS_PROFILE`/`AWS_REGION` in `.env`, never hardcoded in tracked files)
- **Docker builds for Lambda**: must use `--platform linux/amd64 --provenance=false` on Apple Silicon — Lambda only supports the classic Docker manifest format, not OCI format which Docker Desktop on Mac produces by default
- **Separate Lambda Dockerfiles**: `dockerfile.api.lambda` and `dockerfile.ingest.lambda` use the `public.ecr.aws/lambda/python:3.13` base image and a handler CMD (`src.api.handler` / `src.fetch_and_ingest.handler`); plain `dockerfile.api`/`dockerfile.ingest` are for local use
- **Image-digest detection** (replaced the old `deploy_lambda` flag): `get_image_digest()` in `infra/__main__.py` checks ECR for a `:latest` image per repo and only deploys services whose images exist — `pulumi up` → push images → `pulumi up` is self-healing on clean slate, steady state, and when adding a new service. Services reference images by digest, so new pushes give in-place updates and `api_url` stays stable
- **Full deploy**: run `./deploy.sh` from project root — handles everything in correct order, prints API URL + dashboard URL at the end
- **API Gateway URL**: run `pulumi stack output api_url` in `infra/` after deploy
- **Dashboard IP**: changes when the Fargate task restarts — deploy.sh looks it up via task → ENI → public IP
- **Teardown**: `cd infra && pulumi destroy` removes all AWS resources (RDS, Lambdas, ECR repos, API Gateway, EventBridge, IAM roles, ECS cluster/service) — requires `AWS_PROFILE`/`AWS_REGION` env vars set (e.g. `set -a && source ../.env && set +a`) and `PULUMI_CONFIG_PASSPHRASE_FILE` pointing at `infra/.pulumi-passphrase`

## What's Next
- Possible hardening: restrict RDS security group (currently 0.0.0.0/0 on 5432), ALB + HTTPS for stable dashboard URL

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
AWS_ACCOUNT_ID=<your_aws_account_id>
AWS_REGION=<your_aws_region>
AWS_PROFILE=<your_aws_profile>
```
