#!/bin/bash
set -e

set -a
source .env
set +a

ACCOUNT_ID="$AWS_ACCOUNT_ID"
REGION="$AWS_REGION"
PROFILE="$AWS_PROFILE"
ECR_REGISTRY="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com"

if [ -z "$PULUMI_CONFIG_PASSPHRASE" ]; then
    export PULUMI_CONFIG_PASSPHRASE_FILE="$(pwd)/infra/.pulumi-passphrase"
fi

echo "=== [1/5] Pulumi up (infrastructure) ==="
cd infra
pulumi config set deploy_lambda false
pulumi up --yes --non-interactive
cd ..

echo "=== [2/5] ECR login ==="
aws ecr get-login-password --region $REGION --profile $PROFILE | \
    docker login --username AWS --password-stdin $ECR_REGISTRY

echo "=== [3/5] Build & push ingest image ==="
docker build --platform linux/amd64 --provenance=false -f dockerfile.ingest -t crypto-ingest .
docker tag crypto-ingest $ECR_REGISTRY/crypto-data-platform-ingest-repo:latest
docker push $ECR_REGISTRY/crypto-data-platform-ingest-repo:latest

echo "=== [4/5] Build & push api image ==="
docker build --platform linux/amd64 --provenance=false -f dockerfile.api.lambda -t crypto-api .
docker tag crypto-api $ECR_REGISTRY/crypto-data-platform-api-repo:latest
docker push $ECR_REGISTRY/crypto-data-platform-api-repo:latest

echo "=== [5/5] Pulumi up (Lambda + API Gateway) ==="
cd infra
pulumi config set deploy_lambda true
pulumi up --yes --non-interactive
echo ""
echo "API URL: $(pulumi stack output api_url)"
cd ..

echo "=== Deploy complete! ==="
