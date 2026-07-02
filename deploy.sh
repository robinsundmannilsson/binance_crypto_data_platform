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

# The Pulumi program only deploys services whose images exist in ECR,
# so this first up ensures base infra + ECR repos exist before we push.
echo "=== [1/6] Pulumi up (base infrastructure + ECR repos) ==="
cd infra
pulumi up --yes --non-interactive
cd ..

echo "=== [2/6] ECR login ==="
aws ecr get-login-password --region $REGION --profile $PROFILE | \
    docker login --username AWS --password-stdin $ECR_REGISTRY

echo "=== [3/6] Build & push ingest image ==="
docker build --platform linux/amd64 --provenance=false -f dockerfile.ingest.lambda -t crypto-ingest .
docker tag crypto-ingest $ECR_REGISTRY/crypto-data-platform-ingest-repo:latest
docker push $ECR_REGISTRY/crypto-data-platform-ingest-repo:latest

echo "=== [4/6] Build & push api image ==="
docker build --platform linux/amd64 --provenance=false -f dockerfile.api.lambda -t crypto-api .
docker tag crypto-api $ECR_REGISTRY/crypto-data-platform-api-repo:latest
docker push $ECR_REGISTRY/crypto-data-platform-api-repo:latest

echo "=== [5/6] Build & push dashboard image ==="
docker build --platform linux/amd64 --provenance=false -f dockerfile.dashboard -t crypto-dashboard .
docker tag crypto-dashboard $ECR_REGISTRY/crypto-data-platform-dashboard-repo:latest
docker push $ECR_REGISTRY/crypto-data-platform-dashboard-repo:latest

echo "=== [6/6] Pulumi up (Lambda + API Gateway + Fargate dashboard) ==="
cd infra
pulumi up --yes --non-interactive
echo ""
echo "API URL: $(pulumi stack output api_url)"

CLUSTER=$(pulumi stack output dashboard_cluster_name)
SERVICE=$(pulumi stack output dashboard_service_name)
cd ..

echo "Waiting for dashboard task to get a public IP..."
DASHBOARD_IP=""
for i in $(seq 1 24); do
    TASK_ARN=$(aws ecs list-tasks --cluster "$CLUSTER" --service-name "$SERVICE" \
        --desired-status RUNNING --query 'taskArns[0]' --output text \
        --region $REGION --profile $PROFILE)
    if [ "$TASK_ARN" != "None" ] && [ -n "$TASK_ARN" ]; then
        ENI_ID=$(aws ecs describe-tasks --cluster "$CLUSTER" --tasks "$TASK_ARN" \
            --query "tasks[0].attachments[0].details[?name=='networkInterfaceId'].value" --output text \
            --region $REGION --profile $PROFILE)
        DASHBOARD_IP=$(aws ec2 describe-network-interfaces --network-interface-ids "$ENI_ID" \
            --query 'NetworkInterfaces[0].Association.PublicIp' --output text \
            --region $REGION --profile $PROFILE)
        if [ -n "$DASHBOARD_IP" ] && [ "$DASHBOARD_IP" != "None" ]; then
            break
        fi
    fi
    sleep 5
done

if [ -n "$DASHBOARD_IP" ] && [ "$DASHBOARD_IP" != "None" ]; then
    echo "Dashboard URL: http://$DASHBOARD_IP:8501"
else
    echo "Dashboard task not running yet — find the IP later with:"
    echo "  aws ecs list-tasks --cluster $CLUSTER --service-name $SERVICE --region $REGION --profile $PROFILE"
fi

echo "=== Deploy complete! ==="
