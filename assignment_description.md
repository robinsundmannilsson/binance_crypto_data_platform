# Goal: Get hands-on with the full lifecycle of a data service: ingesting from a live external source, persisting it, serving it over an API, visualizing it, and running the whole thing on Kubernetes locally. We care far more about how the pieces fit together and the decisions you make than about polish.

## Ground rules

### Try to write the code yourself. Reach for the docs first, then Stack Overflow and official examples, and keep AI assistants as a last resort. We use AI a lot day-to-day here, and you will too, but right now is your chance to actually learn the fundamentals: build the muscle memory and understand why things work. That foundation is what makes you good at directing AI later, instead of just pasting what it gives you.

### Pick a data source you find genuinely interesting, you'll be staring at it for a week. Weather, financial/crypto, transit, RSS/news, earthquakes, air quality, public APIs of any kind. Prefer one that changes over time so re-running the ingester actually does something.

1. Ingest (a Python service)
Write a service that pulls data from a public, open data source, parses it, and stores it (Postgres comes in step 2).
 • Make it runnable repeatedly; fetch on a schedule or in a loop, not just once. Think about the second run.
 • Handle the boring-but-real stuff: network errors, rate limits, the source being down, malformed responses.
 • Config (URLs, intervals, credentials) via environment variables, not hardcoded.
 • Add structured logging.
 • Write a few tests with pytest (e.g. a unit test on your parsing logic).
 • Have answers for: How often does the source update? What's your unique key per record? What happens on a record you've seen before?

2.  Store (Postgres)
 • Design a schema deliberately: types, indexes, what you'll actually query.
 • Make ingestion idempotent (look into INSERT ... ON CONFLICT).
 • Think about how the schema gets created/changed (a simple migration beats hand-run SQL).
 • Use a well-known library (psycopg, SQLAlchemy) and learn why.

3. Serve (an API)
Put an HTTP API in front of the data (FastAPI is a great choice).
 • Expose a few meaningful endpoints, not just "dump the table": filtering, time ranges, aggregations.
 • Add a health/readiness endpoint (you'll thank yourself in step 5).
 • Use request/response models (FastAPI gives you OpenAPI docs for free).

4. Consume (a dashboard)
Build something that reads from your API (not the DB directly), e.g. Streamlit, a Jupyter notebook, or a custom frontend.
 • Show something only interesting because you've been collecting over time (a trend, comparison, map, leaderboard).
 • This is where you find out if your API was well-designed. Expect to revisit step 3.

5. Ship it (Kubernetes via kind)
 • A Dockerfile per service.
 • Run Postgres in the cluster.
 • Services talk via Kubernetes Services (DNS), not hardcoded IPs.
 • Wire health endpoints to liveness/readiness probes.
 • Config via ConfigMap/Secret. Plain manifests first; if you have time, see why people reach for Helm.
 • Document the exact commands (clean machine to running stack) in a README.

Stretch goals (only if time allows)
 • Deploy it on AWS (perhaps ECS + ECR).
 • Backfill historical data vs. only live data.
 • A CI workflow that lints and runs tests on push.