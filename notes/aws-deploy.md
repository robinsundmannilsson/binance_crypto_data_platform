# Deploying to AWS (Pulumi + deploy.sh)

## Full deploy (the normal way)
# deploy.sh is self-contained — it sources .env and sets PULUMI_CONFIG_PASSPHRASE_FILE
# itself, so no manual exports are needed. Run from the project root.
# Order: pulumi up (base + repos) -> ECR login -> build/push 3 images -> pulumi up (services)
# Prints API URL + dashboard URL at the end.
bash deploy.sh
# (or `chmod +x deploy.sh` once, then `./deploy.sh`)

## Setup (run once per terminal session — only needed for manual pulumi/aws commands)
# Loads AWS_ACCOUNT_ID / AWS_REGION / AWS_PROFILE from .env and points Pulumi at the local passphrase file
set -a && source .env && set +a
export PULUMI_CONFIG_PASSPHRASE_FILE="$(pwd)/infra/.pulumi-passphrase"

## Pulumi
# Login local mode
pulumi login --local

# Preview changes (run in infra/)
pulumi preview

# The program detects per ECR repo whether a :latest image exists and only deploys
# services whose images are pushed (get_image_digest in infra/__main__.py) — so a
# plain `pulumi up` always does the right thing, no deploy flags needed:
#   - repos missing/empty -> base infra + ECR repos only
#   - images pushed -> Lambdas, API Gateway, Fargate dashboard too
pulumi up

# Clear pending operations after interrupted deploy
pulumi refresh

# List deployed resources
pulumi stack --show-urns

# Show stack outputs (e.g. API URL)
pulumi stack output api_url

# Set a secret config value
pulumi config set --secret db_password <password>

# aws:region / aws:profile are NOT set via pulumi config — they come from
# AWS_REGION / AWS_PROFILE env vars (see "Setup" above) so nothing account-specific
# ends up committed in Pulumi.dev.yaml

## ECR (manual image builds — deploy.sh does all of this)
# Login Docker to ECR
aws ecr get-login-password --region $AWS_REGION --profile $AWS_PROFILE | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# Build and push ingest image (dockerfile.ingest.lambda — Lambda-specific, not dockerfile.ingest which is for local use)
# NOTE: --platform linux/amd64 and --provenance=false are required on Apple Silicon Macs.
# Lambda only supports the classic Docker manifest format — without these flags the push
# succeeds but Lambda rejects the image with "media type not supported".
docker build --platform linux/amd64 --provenance=false -f dockerfile.ingest.lambda -t crypto-ingest .
docker tag crypto-ingest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/crypto-data-platform-ingest-repo:latest
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/crypto-data-platform-ingest-repo:latest

# Build and push api image (dockerfile.api.lambda — Lambda-specific, not dockerfile.api which is for local use)
docker build --platform linux/amd64 --provenance=false -f dockerfile.api.lambda -t crypto-api . && \
docker tag crypto-api $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/crypto-data-platform-api-repo:latest && \
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/crypto-data-platform-api-repo:latest

# Build and push dashboard image (same dockerfile.dashboard as local — Fargate overrides API_BASE via task definition env)
docker build --platform linux/amd64 --provenance=false -f dockerfile.dashboard -t crypto-dashboard . && \
docker tag crypto-dashboard $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/crypto-data-platform-dashboard-repo:latest && \
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/crypto-data-platform-dashboard-repo:latest

## Teardown (full AWS cost cleanup — deletes everything, including all data in RDS)
# Requires the "Setup" exports above. Shows a preview and asks for confirmation first.
cd infra
pulumi destroy
cd ..
# To redeploy from scratch afterwards, just run ./deploy.sh again,
# then trigger the ingest Lambda once to repopulate the database (see aws-operations.md).
# For a temporary overnight shutdown, see "Pause / resume" in aws-operations.md instead.
