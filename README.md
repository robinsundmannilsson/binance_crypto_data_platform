# Binance Crypto Data Platform

![Python](https://img.shields.io/badge/Python-3.13-blue?logo=python)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-18-blue?logo=postgresql)
![FastAPI](https://img.shields.io/badge/FastAPI-latest-green?logo=fastapi)
![Streamlit](https://img.shields.io/badge/Streamlit-latest-red?logo=streamlit)
![Docker](https://img.shields.io/badge/Docker-Compose-blue?logo=docker)
![Kubernetes](https://img.shields.io/badge/Kubernetes-kind-blue?logo=kubernetes)

A full data service lifecycle pipeline that ingests historical cryptocurrency data from the Binance public API, stores it in PostgreSQL, serves it via FastAPI, and visualises it in a Streamlit dashboard — deployable with Docker Compose or Kubernetes.

---

## Features

- Ingests historical daily OHLCV candle data for 6 cryptocurrencies from the Binance public API
- Stores data in PostgreSQL using `NUMERIC(20,8)` precision (no floats for financial data)
- Upsert logic — safe to re-run without duplicates
- FastAPI with Pydantic response models and optional date filtering
- Streamlit dashboard with live currency conversion (USD/EUR/SEK/NOK/DKK) and Plotly candlestick charts
- Deployable locally with Docker Compose or on a Kubernetes cluster with kind

---

## Cryptocurrencies

| Symbol | Name |
|--------|------|
| BTCUSDT | Bitcoin |
| ETHUSDT | Ethereum |
| XRPUSDT | Ripple |
| SOLUSDT | Solana |
| LINKUSDT | Chainlink |
| ADAUSDT | Cardano |

---

## Project Structure

```
src/
  fetch_and_ingest.py   # Binance API ingestion script
  api.py                # FastAPI app
  models.py             # Pydantic response models
  dashboard.py          # Streamlit dashboard
k8s/
  postgres-pvc.yaml         # PersistentVolumeClaim
  postgres-deployment.yaml  # Postgres Deployment
  postgres-service.yaml     # Postgres Service
  api-deployment.yaml       # API Deployment
  api-service.yaml          # API Service
  dashboard-deployment.yaml # Dashboard Deployment
  dashboard-service.yaml    # Dashboard Service
  ingest-job.yaml           # CronJob for daily ingest
dockerfile.ingest       # Docker image for ingest
dockerfile.api          # Docker image for API
dockerfile.dashboard    # Docker image for dashboard
docker-compose.yml      # Local orchestration
```

---

## Prerequisites

- [Docker](https://www.docker.com/)
- [kind](https://kind.sigs.k8s.io/) (for Kubernetes)
- [kubectl](https://kubernetes.io/docs/tasks/tools/) (for Kubernetes)

---

## Environment Variables

Copy `.env.example` and fill in your values:

```bash
cp .env.example .env
```

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

---

## Running with Docker Compose

```bash
docker compose up --build
```

This starts all four services in the correct order:

| Service | URL |
|---------|-----|
| Dashboard | http://localhost:8501 |
| API | http://localhost:8000 |
| PostgreSQL | localhost:5432 |

---

## Running with Kubernetes (kind)

### 1. Create the cluster

```bash
kind create cluster --name binance-crypto-cluster
```

### 2. Build and load images

```bash
docker build -f dockerfile.api -t binance_crypto_data_platform-api:latest .
docker build -f dockerfile.ingest -t binance_crypto_data_platform-ingest:latest .
docker build -f dockerfile.dashboard -t binance_crypto_data_platform-dashboard:latest .

kind load docker-image binance_crypto_data_platform-api:latest --name binance-crypto-cluster
kind load docker-image binance_crypto_data_platform-ingest:latest --name binance-crypto-cluster
kind load docker-image binance_crypto_data_platform-dashboard:latest --name binance-crypto-cluster
```

### 3. Create the secret

Create `k8s/postgres-secrets.yaml` (this file is gitignored):

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: postgres-secret
type: Opaque
stringData:
  DB_USER: "<your_postgres_user>"
  DB_PASSWORD: "<your_postgres_password>"
  DB_PORT: "5432"
```

### 4. Apply manifests

```bash
kubectl apply -f k8s/postgres-secrets.yaml
kubectl apply -f k8s/postgres-pvc.yaml
kubectl apply -f k8s/postgres-deployment.yaml
kubectl apply -f k8s/postgres-service.yaml
kubectl apply -f k8s/api-deployment.yaml
kubectl apply -f k8s/api-service.yaml
kubectl apply -f k8s/dashboard-deployment.yaml
kubectl apply -f k8s/dashboard-service.yaml
kubectl apply -f k8s/ingest-job.yaml
```

### 5. Run ingest manually

```bash
kubectl create job ingest-manual --from=cronjob/ingest
```

### 6. Access the dashboard

```bash
kubectl port-forward service/dashboard 8501:8501
```

Open http://localhost:8501 in your browser.

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/candles/{symbol}` | Full price history (optional `from_date` / `to_date`) |
| GET | `/candles/{symbol}/latest` | Latest candle for a symbol |

---

## Screenshots

*Coming soon*
