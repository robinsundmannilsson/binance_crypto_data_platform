# Deploying to AWS (Pulumi + deploy.sh)

How to create, update and tear down the AWS infrastructure.
For day-to-day usage of the deployed stack, see [aws-operations.md](aws-operations.md).

## Full deploy (the normal way)

`deploy.sh` is self-contained — it sources `.env` and sets `PULUMI_CONFIG_PASSPHRASE_FILE`
itself, so no manual exports are needed. Run it from the project root:

```bash
bash deploy.sh
# (or `chmod +x deploy.sh` once, then `./deploy.sh`)
```

It runs everything in the correct order and prints the API URL + dashboard URL at the end:

1. `pulumi up` — base infra + ECR repos
2. ECR login
3. Build & push all three images
4. `pulumi up` — Lambdas, API Gateway, Fargate dashboard

## Setup for manual commands

Only needed when running `pulumi`/`aws` commands directly (not through `deploy.sh`).
Run once per terminal session:

```bash
set -a && source .env && set +a
export PULUMI_CONFIG_PASSPHRASE_FILE="$(pwd)/infra/.pulumi-passphrase"
```

## Pulumi

> **How deploys are gated:** the program detects per ECR repo whether a `:latest`
> image exists (`get_image_digest()` in `infra/__main__.py`) and only deploys services
> whose images are pushed. A plain `pulumi up` therefore always does the right thing:
> repos missing/empty → base infra only; images pushed → Lambdas, API Gateway and
> Fargate dashboard too. No deploy flags needed.

Run these in `infra/`:

```bash
# Login local mode (state on disk instead of Pulumi Cloud)
pulumi login --local

# Preview changes without applying
pulumi preview

# Apply changes
pulumi up

# Clear pending operations after an interrupted deploy
pulumi refresh

# List deployed resources
pulumi stack --show-urns

# Show stack outputs (e.g. API URL)
pulumi stack output api_url

# Set a secret config value
pulumi config set --secret db_password <password>
```

> **Note:** `aws:region` / `aws:profile` are NOT set via Pulumi config — they come from
> the `AWS_REGION` / `AWS_PROFILE` env vars (see Setup above), so nothing
> account-specific ends up committed in `Pulumi.dev.yaml`.

## Manual image builds

`deploy.sh` does all of this — only needed for one-off builds.

> **Apple Silicon:** `--platform linux/amd64 --provenance=false` is required.
> Lambda only supports the classic Docker manifest format — without these flags the
> push succeeds but Lambda rejects the image with "media type not supported".

Login to ECR:

```bash
aws ecr get-login-password --region $AWS_REGION --profile $AWS_PROFILE | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com
```

**Ingest** (`dockerfile.ingest.lambda` — Lambda-specific; plain `dockerfile.ingest` is for local use):

```bash
docker build --platform linux/amd64 --provenance=false -f dockerfile.ingest.lambda -t crypto-ingest .
docker tag crypto-ingest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/crypto-data-platform-ingest-repo:latest
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/crypto-data-platform-ingest-repo:latest
```

**API** (`dockerfile.api.lambda` — Lambda-specific; plain `dockerfile.api` is for local use):

```bash
docker build --platform linux/amd64 --provenance=false -f dockerfile.api.lambda -t crypto-api .
docker tag crypto-api $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/crypto-data-platform-api-repo:latest
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/crypto-data-platform-api-repo:latest
```

**Dashboard** (same `dockerfile.dashboard` as local — Fargate overrides `API_BASE` via task definition env):

```bash
docker build --platform linux/amd64 --provenance=false -f dockerfile.dashboard -t crypto-dashboard .
docker tag crypto-dashboard $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/crypto-data-platform-dashboard-repo:latest
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/crypto-data-platform-dashboard-repo:latest
```

## Teardown

Deletes **everything**, including all data in RDS. Requires the Setup exports above.
Shows a preview and asks for confirmation first:

```bash
cd infra
pulumi destroy
cd ..
```

To redeploy from scratch afterwards, just run `./deploy.sh` again, then trigger the
ingest Lambda once to repopulate the database (see [aws-operations.md](aws-operations.md)).

> **Tip:** for a temporary overnight shutdown that keeps the data, use
> "Pause / resume" in [aws-operations.md](aws-operations.md) instead.
