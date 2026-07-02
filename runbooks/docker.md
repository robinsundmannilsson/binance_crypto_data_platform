# Running with Docker Compose

Runs the full stack (Postgres, ingest, API, dashboard) in the correct order.
Dashboard: <http://localhost:8501> · API: <http://localhost:8000>

## Start & stop

```bash
# Run full stack (foreground)
docker compose up --build

# Run in background
docker compose up --build -d

# Stop all services
docker compose down

# Stop and remove volumes (deletes all data!)
docker compose down -v
```

## Logs & debugging

```bash
# View logs for a service
docker compose logs api

# Follow logs live
docker compose logs -f api

# Open a shell inside a running container
docker exec -it <container-name> bash

# Resource usage (CPU, memory, network)
docker stats
```

## Housekeeping

```bash
# List running containers
docker ps

# List all images
docker images

# Remove unused images
docker image prune
```
