# Runbooks

Step-by-step commands for running and operating the project, organized by run target:

| File | When to use |
|------|-------------|
| [local.md](local.md) | Running services directly on your machine (uv + local Postgres) |
| [docker.md](docker.md) | Running the full stack with Docker Compose |
| [kubernetes.md](kubernetes.md) | Running on the local kind cluster |
| [aws-deploy.md](aws-deploy.md) | Deploying to AWS: deploy.sh, Pulumi, ECR builds, teardown |
| [aws-operations.md](aws-operations.md) | Day-to-day AWS ops: trigger ingest, logs, dashboard IP, pause/resume |
