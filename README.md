# ETAguard

ETAguard monitors BLDR deliveries, tracks promised versus actual ETAs, and surfaces SLA breaches using n8n automations, PostgreSQL, and an optional FastAPI proxy.

## Repository layout

```
etaguard/
  infra/
    docker-compose.yaml
  service/
    app.py
    ml_server.py
    client.py
    nlp_text_triage.py
    schemas.py
    schemas_text.py
    requirements.txt
    Dockerfile
    model_store/
      text_triage.pkl
    tests/
      test_explain_delay.py
  ml/
    text/
      labels.py
      train_text_triage.py
      data/
        delivery_notes.sample.csv
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
      004_delay_cause.sql
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
   * When the delivery note is present, a Slack alert line with the ML-predicted cause and a `delay_causes` entry.
   * A daily summary posted at 07:30 America/Los_Angeles.

## Delay note triage (TF-IDF + Logistic Regression)

* The FastAPI service now exposes `POST /explain_delay` which returns a predicted delay label, confidence, model version, and top-3 probabilities for any delivery note.
* Train or update the lightweight scikit-learn model with:

  ```bash
  python -m ml.text.train_text_triage --csv ml/text/data/delivery_notes.sample.csv
  ```

  The script will emit a `service/model_store/text_triage.pkl` artifact used by the API.
* n8n workflow “ETAguard — Poll & Alert” calls the endpoint for deliveries that include a note, stores the result in the `delay_causes` table, and enriches Slack alerts with `Cause (ML): <label> (<confidence>%)`.

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
