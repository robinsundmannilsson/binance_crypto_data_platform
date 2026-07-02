# Running with Kubernetes (kind)

## Cluster
# Create cluster
kind create cluster --name binance-crypto-cluster

# Delete cluster
kind delete cluster --name binance-crypto-cluster

# Resume after restarting Docker Desktop
kubectl config use-context kind-binance-crypto-cluster

## Images
# Load images into cluster (build them with docker compose first)
kind load docker-image binance_crypto_data_platform-api:latest --name binance-crypto-cluster
kind load docker-image binance_crypto_data_platform-ingest:latest --name binance-crypto-cluster
kind load docker-image binance_crypto_data_platform-dashboard:latest --name binance-crypto-cluster

## Deploy
# Apply all manifests
kubectl apply -f k8s/

# Check pod status
kubectl get pods

# View logs
kubectl logs deployment/api
kubectl logs deployment/dashboard

# Restart deployment
kubectl rollout restart deployment/api

## Ingest
# Trigger ingest manually
kubectl create job ingest-manual --from=cronjob/ingest

## Access
# Port-forward dashboard
kubectl port-forward service/dashboard 8501:8501

# Port-forward API
kubectl port-forward service/api 8000:8000

## Postgres
# Connect to Postgres inside Kubernetes
kubectl exec -it deployment/postgres -- psql -U <your_postgres_user> -d binance_crypto_data
