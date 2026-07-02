# Running with Kubernetes (kind)

Runs the full stack on a local kind cluster (`binance-crypto-cluster`).

## Cluster

```bash
# Create cluster
kind create cluster --name binance-crypto-cluster

# Delete cluster
kind delete cluster --name binance-crypto-cluster

# Resume after restarting Docker Desktop
kubectl config use-context kind-binance-crypto-cluster
```

## Images

Build the images with Docker Compose first, then load them into the cluster
(deployments use `imagePullPolicy: Never`, so the images must exist locally):

```bash
kind load docker-image binance_crypto_data_platform-api:latest --name binance-crypto-cluster
kind load docker-image binance_crypto_data_platform-ingest:latest --name binance-crypto-cluster
kind load docker-image binance_crypto_data_platform-dashboard:latest --name binance-crypto-cluster
```

## Deploy

```bash
# Apply all manifests
kubectl apply -f k8s/

# Check pod status
kubectl get pods

# View logs
kubectl logs deployment/api
kubectl logs deployment/dashboard

# Restart a deployment
kubectl rollout restart deployment/api
```

## Ingest

The CronJob runs daily at midnight. Trigger it manually with:

```bash
kubectl create job ingest-manual --from=cronjob/ingest
```

## Access

```bash
# Port-forward dashboard -> http://localhost:8501
kubectl port-forward service/dashboard 8501:8501

# Port-forward API -> http://localhost:8000
kubectl port-forward service/api 8000:8000
```

## Postgres

```bash
# Connect to Postgres inside the cluster
kubectl exec -it deployment/postgres -- psql -U <your_postgres_user> -d binance_crypto_data
```
