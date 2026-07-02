# AWS Day-to-Day Operations

Using the deployed stack: trigger ingest, read logs, find the dashboard IP, pause overnight.
For creating/updating/tearing down the infrastructure, see [aws-deploy.md](aws-deploy.md).

## Setup (run once per terminal session)

```bash
set -a && source .env && set +a
export PULUMI_CONFIG_PASSPHRASE_FILE="$(pwd)/infra/.pulumi-passphrase"
```

## AWS SSO

```bash
# Login / renew session
aws sso login --profile $AWS_PROFILE

# Verify identity
aws sts get-caller-identity --profile $AWS_PROFILE
```

## API

The API URL is stable across deploys:

```bash
cd infra && pulumi stack output api_url && cd ..
```

Open `<api_url>/docs` in a browser for the interactive Swagger UI (`/redoc` for the
ReDoc view). Endpoints: `/health`, `/candles/{symbol}`, `/candles/{symbol}/latest`.

## Lambda (ingest)

Pulumi adds a random suffix to function names (e.g. `ingest-lambda-ea280a2`) — list them with:

```bash
aws lambda list-functions --query 'Functions[].FunctionName' --profile $AWS_PROFILE
```

Trigger the ingest Lambda manually (full run takes ~1 min, returns `{"status": "ok"}`):

```bash
aws lambda invoke --function-name <ingest-function-name> --cli-read-timeout 320 --profile $AWS_PROFILE output.json && cat output.json
```

Tail Lambda logs live:

```bash
aws logs tail /aws/lambda/<function-name> --follow --profile $AWS_PROFILE
```

> **Note:** new images are picked up by `deploy.sh` / `pulumi up` — services reference
> the image digest, so a new push shows up as an in-place `imageUri` update in Pulumi.

## Dashboard (ECS Fargate)

Cluster/service names come from Pulumi outputs:

```bash
CLUSTER=$(cd infra && pulumi stack output dashboard_cluster_name)
SERVICE=$(cd infra && pulumi stack output dashboard_service_name)
```

**Find the public IP** (task → ENI → public IP; `deploy.sh` does this automatically).
The dashboard runs on `http://<public-ip>:8501` — the IP changes when the task restarts:

```bash
TASK_ARN=$(aws ecs list-tasks --cluster $CLUSTER --service-name $SERVICE --desired-status RUNNING --query 'taskArns[0]' --output text --profile $AWS_PROFILE)
ENI_ID=$(aws ecs describe-tasks --cluster $CLUSTER --tasks $TASK_ARN --query "tasks[0].attachments[0].details[?name=='networkInterfaceId'].value" --output text --profile $AWS_PROFILE)
aws ec2 describe-network-interfaces --network-interface-ids $ENI_ID --query 'NetworkInterfaces[0].Association.PublicIp' --output text --profile $AWS_PROFILE
```

**Dashboard logs** (log group name has a Pulumi suffix, list first):

```bash
aws logs describe-log-groups --log-group-name-prefix dashboard --query 'logGroups[].logGroupName' --profile $AWS_PROFILE
aws logs tail <log-group-name> --follow --profile $AWS_PROFILE
```

**Force a fresh task** (e.g. to pick up config changes):

```bash
aws ecs update-service --cluster $CLUSTER --service $SERVICE --force-new-deployment --profile $AWS_PROFILE
```

## RDS

```bash
# Check instance status
aws rds describe-db-instances --query 'DBInstances[].{id:DBInstanceIdentifier,status:DBInstanceStatus}' --profile $AWS_PROFILE
```

## Pause / resume

Temporary shutdown to save cost — **data survives**. Only RDS and the Fargate task cost
money per hour when idle. Lambdas, API Gateway and EventBridge are pay-per-use,
ECR/IAM/security groups are effectively free — leave them.

### Pause (e.g. overnight)

```bash
# Scale the dashboard down to 0 tasks
CLUSTER=$(cd infra && pulumi stack output dashboard_cluster_name)
SERVICE=$(cd infra && pulumi stack output dashboard_service_name)
aws ecs update-service --cluster $CLUSTER --service $SERVICE --desired-count 0 --profile $AWS_PROFILE

# Stop the database (compute off, storage + data stay — find the id under "RDS" above)
aws rds stop-db-instance --db-instance-identifier <db-instance-id> --profile $AWS_PROFILE
```

> **Note:** the midnight EventBridge cron will fail against a stopped RDS — harmless,
> the next successful ingest refetches the full history (upsert), no data is lost.

### Resume (takes ~5 min total)

```bash
# Database first — `wait` blocks until it is available
aws rds start-db-instance --db-instance-identifier <db-instance-id> --profile $AWS_PROFILE
aws rds wait db-instance-available --db-instance-identifier <db-instance-id> --profile $AWS_PROFILE

# Scale the dashboard back up
CLUSTER=$(cd infra && pulumi stack output dashboard_cluster_name)
SERVICE=$(cd infra && pulumi stack output dashboard_service_name)
aws ecs update-service --cluster $CLUSTER --service $SERVICE --desired-count 1 --profile $AWS_PROFILE
```

The new task gets a **new public IP** — look it up with the commands under "Dashboard" above.

> **Warning:** do NOT use `deploy.sh` to resume — Pulumi compares against its saved
> state (where `desired_count` is already 1) and will not notice the manual scale-down.
