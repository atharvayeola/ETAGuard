# ETAguard

ETAguard monitors deliveries, tracks promised versus actual ETAs, and surfaces SLA breaches using n8n automations, PostgreSQL, and an optional FastAPI proxy.

## Repository layout

```
etaguard/
  infra/
    docker-compose.yaml
  service/
    app.py
    client.py
    schemas.py
    requirements.txt
    Dockerfile
  n8n/
    workflows/
      etaguard_poll_and_alert.json
      etaguard_daily_summary.json
      etaguard_errors.json
    env.example
  db/
    migrations/
      001_init.sql
      002_indexes.sql
  README.md
  .env
```

## Getting started

1. **Create environment file**

   ```bash
   cp n8n/env.example .env
   ```

   Update secrets like `SLACK_BOT_TOKEN`, `SLACK_SLA_CHANNEL`, and `MYBLDR_AUTH_COOKIE`.

2. **Launch the stack**

   ```bash
   cd infra
   docker compose up --build -d
   ```

   Services:

   * n8n UI: [http://localhost:5678](http://localhost:5678) (basic auth from `.env`)
   * FastAPI proxy: [http://localhost:8000/health](http://localhost:8000/health)
   * PostgreSQL: `localhost:5432`

3. **Import n8n workflows**

   * In the n8n UI, import the JSON files in `n8n/workflows/`.
   * Update node credentials (Postgres, Slack, HTTP Request) to use your environment secrets.

4. **Smoke test**

   The default proxy stub returns a sample delivery with a 40 minute delay. After the poll workflow runs you should see:

   * A row in `deliveries` for order `B12345`.
   * A Slack alert in `SLACK_SLA_CHANNEL` for the late delivery.
   * A row in `alerts` for the breach.
   * A daily summary posted at 07:30 America/Los_Angeles.

## Development notes

* The proxy service is optional if you have a direct API; point `SERVICE_URL` to the appropriate endpoint returning the same schema.
* `db/migrations` are mounted into PostgreSQL via Docker Compose and run automatically.
* The `sla_history` table is updated by the daily summary workflow using an UPSERT.
* An error workflow posts execution failures into Slack.

## Testing locally without Docker

1. Install dependencies for the proxy service:

   ```bash
   cd service
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   uvicorn app:app --reload
   ```

2. Ensure you have PostgreSQL available and apply the SQL migrations.
3. Run the n8n workflows using the desktop app or a local n8n instance pointed at the same database.

## License

MIT
