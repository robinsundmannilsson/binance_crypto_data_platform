# Running with Docker Compose

# Run full stack (dashboard: http://localhost:8501, API: http://localhost:8000)
docker compose up --build

# Run in background
docker compose up --build -d

# Stop all services
docker compose down

# Stop and remove volumes (deletes all data)
docker compose down -v

# View logs
docker compose logs api
docker compose logs -f api

# List running containers
docker ps

# List all images
docker images

# Remove unused images
docker image prune

# Open shell in running container
docker exec -it <container-name> bash

# View resource usage (CPU, memory, network)
docker stats
